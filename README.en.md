# nori

English | [日本語](README.md)

A Rust CLI and library that merges PDF files into one. "Nori" is Japanese for glue.

Inputs are read one at a time. The objects each page refers to are written to the output under new object numbers, and the input is dropped before the next one is opened. Nothing is held back until the end, so memory use stays around the size of the largest single input, however many files are merged. It was written to join thousands of per-recipient PDFs into one print file.

```bash
nori -o merged.pdf a.pdf b.pdf c.pdf
```

## Comparison with qpdf and lopdf

PDFs picked at random from Wikimedia Commons were merged with nori, with [qpdf](https://qpdf.sourceforge.io/), and with the merge code from the [lopdf](https://github.com/J-F-Liu/lopdf) README. Wall-clock time, peak memory and output size were measured; see [How the comparison was made](#how-the-comparison-was-made) for the procedure and how the inputs were chosen.

Measured on a Mac (Intel Core i5-8500B, 6 cores, 16 GB, macOS 15.8) with qpdf 12.4.2, lopdf 0.47.0 and nori 0.1.0. Values are the median of 5 runs; memory is peak RSS. `nori -j6` parses six inputs at a time. A `-` marks a case not run because the next step would not fit in memory.

### 40 PDFs of every make, merged once

40 random files (277 pages, 33.8 MB in all: official journals, regulations, scanned newspapers and notebooks, Internet Archive books) were merged in one go, in name order. All four tools produced a 277-page output that passes qpdf's check. The list is in `bench/public-pdfs.json`.

| | nori | nori -j6 | qpdf | lopdf |
|---|---:|---:|---:|---:|
| Time | 88 ms | 53 ms | 1.43 s | 170 ms |
| Peak memory | 21.3 MB | 36.8 MB | 30.3 MB | 111.2 MB |
| Output size | 32.0 MB | 32.0 MB | 31.9 MB | 33.7 MB |

### One PDF copied 10 to 2,000 times

Three of the 40 were chosen for how differently they are built.

| PDF | What it is | Pages | Objects | Size |
|---|---|---:|---:|---:|
| [UK regulation](https://commons.wikimedia.org/wiki/File:The_Organic_Products_(Amendment)_Regulations_2015_(UKSI_2015-1669_qp).pdf) | Text only, made with Ghostscript; a light PDF | 4 | 36 | 40 KB |
| [EU Official Journal](https://commons.wikimedia.org/wiki/File:OJ_C_202301032_of_2023_-_SK_Slovak.pdf) | Made with PDFlib, with many objects per page | 7 | 478 | 540 KB |
| [Scanned newspaper](https://commons.wikimedia.org/wiki/File:The_New_Orleans_Bee_1900_October_0074.pdf) | A 1900 front page; each page is one image | 1 | 9 | 610 KB |

#### UK regulation (4 pages, 36 objects, 40 KB)

Time

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 17 ms | 16 ms | 44 ms | 29 ms |
| 100 | 400 | 59 ms | 41 ms | 203 ms | 109 ms |
| 1,000 | 4,000 | 522 ms | 360 ms | 3.28 s | 1.49 s |
| 2,000 | 8,000 | 1.12 s | 626 ms | 5.86 s | 3.61 s |

Peak memory

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 1.8 MB | 3.6 MB | 5.4 MB | 4.5 MB |
| 100 | 400 | 2.8 MB | 5.4 MB | 24.7 MB | 35.2 MB |
| 1,000 | 4,000 | 4.6 MB | 7.5 MB | 212.8 MB | 349.7 MB |
| 2,000 | 8,000 | 5.7 MB | 8.5 MB | 422.5 MB | 694.7 MB |

Output size

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 0.4 MB | 0.4 MB | 0.4 MB | 0.4 MB |
| 100 | 400 | 3.8 MB | 3.8 MB | 3.8 MB | 3.8 MB |
| 1,000 | 4,000 | 38.4 MB | 38.4 MB | 38.4 MB | 38.2 MB |
| 2,000 | 8,000 | 76.8 MB | 76.8 MB | 76.8 MB | 76.3 MB |

#### EU Official Journal (7 pages, 478 objects, 540 KB)

Time

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 46 ms | 33 ms | 93 ms | 95 ms |
| 100 | 700 | 343 ms | 189 ms | 778 ms | 925 ms |
| 1,000 | 7,000 | 3.46 s | 2.03 s | 8.59 s | - |
| 2,000 | 14,000 | 6.14 s | 3.96 s | 17.95 s | - |

Peak memory

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 5.0 MB | 23.5 MB | 14.0 MB | 42.3 MB |
| 100 | 700 | 13.0 MB | 27.8 MB | 105.4 MB | 409.6 MB |
| 1,000 | 7,000 | 14.8 MB | 33.4 MB | 1.02 GB | - |
| 2,000 | 14,000 | 16.3 MB | 36.7 MB | 2.03 GB | - |

Output size

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 4.9 MB | 4.9 MB | 4.9 MB | 5.4 MB |
| 100 | 700 | 49.2 MB | 49.2 MB | 49.2 MB | 54.1 MB |
| 1,000 | 7,000 | 492.0 MB | 492.0 MB | 492.0 MB | - |
| 2,000 | 14,000 | 984.2 MB | 984.2 MB | 984.3 MB | - |

#### Scanned newspaper (1 page, 9 objects, 610 KB)

Time

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 21 ms | 19 ms | 31 ms | 26 ms |
| 100 | 100 | 70 ms | 61 ms | 104 ms | 133 ms |
| 1,000 | 1,000 | 715 ms | 661 ms | 1.16 s | 1.62 s |
| 2,000 | 2,000 | 1.53 s | 1.41 s | 2.60 s | - |

Peak memory

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 3.6 MB | 11.4 MB | 4.9 MB | 14.0 MB |
| 100 | 100 | 3.9 MB | 10.4 MB | 7.9 MB | 128.0 MB |
| 1,000 | 1,000 | 4.6 MB | 11.7 MB | 30.6 MB | 1.26 GB |
| 2,000 | 2,000 | 5.4 MB | 11.8 MB | 56.7 MB | - |

Output size

| Files | Pages | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 6.1 MB | 6.1 MB | 6.1 MB | 6.1 MB |
| 100 | 100 | 61.1 MB | 61.1 MB | 61.1 MB | 61.1 MB |
| 1,000 | 1,000 | 610.7 MB | 610.7 MB | 610.8 MB | 610.9 MB |
| 2,000 | 2,000 | 1.22 GB | 1.22 GB | 1.22 GB | - |

### What the numbers say

- With few objects per file, both speed and memory differ by orders of magnitude. Merging 2,000 copies of the regulation (8,000 pages) took nori 1.12 s and 5.7 MB, qpdf 5.9 s and 423 MB, lopdf 3.6 s and 695 MB. nori's memory barely moved from the 1.8 MB it used for 10 files
- With many objects per file, memory still stays flat. The journal has 478 objects per file and takes longer to parse, yet nori is 2.9 times faster than qpdf, 4.5 times with `-j6`. At 2,000 files nori used 16 MB and qpdf 2 GB
- With scanned images, the gap in time narrows. The newspaper has 9 objects per page, so merging is mostly copying image data. For 2,000 files (1.2 GB) nori took 1.53 s and qpdf 2.60 s, 1.7 times apart, but memory was 5.4 MB for nori, 57 MB for qpdf and 1.3 GB for lopdf at 1,000 files
- lopdf is not slow; the merge code is the problem. nori itself parses inputs with lopdf. The README's merge code gathers every input into one `Document` and saves at the end, so memory grows with the total input, and objects no page refers to stay in the output, which makes it a little larger
- Outputs are about the same size from every tool, all pass `qpdf --check`, and all have the expected page count

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

`bench/bench.py` runs each tool as a command and takes wall-clock time and peak RSS from `/usr/bin/time`. Each output is checked with qpdf for its page count and with `qpdf --check`. There are two kinds of run.

- `--fixture`: one PDF is copied 10 to 2,000 times and merged, to show how time and memory grow with the number of files
- `--corpus`: every PDF in a directory is merged once, all together, to show that real-world files of every make come through

The inputs are PDFs picked at random from Wikimedia Commons. `bench/fetch.py select` asks CirrusSearch for PDFs in random order (`srsort=random`), keeps 40 that are at most 3 MB and 60 pages, and writes their titles, URLs and licenses to `bench/public-pdfs.json`. `bench/fetch.py fetch` downloads that list into `bench/inputs/public/` (the PDFs themselves are not in the repository). For the scaling runs, three of the 40 were chosen for how differently they are built.

```bash
cargo build --release --workspace
python3 bench/fetch.py fetch
python3 bench/bench.py --corpus bench/inputs/public
python3 bench/bench.py --fixture bench/inputs/public/public-17.pdf
python3 bench/bench.py --fixture bench/inputs/public/public-13.pdf --max-count lopdf=100
python3 bench/bench.py --fixture bench/inputs/public/public-24.pdf --max-count lopdf=1000
```

- qpdf is run as `qpdf --warning-exit-0 --empty --pages <inputs>... -- <output>`
- lopdf is `bench/lopdf-merge/`, the merge code from the lopdf README made into a binary. It loads every input, gathers all objects into one `Document`, and saves at the end
- nori itself parses inputs with lopdf. lopdf is neither slow nor memory-hungry; the README's merge code holds every input in memory until the final save, so its memory grows with the total input. nori writes each input out as soon as it is read, so its memory does not depend on the number of inputs
- `--max-count` stops a tool before its memory would exceed the benchmark machine's 16 GB

## Tests

```bash
cargo test
```

With qpdf installed, outputs are also run through `qpdf --check`; without it that check is skipped.

## License

MIT
