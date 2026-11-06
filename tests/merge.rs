use lopdf::{Dictionary, Document, Object, ObjectId, Stream, dictionary};
use std::path::{Path, PathBuf};
use std::process::Command;

struct Dir(PathBuf);

impl Dir {
    fn new(name: &str) -> Dir {
        let path = std::env::temp_dir().join(format!("nori-test-{}-{name}", std::process::id()));
        let _ = std::fs::remove_dir_all(&path);
        std::fs::create_dir_all(&path).unwrap();
        Dir(path)
    }

    fn file(&self, name: &str, bytes: &[u8]) -> PathBuf {
        let path = self.0.join(name);
        std::fs::write(&path, bytes).unwrap();
        path
    }

    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }
}

impl Drop for Dir {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

fn fixture() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("bench/fixtures/statement-libreoffice.pdf")
}

fn save(mut doc: Document) -> Vec<u8> {
    let mut bytes = Vec::new();
    doc.save_to(&mut bytes).unwrap();
    bytes
}

/// A document whose pages inherit MediaBox, Resources and Rotate from the
/// page tree root through an intermediate node.
fn inheriting_document(page_count: usize, label: &str) -> Vec<u8> {
    let mut doc = Document::with_version("1.5");
    let root_id = doc.new_object_id();
    let node_id = doc.new_object_id();
    let font_id = doc.add_object(dictionary! {
        "Type" => "Font", "Subtype" => "Type1", "BaseFont" => "Helvetica",
    });
    let resources_id = doc.add_object(dictionary! { "Font" => dictionary! { "F1" => font_id } });
    let mut kids = Vec::new();
    for i in 0..page_count {
        let content = format!("BT /F1 24 Tf 72 700 Td ({label} {i}) Tj ET");
        let content_id = doc.add_object(Stream::new(dictionary! {}, content.into_bytes()));
        let page_id = doc.add_object(dictionary! {
            "Type" => "Page", "Parent" => node_id, "Contents" => content_id,
        });
        kids.push(Object::Reference(page_id));
    }
    doc.objects.insert(
        node_id,
        Object::Dictionary(dictionary! {
            "Type" => "Pages", "Parent" => root_id, "Kids" => kids, "Count" => page_count as i64,
            "Rotate" => 90,
        }),
    );
    doc.objects.insert(
        root_id,
        Object::Dictionary(dictionary! {
            "Type" => "Pages", "Kids" => vec![Object::Reference(node_id)], "Count" => page_count as i64,
            "MediaBox" => vec![0.into(), 0.into(), 612.into(), 792.into()],
            "Resources" => resources_id,
        }),
    );
    let catalog_id = doc.add_object(dictionary! { "Type" => "Catalog", "Pages" => root_id });
    doc.trailer.set("Root", catalog_id);
    save(doc)
}

/// A one-page document with a link annotation pointing back at its page, a
/// dangling reference and a name that needs escaping.
fn annotated_document() -> Vec<u8> {
    let mut doc = Document::with_version("1.4");
    let pages_id = doc.new_object_id();
    let page_id = doc.new_object_id();
    let annot_id = doc.add_object(dictionary! {
        "Type" => "Annot", "Subtype" => "Link", "P" => page_id,
        "Rect" => vec![0.into(), 0.into(), 10.into(), 10.into()],
    });
    let content_id = doc.add_object(Stream::new(dictionary! {}, b"0 0 m 10 10 l S".to_vec()));
    doc.objects.insert(
        page_id,
        Object::Dictionary(dictionary! {
            "Type" => "Page", "Parent" => pages_id, "Contents" => content_id,
            "MediaBox" => vec![0.into(), 0.into(), 100.into(), 100.into()],
            "Annots" => vec![Object::Reference(annot_id), Object::Reference((9999, 0))],
            "Resources" => dictionary! { "ExtGState" => dictionary! { "a b/c" => dictionary! { "CA" => 0.5f32 } } },
        }),
    );
    doc.objects.insert(
        pages_id,
        Object::Dictionary(dictionary! {
            "Type" => "Pages", "Kids" => vec![Object::Reference(page_id)], "Count" => 1,
        }),
    );
    let catalog_id = doc.add_object(dictionary! { "Type" => "Catalog", "Pages" => pages_id });
    doc.trailer.set("Root", catalog_id);
    save(doc)
}

fn pages(doc: &Document) -> Vec<ObjectId> {
    doc.page_iter().collect()
}

fn page_dict(doc: &Document, index: usize) -> &Dictionary {
    doc.get_dictionary(pages(doc)[index]).unwrap()
}

fn qpdf_check(path: &Path) {
    let Ok(output) = Command::new("qpdf").arg("--check").arg(path).output() else {
        eprintln!("qpdf not installed; skipping --check");
        return;
    };
    assert!(
        output.status.success(),
        "qpdf --check failed:\n{}{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn merges_pages_in_order_with_inherited_attributes() {
    let dir = Dir::new("inherit");
    let a = dir.file("a.pdf", &inheriting_document(2, "A"));
    let b = dir.file("b.pdf", &annotated_document());
    let c = dir.file("c.pdf", &inheriting_document(1, "C"));
    let out = dir.path("out.pdf");

    let summary = nori::merge(&[&a, &b, &c], &out, 1).unwrap();
    assert_eq!((summary.inputs, summary.pages), (3, 4));

    let doc = Document::load(&out).unwrap();
    assert_eq!(pages(&doc).len(), 4);
    for (index, expected) in [(0, "A 0"), (1, "A 1"), (3, "C 0")] {
        let page = page_dict(&doc, index);
        assert_eq!(page.get(b"Rotate").unwrap().as_i64().unwrap(), 90);
        assert_eq!(page.get(b"MediaBox").unwrap().as_array().unwrap().len(), 4);
        let resources = doc
            .get_dictionary(page.get(b"Resources").unwrap().as_reference().unwrap())
            .unwrap();
        assert!(resources.get(b"Font").is_ok());
        let content = doc.get_page_content(pages(&doc)[index]);
        assert!(String::from_utf8_lossy(&content).contains(&format!("({expected})")));
    }
    assert!(
        page_dict(&doc, 2).get(b"Rotate").is_err(),
        "the annotated page inherits nothing"
    );

    // Every page hangs off the new tree: page -> node -> root, root has no parent.
    let catalog = doc.catalog().unwrap();
    let root_id = catalog.get(b"Pages").unwrap().as_reference().unwrap();
    let root = doc.get_dictionary(root_id).unwrap();
    assert_eq!(root.get(b"Count").unwrap().as_i64().unwrap(), 4);
    assert!(root.get(b"Parent").is_err());
    for page_id in pages(&doc) {
        let node_id = doc
            .get_dictionary(page_id)
            .unwrap()
            .get(b"Parent")
            .unwrap()
            .as_reference()
            .unwrap();
        let node = doc.get_dictionary(node_id).unwrap();
        assert_eq!(
            node.get(b"Parent").unwrap().as_reference().unwrap(),
            root_id
        );
    }
    qpdf_check(&out);
}

#[test]
fn renumbers_references_and_nulls_dangling_ones() {
    let dir = Dir::new("refs");
    let a = dir.file("a.pdf", &inheriting_document(1, "A"));
    let b = dir.file("b.pdf", &annotated_document());
    let out = dir.path("out.pdf");
    nori::merge(&[&a, &b], &out, 1).unwrap();

    let doc = Document::load(&out).unwrap();
    let page_id = pages(&doc)[1];
    let page = doc.get_dictionary(page_id).unwrap();
    let annots = page.get(b"Annots").unwrap().as_array().unwrap();
    let annot = doc
        .get_dictionary(annots[0].as_reference().unwrap())
        .unwrap();
    assert_eq!(annot.get(b"P").unwrap().as_reference().unwrap(), page_id);
    assert!(matches!(annots[1], Object::Null));

    let resources = page.get(b"Resources").unwrap().as_dict().unwrap();
    let states = resources.get(b"ExtGState").unwrap().as_dict().unwrap();
    let state = states.get(b"a b/c").unwrap().as_dict().unwrap();
    assert_eq!(state.get(b"CA").unwrap().as_float().unwrap(), 0.5);
    qpdf_check(&out);
}

#[test]
fn keeps_stream_data_as_is() {
    let dir = Dir::new("streams");
    let out = dir.path("out.pdf");
    nori::merge(&[fixture(), fixture()], &out, 1).unwrap();

    let original = Document::load(fixture()).unwrap();
    let merged = Document::load(&out).unwrap();
    let count = pages(&original).len();
    assert_eq!(pages(&merged).len(), count * 2);
    for (index, page_id) in pages(&original).into_iter().enumerate() {
        let expected = original.get_page_content(page_id);
        for copy in [index, index + count] {
            assert_eq!(
                merged.get_page_content(pages(&merged)[copy]),
                expected,
                "page {copy}"
            );
        }
    }
    qpdf_check(&out);
}

#[test]
fn rejects_unreadable_input_and_leaves_no_output() {
    let dir = Dir::new("broken");
    let good = dir.file("good.pdf", &inheriting_document(1, "A"));
    let broken = dir.file("broken.pdf", b"%PDF-1.4\nthis is not a pdf");
    let out = dir.path("out.pdf");

    let err = nori::merge(&[&good, &broken], &out, 1).unwrap_err();
    assert!(matches!(err, nori::Error::Read { .. }), "{err}");
    assert!(err.to_string().contains("broken.pdf"));
    assert!(!out.exists());

    let err = nori::merge(&[dir.path("missing.pdf")], &out, 1).unwrap_err();
    assert!(matches!(err, nori::Error::Read { .. }), "{err}");
    assert!(!out.exists());

    let err = nori::merge::<PathBuf>(&[], &out, 1).unwrap_err();
    assert!(matches!(err, nori::Error::NoInputs));
}

#[test]
fn rejects_input_without_pages() {
    let dir = Dir::new("nopages");
    let mut doc = Document::with_version("1.4");
    let pages_id = doc.add_object(
        dictionary! { "Type" => "Pages", "Kids" => Vec::<Object>::new(), "Count" => 0 },
    );
    let catalog_id = doc.add_object(dictionary! { "Type" => "Catalog", "Pages" => pages_id });
    doc.trailer.set("Root", catalog_id);
    let empty = dir.file("empty.pdf", &save(doc));
    let out = dir.path("out.pdf");

    let err = nori::merge(&[&empty], &out, 1).unwrap_err();
    assert!(matches!(err, nori::Error::NoPages(_)), "{err}");
    assert!(!out.exists());
}

#[test]
fn announces_the_newest_input_version() {
    let dir = Dir::new("version");
    let saved = annotated_document();
    let header = &saved[..8];
    assert_eq!(
        header, b"%PDF-1.5",
        "lopdf writes 1.5; the test rewrites the header"
    );
    let old = dir.file("old.pdf", &[b"%PDF-1.4", &saved[8..]].concat());
    let new = dir.file("new.pdf", &[b"%PDF-1.7", &saved[8..]].concat());
    let out = dir.path("out.pdf");
    nori::merge(&[&old, &new], &out, 1).unwrap();

    let bytes = std::fs::read(&out).unwrap();
    assert!(
        bytes.starts_with(b"%PDF-1.4\n"),
        "the header follows the first input"
    );
    let doc = Document::load(&out).unwrap();
    let announced = doc
        .catalog()
        .unwrap()
        .get(b"Version")
        .unwrap()
        .as_name()
        .unwrap();
    assert_eq!(announced, b"1.7", "the catalog announces the newest input");

    nori::merge(&[&new, &old], &out, 1).unwrap();
    let doc = Document::load(&out).unwrap();
    assert!(
        doc.catalog().unwrap().get(b"Version").is_err(),
        "nothing to announce when the header is newest"
    );
}

#[test]
fn parallel_parsing_gives_the_same_output_in_the_same_order() {
    let dir = Dir::new("jobs");
    let mut inputs = Vec::new();
    for i in 0..23 {
        inputs.push(dir.file(
            &format!("{i}.pdf"),
            &inheriting_document(i % 3 + 1, &format!("doc{i}")),
        ));
    }
    inputs.push(fixture());
    inputs.push(dir.file("broken.pdf", b"%PDF-1.4\nnot a pdf"));

    let good = &inputs[..inputs.len() - 1];
    let sequential = dir.path("sequential.pdf");
    let parallel = dir.path("parallel.pdf");
    nori::merge(good, &sequential, 1).unwrap();
    for jobs in [2, 4, 64] {
        nori::merge(good, &parallel, jobs).unwrap();
        assert_eq!(
            std::fs::read(&parallel).unwrap(),
            std::fs::read(&sequential).unwrap(),
            "jobs = {jobs}"
        );
    }

    let err = nori::merge(&inputs, &parallel, 4).unwrap_err();
    assert!(err.to_string().contains("broken.pdf"), "{err}");
    assert!(!parallel.exists());
}

#[test]
fn cli_merges_positional_and_listed_inputs() {
    let dir = Dir::new("cli");
    let a = dir.file("a.pdf", &inheriting_document(2, "A"));
    let b = dir.file("b.pdf", &inheriting_document(3, "B"));
    let list = dir.file(
        "list.txt",
        format!("{}\n\n{}\r\n", b.display(), a.display()).as_bytes(),
    );
    let out = dir.path("out.pdf");

    let status = Command::new(env!("CARGO_BIN_EXE_nori"))
        .args([
            "-o",
            out.to_str().unwrap(),
            a.to_str().unwrap(),
            "--list",
            list.to_str().unwrap(),
        ])
        .status()
        .unwrap();
    assert!(status.success());
    assert_eq!(pages(&Document::load(&out).unwrap()).len(), 7);
}

#[test]
fn cli_reports_errors_on_stderr() {
    let dir = Dir::new("cli-errors");
    let a = dir.file("a.pdf", &inheriting_document(1, "A"));
    let out = dir.path("out.pdf");

    let output = Command::new(env!("CARGO_BIN_EXE_nori"))
        .args([
            "-o",
            out.to_str().unwrap(),
            a.to_str().unwrap(),
            dir.path("missing.pdf").to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(1));
    assert!(String::from_utf8_lossy(&output.stderr).starts_with("nori: "));
    assert!(!out.exists());

    let output = Command::new(env!("CARGO_BIN_EXE_nori"))
        .args(["-o", a.to_str().unwrap(), a.to_str().unwrap()])
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(1));
    assert!(
        String::from_utf8_lossy(&output.stderr).contains("output must not be one of the inputs")
    );
    assert!(Document::load(&a).is_ok(), "the input is untouched");
}
