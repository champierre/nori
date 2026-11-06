# nori

[English](README.en.md) | 日本語

複数の PDF を 1 つにつなぐ Rust 製の CLI 兼ライブラリです。「糊」の nori。

入力を 1 ファイルずつ読み、そのページが参照するオブジェクトだけを新しい番号で出力に書き出してから、次のファイルを開きます。全部の入力を読み込んでから書くのではないので、メモリ使用量は入力の数に関係なく、いちばん大きい入力 1 つ分にとどまります。宛先ごとに作った帳票 PDF を数千件つないで 1 つの印刷用 PDF にする、といった用途のために作りました。

```bash
nori -o merged.pdf a.pdf b.pdf c.pdf
```

## qpdf と lopdf との比較

同じ 14 ページの PDF を 10〜2,000 個コピーしてつなぎ、[qpdf](https://qpdf.sourceforge.io/) と、[lopdf](https://github.com/J-F-Liu/lopdf) の README にある結合コードとで、実行時間・メモリ使用量・出力サイズを比べました。計測の手順は「[比較方法](#比較方法)」にあります。

<!-- BENCH -->

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

`bench/bench.py` が、`bench/fixtures/` の PDF をファイル数ぶんコピーして各ツールに渡し、`/usr/bin/time` で実行時間と最大 RSS を取ります。出力は qpdf でページ数と `--check` を確かめています。

```bash
cargo build --release --workspace
python3 bench/bench.py --counts 10,100,1000,2000 --runs 5 --max-count lopdf=100
```

- qpdf は `qpdf --warning-exit-0 --empty --pages <入力>... -- <出力>` で呼びます
- lopdf は `bench/lopdf-merge/` にある、lopdf の README の結合コードをそのまま実行ファイルにしたものです。全入力を読み込んで 1 つの `Document` に集め、最後に保存します
- nori は入力の解析に lopdf を使っています。lopdf が遅い・メモリを食うのではなく、README の結合コードが全入力をメモリに持ったまま最後に書く作りだから、入力の合計に比例してメモリが増えます。nori は 1 ファイルずつ書き出すので、入力の数に関係なく一定です

計測用の PDF は、同じ HTML を LibreOffice と Google Chrome で PDF にしたものです（`bench/fixtures/make_fixtures.py`）。ページ数は同じ 14 ページでも、作りがまったく違います。

| | LibreOffice | Chrome |
|---|---:|---:|
| オブジェクト数 | 58 | 3,002 |
| フォント | サブセットを埋め込み | Type3（グリフを個別のストリームで持つ） |
| サイズ | 73 KB | 670 KB |

## テスト

```bash
cargo test
```

qpdf があれば、出力の `qpdf --check` も通します。無ければその確認だけ飛ばします。

## ライセンス

MIT
