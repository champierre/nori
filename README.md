# nori

[English](README.en.md) | 日本語

複数の PDF を 1 つにつなぐ Rust 製の CLI 兼ライブラリです。「糊」の nori。

入力を 1 ファイルずつ読み、そのページが参照するオブジェクトだけを新しい番号で出力に書き出してから、次のファイルを開きます。全部の入力を読み込んでから書くのではないので、メモリ使用量は入力の数に関係なく、いちばん大きい入力 1 つ分にとどまります。宛先ごとに作った帳票 PDF を数千件つないで 1 つの印刷用 PDF にする、といった用途のために作りました。

```bash
nori -o merged.pdf a.pdf b.pdf c.pdf
```

## qpdf と lopdf との比較

Wikimedia Commons からランダムに選んだ PDF をつなぎ、[qpdf](https://qpdf.sourceforge.io/) と、[lopdf](https://github.com/J-F-Liu/lopdf) の README にある結合コードとで、実行時間・メモリ使用量・出力サイズを比べました。計測の手順と入力の選び方は「[比較方法](#比較方法)」にあります。

計測環境は Mac（Intel Core i5-8500B 6 コア、メモリ 16 GB、macOS 15.8）、qpdf 12.4.2、lopdf 0.47.0、nori 0.1.0 です。値は 5 回の中央値、メモリは最大 RSS です。`nori -j6` は 6 スレッドで解析を先行させた場合です。`-` は、その先を測るとメモリがマシンに収まらないため打ち切った箇所です。

### ばらばらな 40 件を 1 回でつなぐ

ランダムに選んだ 40 件（277 ページ、合計 33.8 MB。官報、法令、新聞やノートのスキャン、Internet Archive の書籍など）を名前の順に 1 回でつなぎました。4 ツールとも 277 ページの出力を作り、qpdf の検査も通っています。一覧は `bench/public-pdfs.json` にあります。

| | nori | nori -j6 | qpdf | lopdf |
|---|---:|---:|---:|---:|
| 実行時間 | 88 ms | 53 ms | 1.43 s | 170 ms |
| 最大メモリ | 21.3 MB | 36.8 MB | 30.3 MB | 111.2 MB |
| 出力サイズ | 32.0 MB | 32.0 MB | 31.9 MB | 33.7 MB |

### 1 つの PDF を 10〜2,000 個つなぐ

40 件の中から、作りの違う 3 件を選んでコピーしました。

| PDF | どんな PDF か | ページ | オブジェクト | サイズ |
|---|---|---:|---:|---:|
| [英国の法令](https://commons.wikimedia.org/wiki/File:The_Organic_Products_(Amendment)_Regulations_2015_(UKSI_2015-1669_qp).pdf) | Ghostscript で作られた、文字だけの軽い PDF | 4 | 36 | 40 KB |
| [EU 官報](https://commons.wikimedia.org/wiki/File:OJ_C_202301032_of_2023_-_SK_Slovak.pdf) | PDFlib で作られた、1 ページあたりのオブジェクトが多い PDF | 7 | 478 | 540 KB |
| [新聞のスキャン](https://commons.wikimedia.org/wiki/File:The_New_Orleans_Bee_1900_October_0074.pdf) | 1900 年の新聞の 1 面。1 ページがまるごと画像 | 1 | 9 | 610 KB |

#### 英国の法令（4 ページ、36 オブジェクト、40 KB）

Time

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 17 ms | 16 ms | 44 ms | 29 ms |
| 100 | 400 | 59 ms | 41 ms | 203 ms | 109 ms |
| 1,000 | 4,000 | 522 ms | 360 ms | 3.28 s | 1.49 s |
| 2,000 | 8,000 | 1.12 s | 626 ms | 5.86 s | 3.61 s |

最大メモリ

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 1.8 MB | 3.6 MB | 5.4 MB | 4.5 MB |
| 100 | 400 | 2.8 MB | 5.4 MB | 24.7 MB | 35.2 MB |
| 1,000 | 4,000 | 4.6 MB | 7.5 MB | 212.8 MB | 349.7 MB |
| 2,000 | 8,000 | 5.7 MB | 8.5 MB | 422.5 MB | 694.7 MB |

出力サイズ

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 40 | 0.4 MB | 0.4 MB | 0.4 MB | 0.4 MB |
| 100 | 400 | 3.8 MB | 3.8 MB | 3.8 MB | 3.8 MB |
| 1,000 | 4,000 | 38.4 MB | 38.4 MB | 38.4 MB | 38.2 MB |
| 2,000 | 8,000 | 76.8 MB | 76.8 MB | 76.8 MB | 76.3 MB |

#### EU 官報（7 ページ、478 オブジェクト、540 KB）

Time

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 46 ms | 33 ms | 93 ms | 95 ms |
| 100 | 700 | 343 ms | 189 ms | 778 ms | 925 ms |
| 1,000 | 7,000 | 3.46 s | 2.03 s | 8.59 s | - |
| 2,000 | 14,000 | 6.14 s | 3.96 s | 17.95 s | - |

最大メモリ

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 5.0 MB | 23.5 MB | 14.0 MB | 42.3 MB |
| 100 | 700 | 13.0 MB | 27.8 MB | 105.4 MB | 409.6 MB |
| 1,000 | 7,000 | 14.8 MB | 33.4 MB | 1.02 GB | - |
| 2,000 | 14,000 | 16.3 MB | 36.7 MB | 2.03 GB | - |

出力サイズ

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 70 | 4.9 MB | 4.9 MB | 4.9 MB | 5.4 MB |
| 100 | 700 | 49.2 MB | 49.2 MB | 49.2 MB | 54.1 MB |
| 1,000 | 7,000 | 492.0 MB | 492.0 MB | 492.0 MB | - |
| 2,000 | 14,000 | 984.2 MB | 984.2 MB | 984.3 MB | - |

#### 新聞のスキャン（1 ページ、9 オブジェクト、610 KB）

Time

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 21 ms | 19 ms | 31 ms | 26 ms |
| 100 | 100 | 70 ms | 61 ms | 104 ms | 133 ms |
| 1,000 | 1,000 | 715 ms | 661 ms | 1.16 s | 1.62 s |
| 2,000 | 2,000 | 1.53 s | 1.41 s | 2.60 s | - |

最大メモリ

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 3.6 MB | 11.4 MB | 4.9 MB | 14.0 MB |
| 100 | 100 | 3.9 MB | 10.4 MB | 7.9 MB | 128.0 MB |
| 1,000 | 1,000 | 4.6 MB | 11.7 MB | 30.6 MB | 1.26 GB |
| 2,000 | 2,000 | 5.4 MB | 11.8 MB | 56.7 MB | - |

出力サイズ

| ファイル数 | ページ数 | nori | nori -j6 | qpdf | lopdf |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 6.1 MB | 6.1 MB | 6.1 MB | 6.1 MB |
| 100 | 100 | 61.1 MB | 61.1 MB | 61.1 MB | 61.1 MB |
| 1,000 | 1,000 | 610.7 MB | 610.7 MB | 610.8 MB | 610.9 MB |
| 2,000 | 2,000 | 1.22 GB | 1.22 GB | 1.22 GB | - |

### 読み取れること

- オブジェクトの少ない PDF では、速さもメモリも桁が違います。法令を 2,000 ファイル（8,000 ページ）つなぐと、nori が 1.12 秒・5.7 MB、qpdf が 5.9 秒・423 MB、lopdf が 3.6 秒・695 MB でした。nori のメモリは 10 ファイルの 1.8 MB からほとんど増えていません
- オブジェクトの多い PDF でも、メモリは一定のままです。EU 官報は 1 ファイル 478 オブジェクトあり解析に時間がかかりますが、それでも nori は qpdf の 2.9 倍速く、`-j6` なら 4.5 倍です。メモリは 2,000 ファイルで nori 16 MB、qpdf 2 GB でした
- スキャンした画像の PDF では、時間の差は縮まります。新聞は 1 ページ 9 オブジェクトしかなく、処理の大半が画像データの書き写しです。2,000 ファイル（1.2 GB）で nori 1.53 秒、qpdf 2.60 秒と差は 1.7 倍ですが、メモリは nori 5.4 MB、qpdf 57 MB、lopdf は 1,000 ファイルで 1.3 GB でした
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

入力は Wikimedia Commons からランダムに選んだ PDF です。`bench/fetch.py select` が CirrusSearch の `srsort=random` で PDF を引き、3 MB・60 ページ以下のものを 40 件選んで `bench/public-pdfs.json` に題名・URL・ライセンスを書き出します。`bench/fetch.py fetch` がその一覧を `bench/inputs/public/` にダウンロードします（PDF 自体はリポジトリに入れません）。伸び方の計測には、その 40 件の中から作りの違う 3 件を選びました。

```bash
cargo build --release --workspace
python3 bench/fetch.py fetch
python3 bench/bench.py --corpus bench/inputs/public
python3 bench/bench.py --fixture bench/inputs/public/public-17.pdf
python3 bench/bench.py --fixture bench/inputs/public/public-13.pdf --max-count lopdf=100
python3 bench/bench.py --fixture bench/inputs/public/public-24.pdf --max-count lopdf=1000
```

- qpdf は `qpdf --warning-exit-0 --empty --pages <入力>... -- <出力>` で呼びます
- lopdf は `bench/lopdf-merge/` にある、lopdf の README の結合コードをそのまま実行ファイルにしたものです。全入力を読み込んで 1 つの `Document` に集め、最後に保存します
- nori は入力の解析に lopdf を使っています。lopdf が遅い・メモリを食うのではなく、README の結合コードが全入力をメモリに持ったまま最後に書く作りだから、入力の合計に比例してメモリが増えます。nori は 1 ファイルずつ書き出すので、入力の数に関係なく一定です
- `--max-count` は、そのツールのメモリが計測機（16 GB）に収まらなくなる手前で打ち切る指定です

## テスト

```bash
cargo test
```

qpdf があれば、出力の `qpdf --check` も通します。無ければその確認だけ飛ばします。

## ライセンス

MIT
