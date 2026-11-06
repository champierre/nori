//! Merges PDF files into one.
//!
//! Inputs are read one at a time. The objects each page needs are written to
//! the output as soon as they are found, under new object numbers, and the
//! input is dropped before the next one is opened. Memory therefore stays
//! around the size of the largest input plus one offset per output object,
//! however many files are merged.

#![forbid(unsafe_code)]

use lopdf::{Dictionary, Document, Object, ObjectId, StringFormat};
use std::collections::{BTreeMap, HashMap, HashSet, VecDeque};
use std::fmt;
use std::fs::File;
use std::io::{self, BufWriter, Write};
use std::path::{Path, PathBuf};
use std::sync::{Mutex, mpsc};
use std::thread;

const CATALOG_ID: u32 = 1;
const ROOT_PAGES_ID: u32 = 2;

/// Pages under one intermediate node of the output page tree. Viewers walk
/// the tree to find a page, so a flat tree with tens of thousands of kids is
/// slow to open at an arbitrary page.
const PAGES_PER_NODE: usize = 256;

/// Attributes a page may inherit from its ancestors in the page tree.
const INHERITED: [&[u8]; 4] = [b"Resources", b"MediaBox", b"CropBox", b"Rotate"];

#[derive(Debug)]
pub enum Error {
    Io(io::Error),
    /// An input could not be parsed as a PDF.
    Read {
        path: PathBuf,
        source: lopdf::Error,
    },
    /// An input has no page tree or an empty one.
    NoPages(PathBuf),
    NoInputs,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Io(e) => write!(f, "{e}"),
            Error::Read { path, source } => write!(f, "{}: {source}", path.display()),
            Error::NoPages(path) => write!(f, "{}: no pages", path.display()),
            Error::NoInputs => write!(f, "no input files"),
        }
    }
}

impl std::error::Error for Error {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Error::Io(e) => Some(e),
            Error::Read { source, .. } => Some(source),
            _ => None,
        }
    }
}

impl From<io::Error> for Error {
    fn from(e: io::Error) -> Self {
        Error::Io(e)
    }
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct Summary {
    pub inputs: usize,
    pub pages: usize,
    /// Objects in the output, including the page tree and the info dictionary.
    pub objects: usize,
}

/// Merges `inputs`, in order, into the file at `output`. An existing file is
/// overwritten; on failure nothing is left behind.
///
/// `jobs` inputs are parsed at once on separate threads. Parsing dominates
/// for inputs with many objects, so this scales nearly linearly with cores,
/// at the cost of holding up to about twice that many inputs in memory.
pub fn merge<P: AsRef<Path> + Sync>(
    inputs: &[P],
    output: &Path,
    jobs: usize,
) -> Result<Summary, Error> {
    let file = File::create(output)?;
    let result = merge_into(inputs, BufWriter::with_capacity(1 << 20, file), jobs);
    if result.is_err() {
        let _ = std::fs::remove_file(output);
    }
    result
}

/// Merges `inputs`, in order, writing the PDF to `out`.
pub fn merge_into<P: AsRef<Path> + Sync, W: Write>(
    inputs: &[P],
    out: W,
    jobs: usize,
) -> Result<Summary, Error> {
    if inputs.is_empty() {
        return Err(Error::NoInputs);
    }
    let mut writer = Writer::new(out);
    let jobs = jobs.clamp(1, inputs.len());
    if jobs == 1 {
        for input in inputs {
            let path = input.as_ref();
            writer.append(path, &load(path)?)?;
        }
    } else {
        parse_ahead(inputs, jobs, |path, doc| writer.append(path, doc))?;
    }
    writer.finish()
}

fn load(path: &Path) -> Result<Document, Error> {
    Document::load(path).map_err(|source| Error::Read {
        path: path.to_path_buf(),
        source,
    })
}

/// Parses inputs on `jobs` worker threads and hands each document to
/// `consume` in input order.
///
/// Workers take input indexes from a queue that this thread feeds; it issues
/// a new index only while fewer than `jobs` are being parsed and fewer than
/// `jobs` parsed documents wait for their turn. One slow input therefore
/// cannot make the others pile up: at most about `2 * jobs` documents are in
/// memory at any time.
fn parse_ahead<P: AsRef<Path> + Sync>(
    inputs: &[P],
    jobs: usize,
    mut consume: impl FnMut(&Path, &Document) -> Result<usize, Error>,
) -> Result<(), Error> {
    let (job_tx, job_rx) = mpsc::sync_channel::<usize>(jobs);
    let (result_tx, result_rx) = mpsc::sync_channel::<(usize, Result<Document, Error>)>(jobs);
    let job_rx = Mutex::new(job_rx);

    thread::scope(|scope| {
        // Both ends this thread holds must die when the closure returns, before
        // the scope joins the workers: a worker waits on them otherwise.
        let job_tx = job_tx;
        let result_rx = result_rx;
        for _ in 0..jobs {
            let job_rx = &job_rx;
            let result_tx = result_tx.clone();
            scope.spawn(move || {
                loop {
                    let next = job_rx.lock().unwrap().recv();
                    let Ok(index) = next else { break };
                    let document = load(inputs[index].as_ref());
                    if result_tx.send((index, document)).is_err() {
                        break;
                    }
                }
            });
        }
        drop(result_tx);

        let mut pending: BTreeMap<usize, Result<Document, Error>> = BTreeMap::new();
        let mut issued = 0;
        let mut expected = 0;
        while expected < inputs.len() {
            if let Some(document) = pending.remove(&expected) {
                consume(inputs[expected].as_ref(), &document?)?;
                expected += 1;
                continue;
            }
            let parsing = issued - expected - pending.len();
            if issued < inputs.len() && parsing < jobs && pending.len() < jobs {
                job_tx.send(issued).expect("workers outlive the queue");
                issued += 1;
                continue;
            }
            let (index, document) = result_rx
                .recv()
                .map_err(|_| Error::Io(io::Error::other("a worker thread stopped unexpectedly")))?;
            pending.insert(index, document);
        }
        Ok(())
    })
    // A worker still parsing when the queue closes finishes its file first;
    // its send then fails harmlessly because the receiver is gone.
}

struct Node {
    id: u32,
    kids: Vec<u32>,
}

struct Writer<W: Write> {
    out: W,
    position: u64,
    /// Byte offset of each object, indexed by object number. Entry 0 is the
    /// free-list head and never written.
    offsets: Vec<u64>,
    header_version: Option<String>,
    max_version: String,
    nodes: Vec<Node>,
    inputs: usize,
    pages: usize,
    buf: Vec<u8>,
}

impl<W: Write> Writer<W> {
    fn new(out: W) -> Self {
        Writer {
            out,
            position: 0,
            offsets: vec![0; 3],
            header_version: None,
            max_version: String::new(),
            nodes: Vec::new(),
            inputs: 0,
            pages: 0,
            buf: Vec::new(),
        }
    }

    fn alloc(&mut self) -> u32 {
        self.offsets.push(0);
        (self.offsets.len() - 1) as u32
    }

    fn write(&mut self, bytes: &[u8]) -> io::Result<()> {
        self.out.write_all(bytes)?;
        self.position += bytes.len() as u64;
        Ok(())
    }

    fn write_header(&mut self, version: &str) -> io::Result<()> {
        if self.header_version.is_none() {
            self.header_version = Some(version.to_string());
            self.write(format!("%PDF-{version}\n%\u{e2}\u{e3}\u{cf}\u{d3}\n").as_bytes())?;
        }
        if version_key(version) > version_key(&self.max_version) {
            self.max_version = version.to_string();
        }
        Ok(())
    }

    fn write_object(&mut self, id: u32) -> io::Result<()> {
        self.offsets[id as usize] = self.position;
        let body = std::mem::take(&mut self.buf);
        self.write(format!("{id} 0 obj\n").as_bytes())?;
        self.write(&body)?;
        self.write(b"\nendobj\n")?;
        self.buf = body;
        self.buf.clear();
        Ok(())
    }

    /// Node that the next page goes under, opening a new one when the current
    /// node is full.
    fn next_parent(&mut self) -> u32 {
        if self
            .nodes
            .last()
            .is_none_or(|node| node.kids.len() >= PAGES_PER_NODE)
        {
            let id = self.alloc();
            self.nodes.push(Node {
                id,
                kids: Vec::new(),
            });
        }
        self.nodes.last().unwrap().id
    }

    /// Copies the pages of `doc` and everything they reference. Returns the
    /// number of pages copied.
    fn append(&mut self, path: &Path, doc: &Document) -> Result<usize, Error> {
        self.write_header(&doc.version)?;
        self.inputs += 1;

        let page_ids: Vec<ObjectId> = doc.page_iter().collect();
        let mut map: HashMap<ObjectId, u32> = HashMap::with_capacity(doc.objects.len());
        let mut queue: VecDeque<ObjectId> = VecDeque::new();
        let mut refs: Vec<ObjectId> = Vec::new();
        for &id in &page_ids {
            let new_id = self.alloc();
            map.insert(id, new_id);
        }

        for &id in &page_ids {
            let page = materialize(doc, id);
            refs.clear();
            collect_entries(&page, &mut refs);
            for &r in &refs {
                self.assign(doc, r, &mut map, &mut queue);
            }
            let parent = self.next_parent();
            let new_id = map[&id];
            self.nodes.last_mut().unwrap().kids.push(new_id);
            self.pages += 1;

            self.buf.extend_from_slice(b"<<");
            put_entries(&mut self.buf, &page, &map, None);
            write!(self.buf, " /Parent {parent} 0 R >>").unwrap();
            self.write_object(new_id)?;
        }

        while let Some(id) = queue.pop_front() {
            let Some(object) = doc.objects.get(&id) else {
                continue;
            };
            refs.clear();
            collect(object, &mut refs);
            for &r in &refs {
                self.assign(doc, r, &mut map, &mut queue);
            }
            put_object(&mut self.buf, object, &map);
            self.write_object(map[&id])?;
        }
        if page_ids.is_empty() {
            return Err(Error::NoPages(path.to_path_buf()));
        }
        Ok(page_ids.len())
    }

    /// Gives `id` an output number and queues it, unless it already has one or
    /// the input has no such object. A reference to a missing object is
    /// written as `null`, which is how readers treat it anyway.
    fn assign(
        &mut self,
        doc: &Document,
        id: ObjectId,
        map: &mut HashMap<ObjectId, u32>,
        queue: &mut VecDeque<ObjectId>,
    ) {
        if map.contains_key(&id) || !doc.objects.contains_key(&id) {
            return;
        }
        let new_id = self.alloc();
        map.insert(id, new_id);
        queue.push_back(id);
    }

    fn finish(mut self) -> Result<Summary, Error> {
        let nodes = std::mem::take(&mut self.nodes);
        for node in &nodes {
            write!(
                self.buf,
                "<< /Type /Pages /Parent {ROOT_PAGES_ID} 0 R /Count {} /Kids [",
                node.kids.len()
            )
            .unwrap();
            for kid in &node.kids {
                write!(self.buf, " {kid} 0 R").unwrap();
            }
            self.buf.extend_from_slice(b" ] >>");
            self.write_object(node.id)?;
        }

        write!(self.buf, "<< /Type /Pages /Count {} /Kids [", self.pages).unwrap();
        for node in &nodes {
            write!(self.buf, " {} 0 R", node.id).unwrap();
        }
        self.buf.extend_from_slice(b" ] >>");
        self.write_object(ROOT_PAGES_ID)?;

        write!(self.buf, "<< /Type /Catalog /Pages {ROOT_PAGES_ID} 0 R").unwrap();
        // The header carries the first input's version; a later input with a
        // newer one is announced here, which takes precedence over the header.
        if self.header_version.as_deref() != Some(self.max_version.as_str()) {
            write!(self.buf, " /Version /{}", self.max_version).unwrap();
        }
        self.buf.extend_from_slice(b" >>");
        self.write_object(CATALOG_ID)?;

        let info_id = self.alloc();
        write!(
            self.buf,
            "<< /Producer (nori {}) >>",
            env!("CARGO_PKG_VERSION")
        )
        .unwrap();
        self.write_object(info_id)?;

        let startxref = self.position;
        let size = self.offsets.len();
        self.write(format!("xref\n0 {size}\n0000000000 65535 f \n").as_bytes())?;
        let offsets = std::mem::take(&mut self.offsets);
        for chunk in offsets[1..].chunks(4096) {
            let mut entries = String::with_capacity(chunk.len() * 20);
            for offset in chunk {
                entries.push_str(&format!("{offset:010} 00000 n \n"));
            }
            self.write(entries.as_bytes())?;
        }
        self.write(
            format!(
                "trailer\n<< /Size {size} /Root {CATALOG_ID} 0 R /Info {info_id} 0 R >>\nstartxref\n{startxref}\n%%EOF\n"
            )
            .as_bytes(),
        )?;
        self.out.flush()?;

        Ok(Summary {
            inputs: self.inputs,
            pages: self.pages,
            objects: size - 1,
        })
    }
}

fn version_key(version: &str) -> (u32, u32) {
    let mut parts = version.split('.').map(|p| p.parse().unwrap_or(0));
    (parts.next().unwrap_or(0), parts.next().unwrap_or(0))
}

/// The page dictionary with inherited attributes filled in and without its
/// link to the old page tree. A page whose entry is missing from the input
/// is treated as empty rather than failing the merge.
fn materialize(doc: &Document, id: ObjectId) -> Dictionary {
    let mut page = doc.get_dictionary(id).cloned().unwrap_or_default();
    for key in INHERITED {
        if !matches!(page.get(key), Ok(value) if !matches!(value, Object::Null))
            && let Some(value) = inherited(doc, &page, key)
        {
            page.set(key, value);
        }
    }
    page.remove(b"Parent");
    page
}

fn inherited(doc: &Document, page: &Dictionary, key: &[u8]) -> Option<Object> {
    let mut visited = HashSet::new();
    let mut parent = page.get(b"Parent").ok()?.as_reference().ok()?;
    while visited.insert(parent) {
        let node = doc.get_dictionary(parent).ok()?;
        match node.get(key) {
            Ok(Object::Null) | Err(_) => {}
            Ok(value) => return Some(value.clone()),
        }
        parent = node.get(b"Parent").ok()?.as_reference().ok()?;
    }
    None
}

/// Whether `/Parent` in `dict` points into a page tree. Those links are not
/// copied: the output has its own tree.
fn is_page_tree_node(dict: &Dictionary) -> bool {
    matches!(dict.get(b"Type"), Ok(Object::Name(name)) if name == b"Page" || name == b"Pages")
}

fn collect(object: &Object, refs: &mut Vec<ObjectId>) {
    match object {
        Object::Reference(id) => refs.push(*id),
        Object::Array(items) => items.iter().for_each(|item| collect(item, refs)),
        Object::Dictionary(dict) => collect_entries(dict, refs),
        Object::Stream(stream) => collect_entries(&stream.dict, refs),
        _ => {}
    }
}

fn collect_entries(dict: &Dictionary, refs: &mut Vec<ObjectId>) {
    let skip_parent = is_page_tree_node(dict);
    for (key, value) in dict.iter() {
        if skip_parent && key == b"Parent" {
            continue;
        }
        collect(value, refs);
    }
}

fn put_object(buf: &mut Vec<u8>, object: &Object, map: &HashMap<ObjectId, u32>) {
    match object {
        Object::Null => buf.extend_from_slice(b"null"),
        Object::Boolean(value) => buf.extend_from_slice(if *value { b"true" } else { b"false" }),
        Object::Integer(value) => write!(buf, "{value}").unwrap(),
        Object::Real(value) => put_real(buf, *value),
        Object::Name(name) => put_name(buf, name),
        Object::String(bytes, format) => put_string(buf, bytes, *format),
        Object::Array(items) => {
            buf.push(b'[');
            for (i, item) in items.iter().enumerate() {
                if i > 0 {
                    buf.push(b' ');
                }
                put_object(buf, item, map);
            }
            buf.push(b']');
        }
        Object::Dictionary(dict) => {
            buf.extend_from_slice(b"<<");
            put_entries(buf, dict, map, None);
            buf.extend_from_slice(b" >>");
        }
        Object::Stream(stream) => {
            buf.extend_from_slice(b"<<");
            put_entries(buf, &stream.dict, map, Some(stream.content.len()));
            buf.extend_from_slice(b" >>\nstream\n");
            buf.extend_from_slice(&stream.content);
            buf.extend_from_slice(b"\nendstream");
        }
        Object::Reference(id) => match map.get(id) {
            Some(new_id) => write!(buf, "{new_id} 0 R").unwrap(),
            None => buf.extend_from_slice(b"null"),
        },
    }
}

/// Writes the entries of `dict` without the surrounding `<<` `>>`. With
/// `length`, `/Length` is replaced by that value so it always matches the
/// stream data actually written.
fn put_entries(
    buf: &mut Vec<u8>,
    dict: &Dictionary,
    map: &HashMap<ObjectId, u32>,
    length: Option<usize>,
) {
    let skip_parent = is_page_tree_node(dict);
    for (key, value) in dict.iter() {
        if (skip_parent && key == b"Parent") || (length.is_some() && key == b"Length") {
            continue;
        }
        buf.push(b' ');
        put_name(buf, key);
        buf.push(b' ');
        put_object(buf, value, map);
    }
    if let Some(length) = length {
        write!(buf, " /Length {length}").unwrap();
    }
}

fn put_real(buf: &mut Vec<u8>, value: f32) {
    if !value.is_finite() {
        buf.push(b'0');
    } else if value.fract() == 0.0 && value.abs() < 1e9 {
        write!(buf, "{}", value as i64).unwrap();
    } else {
        write!(buf, "{value}").unwrap();
    }
}

fn put_name(buf: &mut Vec<u8>, name: &[u8]) {
    buf.push(b'/');
    for &byte in name {
        let regular = (0x21..=0x7e).contains(&byte) && !b"()<>[]{}/%#".contains(&byte);
        if regular {
            buf.push(byte);
        } else {
            write!(buf, "#{byte:02X}").unwrap();
        }
    }
}

fn put_string(buf: &mut Vec<u8>, bytes: &[u8], format: StringFormat) {
    match format {
        StringFormat::Literal => {
            buf.push(b'(');
            for &byte in bytes {
                match byte {
                    b'(' | b')' | b'\\' => {
                        buf.push(b'\\');
                        buf.push(byte);
                    }
                    b'\r' => buf.extend_from_slice(b"\\r"),
                    b'\n' => buf.extend_from_slice(b"\\n"),
                    _ => buf.push(byte),
                }
            }
            buf.push(b')');
        }
        StringFormat::Hexadecimal => {
            buf.push(b'<');
            for byte in bytes {
                write!(buf, "{byte:02X}").unwrap();
            }
            buf.push(b'>');
        }
    }
}
