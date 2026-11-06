//! Merges PDFs the way the lopdf README shows: every input is loaded, all
//! objects are renumbered into one `Document`, and that is saved at the end.
//! The bookmark handling of the example is left out; the rest is as written.
//!
//! Usage: lopdf-merge -o OUTPUT INPUT...

use lopdf::{Dictionary, Document, Error, Object, ObjectId};
use std::collections::{BTreeMap, HashSet};
use std::process::ExitCode;

fn inherited_page_attribute(
    doc: &Document,
    page_id: ObjectId,
    key: &[u8],
) -> lopdf::Result<Option<Object>> {
    let mut current = page_id;
    let mut visited = HashSet::new();
    loop {
        if !visited.insert(current) {
            return Err(Error::ReferenceCycle(current));
        }
        let node = doc.get_dictionary(current)?;
        if let Ok(value) = node.get(key) {
            match doc.dereference(value) {
                Ok((_, Object::Null)) | Err(Error::ObjectNotFound(_)) => {}
                Ok(_) => return Ok(Some(value.clone())),
                Err(error) => return Err(error),
            }
        }
        match node.get(b"Parent") {
            Err(_) | Ok(Object::Null) => return Ok(None),
            Ok(parent) => current = parent.as_reference()?,
        }
    }
}

fn materialize_page_attributes(doc: &Document, page_id: ObjectId) -> lopdf::Result<Dictionary> {
    let mut page = doc.get_dictionary(page_id)?.clone();
    let media_box = inherited_page_attribute(doc, page_id, b"MediaBox")?
        .ok_or_else(|| Error::DictKey("MediaBox".to_string()))?;
    let crop_box =
        inherited_page_attribute(doc, page_id, b"CropBox")?.unwrap_or_else(|| media_box.clone());
    let resources = inherited_page_attribute(doc, page_id, b"Resources")?
        .unwrap_or_else(|| Object::Dictionary(Dictionary::new()));
    let rotation = inherited_page_attribute(doc, page_id, b"Rotate")?.unwrap_or(Object::Integer(0));
    page.set("MediaBox", media_box);
    page.set("CropBox", crop_box);
    page.set("Resources", resources);
    page.set("Rotate", rotation);
    Ok(page)
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let (output, inputs) = match args.as_slice() {
        [flag, output, inputs @ ..] if flag == "-o" && !inputs.is_empty() => {
            (output.clone(), inputs.to_vec())
        }
        _ => {
            eprintln!("usage: lopdf-merge -o OUTPUT INPUT...");
            return ExitCode::from(2);
        }
    };

    // Define a starting `max_id` (will be used as start index for object_ids).
    let mut max_id = 1;
    // Collect all Documents Objects grouped by a map
    let mut documents_pages = BTreeMap::new();
    let mut documents_objects = BTreeMap::new();
    let mut document = Document::with_version("1.5");

    for path in &inputs {
        let mut doc = match Document::load(path) {
            Ok(doc) => doc,
            Err(e) => {
                eprintln!("lopdf-merge: {path}: {e}");
                return ExitCode::from(1);
            }
        };
        // Resolve inheritance before renumbering can make a missing reference alias another object.
        for page_id in doc.get_pages().into_values() {
            let page = materialize_page_attributes(&doc, page_id).unwrap();
            doc.objects.insert(page_id, Object::Dictionary(page));
        }
        doc.renumber_objects_with(max_id);

        max_id = doc.max_id + 1;

        documents_pages.extend(
            doc.get_pages()
                .into_iter()
                .map(|(_, object_id)| (object_id, doc.get_object(object_id).unwrap().to_owned()))
                .collect::<BTreeMap<ObjectId, Object>>(),
        );
        documents_objects.extend(doc.objects);
    }

    let mut catalog_object: Option<(ObjectId, Object)> = None;
    let mut pages_object: Option<(ObjectId, Object)> = None;

    for (object_id, object) in documents_objects.iter() {
        match object.type_name().unwrap_or(b"") {
            b"Catalog" => {
                catalog_object = Some((
                    if let Some((id, _)) = catalog_object {
                        id
                    } else {
                        *object_id
                    },
                    object.clone(),
                ));
            }
            b"Pages" => {
                if let Ok(dictionary) = object.as_dict() {
                    let mut dictionary = dictionary.clone();
                    if let Some((_, ref object)) = pages_object
                        && let Ok(old_dictionary) = object.as_dict()
                    {
                        dictionary.extend(old_dictionary);
                    }

                    pages_object = Some((
                        if let Some((id, _)) = pages_object {
                            id
                        } else {
                            *object_id
                        },
                        Object::Dictionary(dictionary),
                    ));
                }
            }
            b"Page" => {}     // Ignored, processed later and separately
            b"Outlines" => {} // Ignored, not supported yet
            b"Outline" => {}  // Ignored, not supported yet
            _ => {
                document.objects.insert(*object_id, object.clone());
            }
        }
    }

    let Some(pages_object) = pages_object else {
        eprintln!("Pages root not found.");
        return ExitCode::from(1);
    };

    for (object_id, object) in documents_pages.iter() {
        if let Ok(dictionary) = object.as_dict() {
            let mut dictionary = dictionary.clone();
            dictionary.set("Parent", pages_object.0);

            document
                .objects
                .insert(*object_id, Object::Dictionary(dictionary));
        }
    }

    let Some(catalog_object) = catalog_object else {
        eprintln!("Catalog root not found.");
        return ExitCode::from(1);
    };

    // Build a new "Pages" with updated fields
    if let Ok(dictionary) = pages_object.1.as_dict() {
        let mut dictionary = dictionary.clone();

        // The rebuilt root has no parent, even when an original node did.
        dictionary.remove(b"Parent");
        // Each page now carries its original attributes; never combine them at the root.
        for key in ["MediaBox", "CropBox", "Resources", "Rotate"] {
            dictionary.remove(key.as_bytes());
        }

        // Set new pages count
        dictionary.set("Count", documents_pages.len() as u32);

        // Set new "Kids" list (collected from documents pages) for "Pages"
        dictionary.set(
            "Kids",
            documents_pages
                .into_iter()
                .map(|(object_id, _)| Object::Reference(object_id))
                .collect::<Vec<_>>(),
        );

        document
            .objects
            .insert(pages_object.0, Object::Dictionary(dictionary));
    }

    // Build a new "Catalog" with updated fields
    if let Ok(dictionary) = catalog_object.1.as_dict() {
        let mut dictionary = dictionary.clone();
        dictionary.set("Pages", pages_object.0);
        dictionary.remove(b"Outlines"); // Outlines not supported in merged PDFs

        document
            .objects
            .insert(catalog_object.0, Object::Dictionary(dictionary));
    }

    document.trailer.set("Root", catalog_object.0);

    // Update the max internal ID as wasn't updated before due to direct objects insertion
    document.max_id = document.objects.len() as u32;

    // Reorder all new Document objects
    document.renumber_objects();

    document.compress();

    // Save the merged PDF.
    if let Err(e) = document.save(&output) {
        eprintln!("lopdf-merge: {output}: {e}");
        return ExitCode::from(1);
    }
    ExitCode::SUCCESS
}
