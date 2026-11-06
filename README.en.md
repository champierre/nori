# nori

English | [日本語](README.md)

A Rust CLI and library that merges PDF files into one. "Nori" is Japanese for glue.

Inputs are read one at a time. The objects each page refers to are written to the output under new object numbers, and the input is dropped before the next one is opened. Nothing is held back until the end, so memory use stays around the size of the largest single input, however many files are merged. It was written to join thousands of per-recipient PDFs into one print file.

```bash
nori -o merged.pdf a.pdf b.pdf c.pdf
```

## Comparison with qpdf and lopdf

The same 14-page PDF was copied 10 to 2,000 times and merged with nori, with [qpdf](https://qpdf.sourceforge.io/), and with the merge code from the [lopdf](https://github.com/J-F-Liu/lopdf) README. Wall-clock time, peak memory and output size were measured; see [How the comparison was made](#how-the-comparison-was-made).

<!-- BENCH -->

## Installation

### From source

```bash
cargo install --git https://github.com/champierre/nori
```

Rust 1.88 or later. The result is a single `nori` binary with no dependency on qpdf or other external commands.

## CLI

```
nori -o <output> [-j <N>] [--list <file>] <input>...
```

| Option | Meaning |
|---|---|
| `-o`, `--output <FILE>` | Output file. Overwritten if it exists. Must not be one of the inputs |
| `--list <FILE>` | File listing inputs, one path per line, appended after the positional inputs. `-` reads the list from standard input |
| `-j`, `--jobs <N>` | Inputs parsed at once on separate threads (default 1). Inputs with many objects merge close to N times faster; up to about 2N inputs are held in memory |

Pages come out in argument order (line order inside `--list`). Use `--list` when the number of inputs exceeds the shell's argument limit.

### Exit codes

| Code | Meaning |
|---:|---|
| 0 | Success |
| 1 | An input could not be read, has no pages, or the output could not be written. The reason goes to standard error as `nori: ...` and no output file is left behind |
| 2 | Invalid arguments |

One unreadable input fails the whole merge, as does a PDF without pages.

## Rust API

```rust
let inputs = ["a.pdf", "b.pdf"];
let summary = nori::merge(&inputs, std::path::Path::new("merged.pdf"), 1)?;
println!("{} pages from {} files", summary.pages, summary.inputs);
```

`nori::merge_into` writes to any `std::io::Write`. The last argument is the same as `-j`.

## Using from Rails

Call it as an external command, the same way as qpdf: write the inputs to files and pass the paths.

```ruby
Dir.mktmpdir do |dir|
  inputs = pdfs.each_with_index.map do |pdf, i|
    File.join(dir, "#{i}.pdf").tap { |path| File.binwrite(path, pdf) }
  end
  output = File.join(dir, "merged.pdf")
  _out, err, status = Open3.capture3("nori", "-o", output, *inputs)
  raise "PDF merge failed: #{err}" unless status.success?
  File.binread(output)
end
```

## What the output looks like

- Pages keep their input order. Whatever a page refers to (content streams, resources, fonts, images, annotations and so on) is copied as far as references reach
- `MediaBox`, `CropBox`, `Resources` and `Rotate` set higher up in an input's page tree are written into each page, because the output gets a page tree of its own
- Stream data is written exactly as read, neither decompressed nor recompressed
- The page tree has two levels: intermediate nodes of 256 pages each under the root
- The output uses no object streams, so it is plain PDF 1.4-style syntax. The header carries the first input's version; a newer input is announced through `/Version` in the catalog
- References to objects that do not exist become `null`

## Limitations

- Only pages and what they refer to are copied. Outlines (bookmarks), AcroForm fields, named destinations, the structure tree of tagged PDF, the document information dictionary and XMP metadata are not carried over. References to pages, such as `/P` in annotations, are redirected to the output pages
- Encrypted PDFs are readable only as far as lopdf can decrypt them
- Parsing is done by lopdf, so a PDF lopdf cannot read cannot be merged

## How the comparison was made

`bench/bench.py` copies a PDF from `bench/fixtures/` as many times as the file count says, runs each tool on the copies, and takes wall-clock time and peak RSS from `/usr/bin/time`. Each output is checked with qpdf for its page count and with `qpdf --check`.

```bash
cargo build --release --workspace
python3 bench/bench.py --counts 10,100,1000,2000 --runs 5 --max-count lopdf=100
```

- qpdf is run as `qpdf --warning-exit-0 --empty --pages <inputs>... -- <output>`
- lopdf is `bench/lopdf-merge/`, the merge code from the lopdf README made into a binary. It loads every input, gathers all objects into one `Document`, and saves at the end
- nori itself parses inputs with lopdf. lopdf is neither slow nor memory-hungry; the README's merge code holds every input in memory until the final save, so its memory grows with the total input. nori writes each input out as soon as it is read, so its memory does not depend on the number of inputs

The benchmark PDFs are the same HTML rendered to PDF by LibreOffice and by Google Chrome (`bench/fixtures/make_fixtures.py`). Both are 14 pages, but they are built very differently.

| | LibreOffice | Chrome |
|---|---:|---:|
| Objects | 58 | 3,002 |
| Fonts | embedded subsets | Type3, one stream per glyph |
| Size | 73 KB | 670 KB |

## Tests

```bash
cargo test
```

With qpdf installed, outputs are also run through `qpdf --check`; without it that check is skipped.

## License

MIT
