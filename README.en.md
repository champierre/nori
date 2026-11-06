# nori

English | [日本語](README.md)

A Rust CLI and library that merges PDF files into one. "Nori" is Japanese for glue.

Inputs are read one at a time. The objects each page refers to are written to the output under new object numbers, and the input is dropped before the next one is opened. Nothing is held back until the end, so memory use stays around the size of the largest single input, however many files are merged. It was written to join thousands of per-recipient PDFs into one print file.

```bash
nori -o merged.pdf a.pdf b.pdf c.pdf
```

## Comparison with qpdf and lopdf

The same 14-page PDF was copied 10 to 2,000 times and merged with nori, with [qpdf](https://qpdf.sourceforge.io/), and with the merge code from the [lopdf](https://github.com/J-F-Liu/lopdf) README. Wall-clock time, peak memory and output size were measured; see [How the comparison was made](#how-the-comparison-was-made).

Measured on a Mac (Intel Core i5-8500B, 6 cores, 16 GB, macOS 15.8) with qpdf 12.4.2, lopdf 0.47.0 and nori 0.1.0. Values are the median of 5 runs; memory is peak RSS. `nori -j6` parses six inputs at a time. A `-` marks a case not run because the next step would not fit in memory (on the Chrome PDF, qpdf needs 5 GB at 1,000 files and lopdf 2.6 GB at 100).

### PDF made by LibreOffice (14 pages, 58 objects, 73 KB)

Time

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 22 ms | 18 ms | 151 ms | 26 ms |
| 100 | 1,400 | 76 ms | 49 ms | 1.34 s | 141 ms |
| 1,000 | 14,000 | 577 ms | 331 ms | 15.08 s | 2.31 s |
| 2,000 | 28,000 | 1.30 s | 762 ms | 31.38 s | 6.63 s |

Peak memory

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 2.2 MB | 4.2 MB | 5.8 MB | 5.8 MB |
| 100 | 1,400 | 3.3 MB | 5.3 MB | 24.9 MB | 48.3 MB |
| 1,000 | 14,000 | 4.7 MB | 7.1 MB | 211.2 MB | 461.6 MB |
| 2,000 | 28,000 | 5.9 MB | 8.5 MB | 419.1 MB | 918.3 MB |

Output size

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 0.7 MB | 0.7 MB | 0.7 MB | 0.7 MB |
| 100 | 1,400 | 6.6 MB | 6.6 MB | 6.7 MB | 6.7 MB |
| 1,000 | 14,000 | 65.9 MB | 65.9 MB | 66.8 MB | 67.2 MB |
| 2,000 | 28,000 | 131.9 MB | 131.9 MB | 133.6 MB | 134.5 MB |

On inputs with few objects, nori is 7 to 24 times faster than qpdf and uses 6 MB even for 2,000 files (28,000 pages). qpdf and lopdf grow in proportion to the number of inputs.

### PDF made by Chrome (14 pages, 3,002 objects, 670 KB)

Time

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 311 ms | 157 ms | 399 ms | 669 ms |
| 100 | 1,400 | 2.74 s | 1.44 s | 3.71 s | 6.87 s |
| 1,000 | 14,000 | 28.01 s | 14.01 s | 85.33 s | - |
| 2,000 | 28,000 | 54.33 s | 28.71 s | - | - |

Peak memory

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 51.9 MB | 117.6 MB | 70.3 MB | 272.1 MB |
| 100 | 1,400 | 76.6 MB | 138.5 MB | 672.8 MB | 2.63 GB |
| 1,000 | 14,000 | 79.6 MB | 210.8 MB | 5.05 GB | - |
| 2,000 | 28,000 | 83.4 MB | 253.6 MB | - | - |

Output size

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 2.6 MB | 2.6 MB | 2.7 MB | 6.1 MB |
| 100 | 1,400 | 26.6 MB | 26.6 MB | 26.7 MB | 62.2 MB |
| 1,000 | 14,000 | 267.7 MB | 267.7 MB | 268.3 MB | - |
| 2,000 | 28,000 | 536.0 MB | 536.0 MB | - | - |

On inputs with many objects, lopdf takes 24 ms to parse each file, which is 80% of nori's time. nori is still 1.3 to 3 times faster than qpdf, and 2.5 to 6 times with `-j6`. qpdf reaches 5 GB at 1,000 files where nori uses 80 MB, and nori stays at 83 MB for 2,000 files. lopdf's output is twice the size because the README's merge code keeps objects that no page refers to, such as the structure tree of tagged PDF.

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
