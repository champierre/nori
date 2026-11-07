# nori

[English](README.en.md) | 日本語

複数の PDF を 1 つにつなぐ Rust 製の CLI 兼ライブラリです。「糊」の nori。

入力を 1 ファイルずつ読み、そのページが参照するオブジェクトだけを新しい番号で出力に書き出してから、次のファイルを開きます。全部の入力を読み込んでから書くのではないので、メモリ使用量は入力の数に関係なく、いちばん大きい入力 1 つ分にとどまります。宛先ごとに作った帳票 PDF を数千件つないで 1 つの印刷用 PDF にする、といった用途のために作りました。

```bash
nori -o merged.pdf a.pdf b.pdf c.pdf
```

## qpdf と lopdf との比較

Wikimedia Commons からランダムに選んだ PDF をつなぎ、[qpdf](https://qpdf.sourceforge.io/) と、[lopdf](https://github.com/J-F-Liu/lopdf) の README にある結合コードとで、実行時間・メモリ使用量・出力サイズを比べました。計測の手順と入力の選び方は「[比較方法](#比較方法)」にあります。

Mac と Linux の 2 台で計測しました。入力の PDF は同じものですが、数値は環境によって変わります。値は 5 回の中央値、メモリは最大 RSS です。`nori -j6`・`nori -j8` は、そのマシンのコア数のスレッドで解析を先行させた場合です。`-` は、その先を測るとメモリがマシンに収まらないため打ち切った箇所です。

| | Mac | Linux |
|---|---|---|
| マシン | Intel Core i5-8500B（6 コア）、メモリ 16 GB | AMD Ryzen 7 6800H（8 コア 16 スレッド）、GEEKOM A6、メモリ 32 GB |
| OS | macOS 15.8 | Omarchy 4.0.6（Arch Linux ベース）、Linux 7.2.8 |
| ツール | nori 0.1.0、qpdf 12.4.2、lopdf 0.47.0 | nori 0.1.0、qpdf 12.4.2、lopdf 0.47.0 |

### 日本語の PDF をまとめてつなぐ

Commons の「Japanese-language PDF files」カテゴリからランダムに選んだ 20 件（115 ページ、合計 8.9 MB。官庁の資料、法令、通知のスキャン、楽譜、Google ドキュメントの書き出しなど）を名前の順に 1 回でつなぎました。4 ツールとも 115 ページの出力を作り、qpdf の検査も通っています。一覧は `bench/public-pdfs-ja.json` にあります。

Mac（Intel Core i5-8500B）

| | nori | nori -j6 | qpdf | lopdf |
|---|---:|---:|---:|---:|
| 実行時間 | 56 ms | 43 ms | 118 ms | 87 ms |
| 最大メモリ | 17.1 MB | 21.7 MB | 14.7 MB | 39.7 MB |
| 出力サイズ | 8.7 MB | 8.7 MB | 8.7 MB | 8.9 MB |

Linux（AMD Ryzen 7 6800H）

| | nori | nori -j8 | qpdf | lopdf |
|---|---:|---:|---:|---:|
| 実行時間 | 24 ms | 18 ms | 53 ms | 43 ms |
| 最大メモリ | 12.8 MB | 25.3 MB | 18.7 MB | 35.1 MB |
| 出力サイズ | 8.7 MB | 8.7 MB | 8.7 MB | 8.9 MB |

### 日本語の法律案を 10〜2,000 個つなぐ

[スマートフォンにおいて利用される特定ソフトウェアに係る競争の促進に関する法律案 新旧対照条文](https://commons.wikimedia.org/wiki/File:スマートフォンにおいて利用される特定ソフトウェアに係る競争の促進に関する法律案_新旧対照条文.pdf)（内閣官房、CC BY 4.0）。JUST PDF 4 で作られ、ＭＳ明朝のサブセットを埋め込んだ 14 ページ・65 オブジェクト・140 KB の条文の表で、日本語の帳票にいちばん近い入力です。

実行時間（Mac）

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 20 ms | 18 ms | 50 ms | 28 ms |
| 100 | 1,400 | 77 ms | 66 ms | 284 ms | 183 ms |
| 1,000 | 14,000 | 711 ms | 406 ms | 3.83 s | 2.59 s |
| 2,000 | 28,000 | 1.28 s | 775 ms | 7.53 s | 7.47 s |

実行時間（Linux）

| ファイル数 | ページ数 | nori | nori -j8 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 7 ms | 6 ms | 24 ms | 11 ms |
| 100 | 1,400 | 29 ms | 18 ms | 186 ms | 89 ms |
| 1,000 | 14,000 | 283 ms | 130 ms | 2.11 s | 1.36 s |
| 2,000 | 28,000 | 503 ms | 258 ms | 4.20 s | 3.48 s |

最大メモリ（Mac）

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 2.8 MB | 6.4 MB | 7.1 MB | 8.5 MB |
| 100 | 1,400 | 4.4 MB | 7.9 MB | 38.0 MB | 78.8 MB |
| 1,000 | 14,000 | 5.7 MB | 10.2 MB | 344.5 MB | 773.4 MB |
| 2,000 | 28,000 | 8.0 MB | 11.5 MB | 686.4 MB | 1.52 GB |

最大メモリ（Linux）

| ファイル数 | ページ数 | nori | nori -j8 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 140 | 5.0 MB | 8.3 MB | 15.8 MB | 9.9 MB |
| 100 | 1,400 | 5.1 MB | 10.4 MB | 50.1 MB | 72.3 MB |
| 1,000 | 14,000 | 5.8 MB | 13.2 MB | 389.7 MB | 696.6 MB |
| 2,000 | 28,000 | 6.6 MB | 14.2 MB | 768.2 MB | 1.39 GB |

出力サイズ

| ファイル数 | ページ数 | nori | qpdf | lopdf |
|---:|---:|---:|---:|---:|
| 10 | 140 | 1.3 MB | 1.3 MB | 1.3 MB |
| 100 | 1,400 | 13.5 MB | 13.5 MB | 13.4 MB |
| 1,000 | 14,000 | 135.0 MB | 135.0 MB | 134.4 MB |
| 2,000 | 28,000 | 270.0 MB | 270.0 MB | 268.9 MB |

### 世界中のばらばらな PDF をまとめてつなぐ

Commons 全体からランダムに選んだ 40 件（277 ページ、合計 33.8 MB。官報、法令、新聞やノートのスキャン、Internet Archive の書籍など）を名前の順に 1 回でつなぎました。4 ツールとも 277 ページの出力を作り、qpdf の検査も通っています。一覧は `bench/public-pdfs.json` にあります。

Mac（Intel Core i5-8500B）

| | nori | nori -j6 | qpdf | lopdf |
|---|---:|---:|---:|---:|
| 実行時間 | 88 ms | 53 ms | 1.43 s | 170 ms |
| 最大メモリ | 21.3 MB | 36.8 MB | 30.3 MB | 111.2 MB |
| 出力サイズ | 32.0 MB | 32.0 MB | 31.9 MB | 33.7 MB |

Linux（AMD Ryzen 7 6800H）

| | nori | nori -j8 | qpdf | lopdf |
|---|---:|---:|---:|---:|
| 実行時間 | 37 ms | 28 ms | 690 ms | 94 ms |
| 最大メモリ | 16.4 MB | 47.8 MB | 36.8 MB | 102.5 MB |
| 出力サイズ | 32.0 MB | 32.0 MB | 31.9 MB | 33.7 MB |

### 作り手の違う PDF を 10〜2,000 個つなぐ

40 件の中から、作りの違う 3 件を選んでコピーしました。

| PDF | どんな PDF か | ページ | オブジェクト | サイズ |
|---|---|---:|---:|---:|
| [英国の法令](https://commons.wikimedia.org/wiki/File:The_Organic_Products_(Amendment)_Regulations_2015_(UKSI_2015-1669_qp).pdf) | Ghostscript で作られた、文字だけの軽い PDF | 4 | 36 | 40 KB |
| [EU 官報](https://commons.wikimedia.org/wiki/File:OJ_C_202301032_of_2023_-_SK_Slovak.pdf) | PDFlib で作られた、1 ページあたりのオブジェクトが多い PDF | 7 | 478 | 540 KB |
| [新聞のスキャン](https://commons.wikimedia.org/wiki/File:The_New_Orleans_Bee_1900_October_0074.pdf) | 1900 年の新聞の 1 面。1 ページがまるごと画像 | 1 | 9 | 610 KB |

#### 英国の法令（4 ページ、36 オブジェクト、40 KB）

実行時間（Mac）

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 17 ms | 16 ms | 44 ms | 29 ms |
| 100 | 400 | 59 ms | 41 ms | 203 ms | 109 ms |
| 1,000 | 4,000 | 522 ms | 360 ms | 3.28 s | 1.49 s |
| 2,000 | 8,000 | 1.12 s | 626 ms | 5.86 s | 3.61 s |

実行時間（Linux）

| ファイル数 | ページ数 | nori | nori -j8 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 5 ms | 5 ms | 17 ms | 8 ms |
| 100 | 400 | 18 ms | 12 ms | 111 ms | 46 ms |
| 1,000 | 4,000 | 136 ms | 76 ms | 1.22 s | 515 ms |
| 2,000 | 8,000 | 279 ms | 148 ms | 2.44 s | 1.19 s |

最大メモリ（Mac）

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 1.8 MB | 3.6 MB | 5.4 MB | 4.5 MB |
| 100 | 400 | 2.8 MB | 5.4 MB | 24.7 MB | 35.2 MB |
| 1,000 | 4,000 | 4.6 MB | 7.5 MB | 212.8 MB | 349.7 MB |
| 2,000 | 8,000 | 5.7 MB | 8.5 MB | 422.5 MB | 694.7 MB |

最大メモリ（Linux）

| ファイル数 | ページ数 | nori | nori -j8 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 4.0 MB | 5.4 MB | 14.3 MB | 6.4 MB |
| 100 | 400 | 4.7 MB | 7.4 MB | 35.7 MB | 34.8 MB |
| 1,000 | 4,000 | 5.3 MB | 8.6 MB | 243.9 MB | 321.0 MB |
| 2,000 | 8,000 | 6.0 MB | 9.6 MB | 476.6 MB | 640.1 MB |

出力サイズ

| ファイル数 | ページ数 | nori | qpdf | lopdf |
|---:|---:|---:|---:|---:|
| 10 | 40 | 0.4 MB | 0.4 MB | 0.4 MB |
| 100 | 400 | 3.8 MB | 3.8 MB | 3.8 MB |
| 1,000 | 4,000 | 38.4 MB | 38.4 MB | 38.2 MB |
| 2,000 | 8,000 | 76.8 MB | 76.8 MB | 76.3 MB |

#### EU 官報（7 ページ、478 オブジェクト、540 KB）

実行時間（Mac）

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 46 ms | 33 ms | 93 ms | 95 ms |
| 100 | 700 | 343 ms | 189 ms | 778 ms | 925 ms |
| 1,000 | 7,000 | 3.46 s | 2.03 s | 8.59 s | - |
| 2,000 | 14,000 | 6.14 s | 3.96 s | 17.95 s | - |

実行時間（Linux）

| ファイル数 | ページ数 | nori | nori -j8 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 17 ms | 14 ms | 53 ms | 48 ms |
| 100 | 700 | 114 ms | 75 ms | 479 ms | 442 ms |
| 1,000 | 7,000 | 1.15 s | 637 ms | 4.98 s | 4.31 s |
| 2,000 | 14,000 | 2.25 s | 1.30 s | 9.82 s | 9.11 s |

最大メモリ（Mac）

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 5.0 MB | 23.5 MB | 14.0 MB | 42.3 MB |
| 100 | 700 | 13.0 MB | 27.8 MB | 105.4 MB | 409.6 MB |
| 1,000 | 7,000 | 14.8 MB | 33.4 MB | 1.02 GB | - |
| 2,000 | 14,000 | 16.3 MB | 36.7 MB | 2.03 GB | - |

最大メモリ（Linux）

| ファイル数 | ページ数 | nori | nori -j8 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 7.1 MB | 24.3 MB | 23.8 MB | 40.1 MB |
| 100 | 700 | 7.6 MB | 32.9 MB | 126.6 MB | 369.8 MB |
| 1,000 | 7,000 | 9.0 MB | 40.5 MB | 1.16 GB | 3.67 GB |
| 2,000 | 14,000 | 9.7 MB | 42.6 MB | 2.30 GB | 7.35 GB |

出力サイズ

| ファイル数 | ページ数 | nori | qpdf | lopdf |
|---:|---:|---:|---:|---:|
| 10 | 70 | 4.9 MB | 4.9 MB | 5.4 MB |
| 100 | 700 | 49.2 MB | 49.2 MB | 54.1 MB |
| 1,000 | 7,000 | 492.0 MB | 492.0 MB | 542.7 MB |
| 2,000 | 14,000 | 984.2 MB | 984.3 MB | 1.09 GB |

#### 新聞のスキャン（1 ページ、9 オブジェクト、610 KB）

実行時間（Mac）

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 21 ms | 19 ms | 31 ms | 26 ms |
| 100 | 100 | 70 ms | 61 ms | 104 ms | 133 ms |
| 1,000 | 1,000 | 715 ms | 661 ms | 1.16 s | 1.62 s |
| 2,000 | 2,000 | 1.53 s | 1.41 s | 2.60 s | - |

実行時間（Linux）

| ファイル数 | ページ数 | nori | nori -j8 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 9 ms | 8 ms | 18 ms | 12 ms |
| 100 | 100 | 63 ms | 24 ms | 83 ms | 83 ms |
| 1,000 | 1,000 | 671 ms | 197 ms | 813 ms | 853 ms |
| 2,000 | 2,000 | 1.37 s | 387 ms | 1.62 s | 1.80 s |

最大メモリ（Mac）

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 3.6 MB | 11.4 MB | 4.9 MB | 14.0 MB |
| 100 | 100 | 3.9 MB | 10.4 MB | 7.9 MB | 128.0 MB |
| 1,000 | 1,000 | 4.6 MB | 11.7 MB | 30.6 MB | 1.26 GB |
| 2,000 | 2,000 | 5.4 MB | 11.8 MB | 56.7 MB | - |

最大メモリ（Linux）

| ファイル数 | ページ数 | nori | nori -j8 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 5.9 MB | 12.8 MB | 12.7 MB | 16.1 MB |
| 100 | 100 | 5.9 MB | 20.9 MB | 15.7 MB | 128.9 MB |
| 1,000 | 1,000 | 6.3 MB | 27.6 MB | 41.2 MB | 1.38 GB |
| 2,000 | 2,000 | 6.9 MB | 29.2 MB | 69.8 MB | 2.57 GB |

出力サイズ

| ファイル数 | ページ数 | nori | qpdf | lopdf |
|---:|---:|---:|---:|---:|
| 10 | 10 | 6.1 MB | 6.1 MB | 6.1 MB |
| 100 | 100 | 61.1 MB | 61.1 MB | 61.1 MB |
| 1,000 | 1,000 | 610.7 MB | 610.8 MB | 610.9 MB |
| 2,000 | 2,000 | 1.22 GB | 1.22 GB | 1.22 GB |

### 読み取れること

- 日本語の帳票に近い PDF で、速さもメモリも桁が違います。法律案の条文を 2,000 ファイル（28,000 ページ）つなぐと、Mac では nori が 1.28 秒・8 MB、qpdf が 7.5 秒・686 MB、lopdf が 7.5 秒・1.5 GB でした。Linux では nori 0.50 秒・6.6 MB、qpdf 4.2 秒・768 MB、lopdf 3.5 秒・1.4 GB です。nori のメモリは 10 ファイルのとき（Mac 2.8 MB、Linux 5.0 MB）からほとんど増えていません
- 作り手の違う PDF でも傾向は同じです。英国の法令（Ghostscript 製）では nori が qpdf の 5.2 倍（Linux では 8.7 倍）速く、EU 官報（PDFlib 製、1 ファイル 478 オブジェクト）では 2.9 倍（4.4 倍）、`-j6`・`-j8` なら 4.5 倍（7.6 倍）です。メモリは 2,000 ファイルで nori 6〜16 MB、qpdf 423 MB〜2.3 GB でした
- スキャンした画像の PDF では、時間の差は縮まります。新聞は 1 ページ 9 オブジェクトしかなく、処理の大半が画像データの書き写しです。2,000 ファイル（1.2 GB）で Mac では nori 1.53 秒、qpdf 2.60 秒と差は 1.7 倍、Linux では 1.37 秒と 1.62 秒で 1.2 倍です。メモリは nori 5〜7 MB、qpdf 57〜70 MB で、lopdf は Linux の 2,000 ファイルで 2.6 GB でした（Mac では 1,000 ファイルの 1.3 GB で打ち切り）
- 件数が少ないと差は小さくなります。日本語 20 件や全体 40 件を 1 回つなぐだけなら、nori は qpdf の 2〜16 倍（Linux では 2〜18 倍）速いものの、メモリは入力 1 つ分がそのまま出るので qpdf と同程度です
- 2 台で傾向は同じです。Ryzen 7 の Linux はどのツールも Mac より速く、nori と qpdf の差はオブジェクトの多い PDF では Linux の方が開き、画像のスキャンでは縮まります。メモリの伸び方は 2 台でほぼ同じです
- lopdf が遅いのではなく、結合コードの作りの問題です。nori 自身も入力の解析には lopdf を使っています。README の結合コードは全入力を 1 つの `Document` に集めて最後に保存するため、メモリが入力の合計に比例します。ページから参照されないオブジェクトも出力に残すので、出力が少し大きくなります
- 出力はどのツールもほぼ同じ大きさで、すべて `qpdf --check` を通り、ページ数も一致しています

## インストール

### ソースからビルド

```bash
cargo install --git https://github.com/champierre/nori
```

Rust 1.88 以降が必要です。実行ファイルは `nori` の 1 つだけで、qpdf などの外部コマンドには依存しません。

## CLI

```
nori -o <出力> [-j <N>] [--list <ファイル>] <入力>...
```

| オプション | 意味 |
|---|---|
| `-o`, `--output <FILE>` | 出力先。既にあれば上書きします。入力と同じファイルは指定できません |
| `--list <FILE>` | 入力の一覧を 1 行 1 パスで書いたファイル。引数で渡した入力のあとに続けます。`-` で標準入力から読みます |
| `-j`, `--jobs <N>` | 同時に解析する入力の数（既定 1）。オブジェクトの多い入力ではコア数に近い倍率で速くなり、代わりに最大で N の 2 倍ほどの入力をメモリに持ちます |

入力は引数の順（`--list` の中は行の順）につながります。シェルの引数の上限に当たる数の入力は `--list` で渡してください。

### 終了コード

| コード | 意味 |
|---:|---|
| 0 | 成功 |
| 1 | 入力が読めない、ページが無い、書き込めないなど。理由を標準エラー出力に `nori: ...` で出し、出力ファイルは残しません |
| 2 | 引数の誤り |

入力が 1 つでも壊れていれば全体を失敗にします。ページの無い PDF も失敗です。

## Rust API

```rust
let inputs = ["a.pdf", "b.pdf"];
let summary = nori::merge(&inputs, std::path::Path::new("merged.pdf"), 1)?;
println!("{} pages from {} files", summary.pages, summary.inputs);
```

`nori::merge_into` は `std::io::Write` に書きます。3 つ目の引数は CLI の `-j` と同じです。

## Rails からの利用

qpdf と同じく外部コマンドとして呼べます。入力をファイルに置き、パスを引数で渡します。

```ruby
Dir.mktmpdir do |dir|
  inputs = pdfs.each_with_index.map do |pdf, i|
    File.join(dir, "#{i}.pdf").tap { |path| File.binwrite(path, pdf) }
  end
  output = File.join(dir, "merged.pdf")
  _out, err, status = Open3.capture3("nori", "-o", output, *inputs)
  raise "PDF の結合に失敗しました: #{err}" unless status.success?
  File.binread(output)
end
```

## 出力の形

- ページは入力の順に並びます。各ページが参照するもの（コンテンツストリーム、リソース、フォント、画像、注釈など）は、参照をたどって届く範囲だけをコピーします
- ページツリーの途中で指定されていた `MediaBox`・`CropBox`・`Resources`・`Rotate` は、各ページに書き込んでから出力します。出力のページツリーは入力のものとは別に作るためです
- ストリームの中身は入力のまま書きます。展開も再圧縮もしません
- ページツリーは、256 ページごとの中間ノードを根の下に並べた 2 段にします
- 出力はオブジェクトストリームを使わない、PDF 1.4 相当の素直な形です。ヘッダーのバージョンは最初の入力に合わせ、より新しい入力があればカタログの `/Version` で示します
- 存在しないオブジェクトへの参照は `null` に置き換えます

## 制限事項

- コピーするのはページと、ページから参照できるものだけです。しおり（Outlines）、フォーム（AcroForm）、名前付き宛先、構造ツリー（タグ付き PDF）、文書情報、XMP メタデータは引き継ぎません。注釈の `/P` のようにページを指す参照は、出力のページに付け替えます
- 暗号化された PDF は、lopdf が復号できるもの以外は読めません
- 入力の解析は lopdf に任せているため、lopdf が読めない PDF は読めません

## 比較方法

`bench/bench.py` が各ツールをコマンドとして実行し、`/usr/bin/time` で実行時間と最大 RSS を取ります。出力は qpdf でページ数と `--check` を確かめています。計測は 2 種類です。

- `--fixture`: 1 つの PDF を 10〜2,000 個コピーしてつなぎ、ファイル数に対する伸び方を見る
- `--corpus`: ディレクトリにある PDF を全部まとめて 1 回つなぎ、作り手のばらばらな実在の PDF を取りこぼさないかを見る

入力は Wikimedia Commons からランダムに選んだ PDF です。`bench/fetch.py select` が CirrusSearch の `srsort=random` で PDF を引き、3 MB・60 ページ以下のものを選んで、題名・URL・ライセンスを JSON に書き出します。`bench/fetch.py fetch` がその一覧を `bench/inputs/` にダウンロードします（PDF 自体はリポジトリに入れません）。一覧は 2 つあります。

- `bench/public-pdfs-ja.json`: 「Japanese-language PDF files」カテゴリから 20 件。先頭の 1 件（内閣官房の法律案の新旧対照条文）は `--include` で固定し、伸び方の計測に使います
- `bench/public-pdfs.json`: Commons 全体から 40 件。伸び方の計測には、この中から作りの違う 3 件を選びました

```bash
cargo build --release --workspace
python3 bench/fetch.py fetch --name ja
python3 bench/fetch.py fetch
python3 bench/bench.py --corpus bench/inputs/ja
python3 bench/bench.py --fixture bench/inputs/ja/ja-01.pdf
python3 bench/bench.py --corpus bench/inputs/public
python3 bench/bench.py --fixture bench/inputs/public/public-17.pdf
python3 bench/bench.py --fixture bench/inputs/public/public-13.pdf --max-count lopdf=100
python3 bench/bench.py --fixture bench/inputs/public/public-24.pdf --max-count lopdf=1000
```

- qpdf は `qpdf --warning-exit-0 --empty --pages <入力>... -- <出力>` で呼びます
- lopdf は `bench/lopdf-merge/` にある、lopdf の README の結合コードをそのまま実行ファイルにしたものです。全入力を読み込んで 1 つの `Document` に集め、最後に保存します
- nori は入力の解析に lopdf を使っています。lopdf が遅い・メモリを食うのではなく、README の結合コードが全入力をメモリに持ったまま最後に書く作りだから、入力の合計に比例してメモリが増えます。nori は 1 ファイルずつ書き出すので、入力の数に関係なく一定です
- `--max-count` は、そのツールのメモリが計測機に収まらなくなる手前で打ち切る指定です。Mac（16 GB）では lopdf を上の通り打ち切り、Linux（32 GB）では打ち切らず `--jobs 8` で全部測りました
- 結果は `bench/results-macos.json` と `bench/results-linux.json` に残り、`docs/build.py` がその両方からランディングページを作ります

## テスト

```bash
cargo test
```

qpdf があれば、出力の `qpdf --check` も通します。無ければその確認だけ飛ばします。

## ライセンス

MIT
