#!/usr/bin/env python3
"""Builds the landing page (docs/index.html and docs/en/index.html) from bench/results-*.json.

The numbers on the page come from the benchmark results, one file per machine, so re-run this
after bench.py. Standard library only.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
# Order on the page; the first machine is the one shown until a button is pressed.
MACHINES = ["macos", "linux"]
RESULTS = {m: HERE.parent / "bench" / f"results-{m}.json" for m in MACHINES}
# Order on the page, per language; each is a file fetch.py downloads from Wikimedia Commons.
# The Japanese page leads with the Japanese government PDF, the English page with the others.
FIXTURES = {
    "ja": ["ja-01.pdf", "public-17.pdf", "public-13.pdf", "public-24.pdf"],
    "en": ["public-17.pdf", "public-13.pdf", "public-24.pdf", "ja-01.pdf"],
}
CORPORA = {"ja": ["ja", "public"], "en": ["public", "ja"]}

T = {
    "ja": {
        "lang": "ja", "dir": "", "alt_href": "en/", "alt_label": "English", "alt_lang": "en",
        "title": "nori | 何千枚の PDF を、一枚に貼り合わせる",
        "description": "nori は複数の PDF を 1 つにつなぐ Rust 製のコマンドです。入力を 1 枚ずつ読んで貼り足すので、メモリ使用量は入力の数に関係なく一定。2,000 ファイルでも 6 MB。qpdf より速く動きます。MIT ライセンス。",
        "nav": [("#top", "nori とは"), ("#how", "しくみ"), ("#benchmark", "qpdf・lopdf との比較"), ("#install", "インストール"), ("#usage", "使い方")],
        "install_button": "インストール", "github_button": "GitHub でソースを見る",
        "chart_title": "最大メモリ使用量",
        "chart_lede": "14 ページの PDF を 10〜2,000 個つないだときの最大 RSS。横軸はファイル数です。",
        "fixture_label": {"ja-01.pdf": "法律案の新旧対照条文", "public-17.pdf": "英国の法令", "public-13.pdf": "EU 官報", "public-24.pdf": "新聞のスキャン"},
        "fixture_short": {"ja-01.pdf": "日本の法律案", "public-17.pdf": "英国の法令", "public-13.pdf": "EU 官報", "public-24.pdf": "新聞"},
        "fixture_desc": {
            "ja-01.pdf": "スマートフォンにおいて利用される特定ソフトウェアに係る競争の促進に関する法律案の新旧対照条文（内閣官房）。日本語フォントを埋め込んだ、表組みの電子生成 PDF",
            "public-17.pdf": "The Organic Products (Amendment) Regulations 2015。Ghostscript で作られた、文字だけの軽い PDF",
            "public-13.pdf": "Official Journal C 2023/1032（スロバキア語版）。PDFlib で作られた、1 ページあたりのオブジェクトが多い PDF",
            "public-24.pdf": "The New Orleans Bee、1900 年 10 月の 1 面。1 ページがまるごと画像のスキャン",
        },
        "chart_caption": {
            "ja-01.pdf": "ＭＳ明朝のサブセットを埋め込んだ、JUST PDF 製の条文の表。qpdf と lopdf は入力の数に比例して増え、nori は {count} ファイル（{pages} ページ）でも {nori} です。",
            "public-17.pdf": "文字だけの軽い PDF。qpdf と lopdf は入力の数に比例して増え、nori は {count} ファイル（{pages} ページ）でも {nori} です。",
            "public-13.pdf": "1 ページあたりのオブジェクトが多い PDF。{count} ファイルで qpdf は {qpdf}、{lopdf_last} に達し、nori は {nori} です。",
            "public-24.pdf": "1 ページが画像のスキャン。オブジェクトが少ないぶん qpdf のメモリも伸びにくいものの、{count} ファイルで nori {nori} に対して qpdf は {qpdf}、{lopdf_last} でした。",
        },
        "lopdf_last": "lopdf は {value}", "lopdf_cut": "lopdf は {count} ファイルで {value}",
        "machine_label": {"macos": "Mac（Intel Core i5-8500B 6 コア、メモリ 16 GB、macOS 15.8）", "linux": "Linux（AMD Ryzen 7 6800H 8 コア、GEEKOM A6、メモリ 32 GB、Omarchy 4.0.6）"},
        "machine_short": {"macos": "Mac（Core i5）", "linux": "Linux（Ryzen 7）"},
        "aria_machine": "計測したマシン",
        "fixture_col": "PDF", "fixture_desc_col": "どんな PDF か", "pages_col": "ページ", "objects_col": "オブジェクト", "size_col": "サイズ",
        "objects": "オブジェクト", "output_title": "出力サイズ",
        "corpus_title": {"ja": "日本語の PDF をまとめてつなぐ", "public": "世界中のばらばらな PDF をまとめてつなぐ"},
        "corpus_lede": {
            "ja": "Wikimedia Commons の日本語 PDF のカテゴリからランダムに選んだ {files} 件（{pages} ページ、合計 {size}）を、名前の順に 1 回でつなぎました。官庁の資料、法令、通知のスキャン、楽譜、Google ドキュメントの書き出しなど、作り手はさまざまです。",
            "public": "Commons 全体からランダムに選んだ {files} 件（{pages} ページ、合計 {size}）を、名前の順に 1 回でつなぎました。EU 官報、英国の法令、19 世紀の新聞やノートのスキャン、Internet Archive の書籍など、言語も年代もばらばらです。",
        },
        "corpus_note": {
            "ja": "4 ツールとも {pages} ページの出力を作り、qpdf の検査も通りました。nori は {nori_time} と qpdf の {vs_qpdf}速く、メモリ {nori_mem} はいちばん大きい入力（{largest} のスキャン）を読むぶんが主です。件数が 20 と少ないので、qpdf との差は伸び方の計測ほど開いていません。",
            "public": "4 ツールとも {pages} ページの出力を作り、qpdf の検査も通りました。nori は {nori_time} と、qpdf の {vs_qpdf}速く、lopdf の {vs_lopdf}速い結果です。メモリは {nori_mem} で、いちばん大きい入力（{largest}）を読むぶんが主です。",
        },
        "corpus_files": "つないだ PDF の一覧",
        "not_measured": "計測せず",
        "how_title": "読んだそばから書き、捨てる",
        "how_p1": "PDF の結合ツールの多くは、まず全部の入力を読み込み、1 つの文書にまとめてから、最後に書き出します。扱いやすい作りですが、メモリは入力の合計に比例して増えます。qpdf も、lopdf の README にある結合コードも、この形です。",
        "how_p2": "nori は入力を 1 つ読むたびに、そのページと、ページが参照するもの（コンテンツストリーム、フォント、画像、注釈）だけを新しい番号で出力に書き足し、その入力を捨ててから次を開きます。ページツリーと相互参照表は最後に書きます。だから、メモリに載るのはいつも入力 1 つ分と、出力したオブジェクトの位置だけです。",
        "flow_all_title": "全部読んでから書く", "flow_all_memory": "メモリは入力の合計",
        "flow_all": ["入力を全部読む", "1 つの文書にまとめる", "書き出す"],
        "flow_nori_title": "nori", "flow_nori_memory": "メモリは入力 1 つ分",
        "flow_nori": ["1 つ読む", "ページに要るものを書く", "捨てて次へ"],
        "how_points": [
            ("ストリームには触りません", "フォントや画像の中身は、展開も再圧縮もせず入力のまま書きます。速く、出力は qpdf とほぼ同じ大きさです。"),
            ("ページに要るものだけ", "しおりやフォーム、タグ付き PDF の構造ツリーは引き継ぎません。ページから参照をたどって届くものだけをコピーします。"),
            ("解析は先読みできます", "<code>-j 6</code> のように指定すると、6 つの入力を別スレッドで同時に解析します。オブジェクトの多い入力では時間が半分になり、メモリは解析中の入力の分だけ増えます。"),
        ],
        "bench_title": "qpdf と lopdf との比較",
        "bench_p1": "Wikimedia Commons にある PDF を 10〜2,000 個コピーしてつなぎ、qpdf と、lopdf の README にある結合コードとで、実行時間と最大メモリを比べました。いずれもコマンドとして実行した 5 回の中央値で、Mac（Intel Core i5）と Linux（AMD Ryzen 7）の 2 台で測りました。グラフの上のボタンで、マシンと入力の PDF を切り替えられます。",
        "bench_p2": "コピー元は、日本語 PDF のカテゴリから選んだ内閣官房の法律案の条文と、Commons 全体からランダムに取った 40 件の中から作りの違う 3 件です。どれもパブリックドメインか自由なライセンスで、リンク先からそのまま取得できます。",
        "time_title": "実行時間", "memory_title": "最大メモリ使用量",
        "bench_lede_time": "棒の長さは、ファイル数ごとにいちばん時間のかかったツールを基準にしています。右の数字は、nori が qpdf の何倍速かったか。",
        "bench_lede_memory": "棒の長さは、ファイル数ごとにいちばんメモリを使ったツールを基準にしています。右の数字は、nori のメモリが qpdf の何分の一か。",
        "files": "ファイル", "pages": "ページ",
        "ratio_time": "倍", "ratio_time_small": "qpdf 比", "ratio_memory_small": "qpdf 比",
        "ratio_none": "qpdf は計測せず",
        "notes": [
            ("日本語の帳票に近い PDF で、速さもメモリも桁が違います", "内閣官房の法律案の条文（JUST PDF 製、ＭＳ明朝のサブセット埋め込み、14 ページ）を 2,000 ファイル（28,000 ページ）つなぐと、Mac では nori が 1.28 秒・8 MB、qpdf が 7.5 秒・686 MB、lopdf が 7.5 秒・1.5 GB でした。Linux では nori 0.50 秒・6.6 MB、qpdf 4.2 秒・768 MB、lopdf 3.5 秒・1.4 GB です。nori のメモリは 10 ファイルのとき（Mac 2.8 MB、Linux 5.0 MB）からほとんど増えていません。"),
            ("作り手の違う PDF でも傾向は同じです", "英国の法令（Ghostscript 製）では nori が qpdf の 5.2 倍（Linux では 8.7 倍）速く、EU 官報（PDFlib 製、1 ファイル 478 オブジェクト）では 2.9 倍（4.4 倍）、解析を先読みさせれば 4.5 倍（7.6 倍）です。メモリは 2,000 ファイルで nori 6〜16 MB、qpdf 423 MB〜2.3 GB でした。"),
            ("スキャンした画像の PDF では、時間の差は縮まります", "新聞のスキャンは 1 ページ 9 オブジェクトしかなく、処理の大半が画像データの書き写しです。2,000 ファイル（1.2 GB）で Mac では nori 1.53 秒、qpdf 2.60 秒と差は 1.7 倍、Linux では 1.37 秒と 1.62 秒で 1.2 倍にとどまります。メモリは nori 5〜7 MB、qpdf 57〜70 MB で、lopdf は Linux の 2,000 ファイルで 2.6 GB でした（Mac では 1,000 ファイルの 1.3 GB で打ち切っています）。"),
            ("2 台で傾向は同じです", "Ryzen 7 の Linux はどのツールも Mac より速く、nori と qpdf の差は、オブジェクトの多い PDF では Linux の方が開き、画像のスキャンでは縮まります。メモリの伸び方は 2 台でほぼ同じです。"),
            ("lopdf が遅いのではなく、結合コードの作りの問題です", "nori 自身も入力の解析には lopdf を使っています。README の結合コードは全入力を 1 つの <code>Document</code> に集めて最後に保存するため、メモリが入力の合計に比例します。ページから参照されないオブジェクトも出力に残すので、出力が少し大きくなります。"),
        ],
        "method_summary": "計測方法",
        "method_p1": "2 台で計測しました。Mac は Intel Core i5-8500B（6 コア、メモリ 16 GB、macOS 15.8）、Linux は AMD Ryzen 7 6800H（8 コア 16 スレッド、GEEKOM A6、メモリ 32 GB、Omarchy 4.0.6、Arch Linux ベース）です。どちらも nori 0.1.0、qpdf 12.4.2、lopdf 0.47.0 です。伸び方の計測では入力を指定した数だけコピーし、各ツールをコマンドとして 1 回ウォームアップしてから 5 回実行し、時間とメモリ（最大常駐メモリ）を <code>/usr/bin/time</code> で取得しています。出力は qpdf でページ数と <code>--check</code> を確かめました。入力の PDF は 2 台で同じものを使いましたが、数値は環境によって変わります。",
        "method_p2": "入力は Wikimedia Commons からランダムに選んだ PDF で、<code>bench/fetch.py</code> が一覧の作成と取得をします。lopdf は EU 官報で 100 ファイル、新聞のスキャンで 1,000 ファイルの時点でメモリが 400 MB〜1.3 GB に達したため、その先はこのマシンでは測っていません。計測スクリプトと入力の一覧は <a href=\"https://github.com/champierre/nori/tree/main/bench\" target=\"_blank\" rel=\"noopener\">bench/</a> にあります。",
        "scope_title": "コピーするもの、引き継がないもの",
        "scope_yes_title": "コピーするもの",
        "scope_yes": ["ページと、その順序", "コンテンツストリーム、リソース、フォント、画像", "注釈（ページを指す参照は出力のページに付け替えます）", "ページツリーの途中で指定された MediaBox・CropBox・Resources・Rotate（各ページに書き込みます）"],
        "scope_no_title": "引き継がないもの",
        "scope_no": ["しおり（Outlines）とフォーム（AcroForm）", "名前付き宛先、タグ付き PDF の構造ツリー", "文書情報と XMP メタデータ", "存在しないオブジェクトへの参照（null になります）"],
        "install_title": "インストール",
        "install_p": "Rust 1.88 以降の開発環境でソースからインストールします。できるのは <code>nori</code> という 1 つの実行ファイルで、qpdf などの外部コマンドには依存しません。",
        "usage_title": "使い方",
        "usage_p1": "出力先と入力を並べるだけです。ページは入力の順につながります。",
        "usage_p2": "入力が 1 つでも読めなければ全体を失敗にし、出力ファイルは残しません。理由は標準エラー出力に <code>nori: ...</code> で出ます。",
        "usage_p3": "オプションと終了コードの一覧は <code>nori --help</code> で確認できます。",
        "cli_title": "コマンドライン", "rails_title": "Rails から呼び出す",
        "cli_code": """<span class="comment"># 3 つの PDF を順につなぐ</span>
nori -o merged.pdf a.pdf b.pdf c.pdf

<span class="comment"># 入力の一覧をファイルから読む（1 行 1 パス。- で標準入力）</span>
ls pages/*.pdf | nori -o merged.pdf --list -

<span class="comment"># 6 つの入力を同時に解析する</span>
nori -j 6 -o merged.pdf --list inputs.txt""",
        "rails_code": """require "open3"

Dir.mktmpdir do |dir|
  inputs = pdfs.each_with_index.map do |pdf, i|
    File.join(dir, "#{i}.pdf").tap { |path| File.binwrite(path, pdf) }
  end
  output = File.join(dir, "merged.pdf")
  _out, err, status = Open3.capture3("nori", "-o", output, *inputs)
  raise "PDF の結合に失敗しました: #{err}" unless status.success?
  File.binread(output)
end""",
        "copy": "コピー", "copied": "コピーしました", "copy_failed": "コピーできませんでした",
        "footer_license": "MIT License", "footer_github": "GitHub",
        "aria_nav": "サイト内", "aria_fixture": "入力の PDF", "aria_fixture_time": "入力の PDF（実行時間）", "aria_fixture_memory": "入力の PDF（メモリ使用量）",
        "brand_aria": "nori トップ",
        "h1": ["何千枚の PDF を、", "一枚に貼り合わせる。"],
        "lede": "nori は複数の PDF を 1 つにつなぐコマンドです。入力を 1 枚ずつ読み、そのページに要るものだけを出力に貼り足してから、次の 1 枚を開きます。だから、メモリ使用量は入力の数に関係なく、いちばん大きい入力 1 つ分にとどまります。",
        "paste_memory": "メモリ", "paste_memory_value": "8.0 MB", "paste_memory_note": "2,000 枚でもこのまま",
        "paste_caption": "入力を 1 枚ずつ読み、要るものを書き足してから捨てる。だから貼る枚数が増えても、手元に持つのは 1 枚分。",
        "cards": [("8 MB", "日本語の法律案 PDF を 2,000 ファイル（28,000 ページ）つないだときの最大メモリ。qpdf は 686 MB（Mac）"), ("5.9 倍", "同じ結合で qpdf より速い（Linux では 8.3 倍）。-j6 なら 9.7 倍")],
        "chart_section_lede": "横軸はファイル数。nori の線は、入力が 200 倍になってもほとんど動きません。Mac で lopdf の線が途中で終わるのは、その先はメモリ 16 GB に収まらないためです。グラフの上のボタンで、計測した 2 台と入力の PDF を切り替えられます。",
    },
    "en": {
        "lang": "en", "dir": "en/", "alt_href": "../", "alt_label": "日本語", "alt_lang": "ja",
        "title": "nori | Thousands of PDFs, pasted into one",
        "description": "nori is a Rust command that merges PDF files into one. It reads inputs one at a time and pastes as it goes, so memory stays constant however many files you merge: 6 MB for 2,000 files. Faster than qpdf. MIT license.",
        "nav": [("#top", "About"), ("#how", "How it works"), ("#benchmark", "vs qpdf and lopdf"), ("#install", "Install"), ("#usage", "Usage")],
        "install_button": "Install", "github_button": "Source on GitHub",
        "chart_title": "Peak memory",
        "chart_lede": "Peak RSS when merging 10 to 2,000 copies of a 14-page PDF. The x axis is the number of files.",
        "fixture_label": {"public-17.pdf": "UK regulation", "public-13.pdf": "EU Official Journal", "public-24.pdf": "scanned newspaper", "ja-01.pdf": "Japanese bill"},
        "fixture_short": {"public-17.pdf": "Regulation", "public-13.pdf": "Journal", "public-24.pdf": "Newspaper", "ja-01.pdf": "Japanese bill"},
        "fixture_desc": {
            "ja-01.pdf": "Comparison table of a Japanese bill on smartphone software competition (Cabinet Secretariat). Born-digital tables with embedded Japanese fonts",
            "public-17.pdf": "The Organic Products (Amendment) Regulations 2015. Text only, made with Ghostscript; a light PDF",
            "public-13.pdf": "Official Journal C 2023/1032, Slovak edition. Made with PDFlib, with many objects per page",
            "public-24.pdf": "The New Orleans Bee, front page, October 1900. A scan: each page is one image",
        },
        "chart_caption": {
            "ja-01.pdf": "Tables of a bill, made with JUST PDF and carrying MS Mincho subsets. qpdf and lopdf grow with the number of inputs; nori is at {nori} for {count} files ({pages} pages).",
            "public-17.pdf": "A light, text-only PDF. qpdf and lopdf grow with the number of inputs; nori is at {nori} even for {count} files ({pages} pages).",
            "public-13.pdf": "A PDF with many objects per page. At {count} files qpdf reaches {qpdf} and {lopdf_last}; nori uses {nori}.",
            "public-24.pdf": "A scan with one image per page. With so few objects even qpdf's memory grows slowly, yet at {count} files nori used {nori} against qpdf's {qpdf}, and {lopdf_last}.",
        },
        "lopdf_last": "lopdf {value}", "lopdf_cut": "lopdf {value} at {count}",
        "machine_label": {"macos": "Mac (Intel Core i5-8500B, 6 cores, 16 GB, macOS 15.8)", "linux": "Linux (AMD Ryzen 7 6800H, 8 cores, GEEKOM A6, 32 GB, Omarchy 4.0.6)"},
        "machine_short": {"macos": "Mac (Core i5)", "linux": "Linux (Ryzen 7)"},
        "aria_machine": "Machine",
        "fixture_col": "PDF", "fixture_desc_col": "What it is", "pages_col": "Pages", "objects_col": "Objects", "size_col": "Size",
        "objects": "objects", "output_title": "Output size",
        "corpus_title": {"public": "PDFs of every make from all over Commons, merged once", "ja": "Japanese PDFs, merged once"},
        "corpus_lede": {
            "public": "{files} PDFs picked at random from all of Wikimedia Commons ({pages} pages, {size} in all) merged in one go, in name order: official journals, regulations, scanned newspapers and notebooks, Internet Archive books, from many producers, languages and decades.",
            "ja": "{files} PDFs picked at random from Commons\u2019 Japanese-language category ({pages} pages, {size} in all) merged in one go: government papers, laws, scanned notices, sheet music, Google Docs exports, from many producers.",
        },
        "corpus_note": {
            "public": "All four tools produced a {pages}-page output that passes qpdf's check. nori took {nori_time}, {vs_qpdf} faster than qpdf and {vs_lopdf} faster than lopdf, in {nori_mem} of memory, most of it for reading the largest input ({largest}).",
            "ja": "All four tools produced a {pages}-page output that passes qpdf's check. nori took {nori_time}, {vs_qpdf} faster than qpdf, in {nori_mem}, most of it for reading the largest input (a {largest} scan). With only 20 files the gap to qpdf is smaller than in the scaling runs.",
        },
        "corpus_files": "The PDFs that were merged",
        "not_measured": "not run",
        "how_title": "Write as you read, then let go",
        "how_p1": "Most PDF merge tools load every input first, gather them into one document, and write it out at the end. It is a convenient design, but memory grows with the total input. qpdf works this way, and so does the merge code in the lopdf README.",
        "how_p2": "nori reads one input, writes its pages and what they refer to (content streams, fonts, images, annotations) to the output under new object numbers, then drops that input before opening the next. The page tree and the cross-reference table are written last. What is in memory is always one input plus the position of every object written so far.",
        "flow_all_title": "Load everything, then write", "flow_all_memory": "memory grows with the total input",
        "flow_all": ["load all inputs", "gather into one document", "write"],
        "flow_nori_title": "nori", "flow_nori_memory": "memory is one input",
        "flow_nori": ["load one", "write what its pages need", "drop it, next"],
        "how_points": [
            ("Streams are left alone", "Font and image data is written exactly as read, neither decompressed nor recompressed. It is fast, and the output is about the same size as qpdf's."),
            ("Only what pages need", "Outlines, forms and the structure tree of tagged PDF are not carried over. Only what can be reached from a page by following references is copied."),
            ("Parsing can run ahead", "With <code>-j 6</code>, six inputs are parsed at once on separate threads. On inputs with many objects this halves the time; memory grows by the inputs being parsed."),
        ],
        "bench_title": "Compared with qpdf and lopdf",
        "bench_p1": "PDFs picked at random from Wikimedia Commons were copied 10 to 2,000 times and merged with nori, with qpdf, and with the merge code from the lopdf README. All were run as commands on two machines, a Mac (Intel Core i5) and a Linux box (AMD Ryzen 7); the values are the median of 5 runs. The buttons above each chart switch the machine and the input PDF.",
        "bench_p2": "Three were chosen from 40 random files for how differently they are built, plus a Japanese government bill from Commons\u2019 Japanese-language category. All are public domain or freely licensed and can be fetched from the links as they are.",
        "time_title": "Time", "memory_title": "Peak memory",
        "bench_lede_time": "Bars are relative to the slowest tool at each file count. The number on the right is how many times faster nori was than qpdf.",
        "bench_lede_memory": "Bars are relative to the tool using the most memory at each file count. The number on the right is nori's memory as a fraction of qpdf's.",
        "files": "files", "pages": "pages",
        "ratio_time": "×", "ratio_time_small": "vs qpdf", "ratio_memory_small": "of qpdf",
        "ratio_none": "qpdf not run",
        "notes": [
            ("With few objects per file, both speed and memory differ by orders of magnitude", "Merging 2,000 copies of the UK regulation (8,000 pages) took nori 1.12 s and 5.7 MB, qpdf 5.9 s and 423 MB, lopdf 3.6 s and 695 MB on the Mac. On Linux it was nori 0.28 s and 6.0 MB, qpdf 2.4 s and 477 MB, lopdf 1.2 s and 640 MB. nori's memory barely moved from what it used for 10 files (1.8 MB on the Mac, 4.0 MB on Linux)."),
            ("With many objects per file, memory still stays flat", "The EU journal has 478 objects per file and takes longer to parse. nori is still 2.9 times faster than qpdf (4.4 on Linux), 4.5 times with parsing run ahead (7.6). At 2,000 files nori used 10 to 16 MB and qpdf 2 to 2.3 GB; lopdf reached 7.4 GB on Linux."),
            ("With scanned images, the gap in time narrows", "The scanned newspaper has 9 objects per page, so merging is mostly copying image data. For 2,000 files (1.2 GB) nori took 1.53 s and qpdf 2.60 s on the Mac, 1.7 times apart, and 1.37 s against 1.62 s on Linux, 1.2 times. Memory was 5 to 7 MB for nori, 57 to 70 MB for qpdf, and 2.6 GB for lopdf at 2,000 files on Linux (the Mac stopped at 1.3 GB for 1,000)."),
            ("CJK documents behave the same", "The Japanese bill (made with JUST PDF, with MS Mincho subsets embedded, 14 pages) merged 2,000 times (28,000 pages) took nori 1.28 s and 8 MB, qpdf 7.5 s and 686 MB, lopdf 7.5 s and 1.5 GB on the Mac; on Linux nori 0.50 s and 6.6 MB, qpdf 4.2 s and 768 MB, lopdf 3.5 s and 1.4 GB."),
            ("Both machines show the same picture", "Every tool is faster on the Ryzen 7 Linux box than on the Mac. The gap between nori and qpdf is wider on Linux for PDFs with many objects and narrower for the scanned images. Memory grows the same way on both."),
            ("lopdf is not slow; the merge code is the problem", "nori itself parses inputs with lopdf. The README's merge code gathers every input into one <code>Document</code> and saves at the end, so memory grows with the total input. Objects no page refers to stay in the output, which makes it a little larger."),
        ],
        "method_summary": "How it was measured",
        "method_p1": "On two machines: a Mac with an Intel Core i5-8500B (6 cores, 16 GB, macOS 15.8) and a Linux box with an AMD Ryzen 7 6800H (8 cores, 16 threads, GEEKOM A6, 32 GB, Omarchy 4.0.6, based on Arch Linux). Both ran nori 0.1.0, qpdf 12.4.2 and lopdf 0.47.0. The input was copied the given number of times, each tool was run as a command once to warm up and then 5 times, and time and peak resident memory were taken from <code>/usr/bin/time</code>. Outputs were checked with qpdf for page count and with <code>--check</code>. The same input PDFs were used on both machines, but the numbers depend on the environment.",
        "method_p2": "The inputs are PDFs picked at random from Wikimedia Commons; <code>bench/fetch.py</code> builds the list and downloads them. lopdf reached 400 MB to 1.3 GB at 100 files of the journal and 1,000 of the newspaper, so larger counts were not run on this machine. The benchmark script and the list of inputs are in <a href=\"https://github.com/champierre/nori/tree/main/bench\" target=\"_blank\" rel=\"noopener\">bench/</a>.",
        "scope_title": "What is copied, what is not",
        "scope_yes_title": "Copied",
        "scope_yes": ["Pages, in input order", "Content streams, resources, fonts, images", "Annotations (references to pages are redirected to the output pages)", "MediaBox, CropBox, Resources and Rotate set higher in the page tree (written into each page)"],
        "scope_no_title": "Not carried over",
        "scope_no": ["Outlines (bookmarks) and AcroForm fields", "Named destinations, the structure tree of tagged PDF", "The document information dictionary and XMP metadata", "References to objects that do not exist (they become null)"],
        "install_title": "Install",
        "install_p": "Build from source with Rust 1.88 or later. The result is a single <code>nori</code> binary with no dependency on qpdf or other external commands.",
        "usage_title": "Usage",
        "usage_p1": "Give the output and the inputs. Pages come out in input order.",
        "usage_p2": "One unreadable input fails the whole merge and no output file is left behind. The reason goes to standard error as <code>nori: ...</code>.",
        "usage_p3": "<code>nori --help</code> lists the options and exit codes.",
        "cli_title": "Command line", "rails_title": "From Rails",
        "cli_code": """<span class="comment"># merge three PDFs in order</span>
nori -o merged.pdf a.pdf b.pdf c.pdf

<span class="comment"># read the input list from a file (one path per line; - is stdin)</span>
ls pages/*.pdf | nori -o merged.pdf --list -

<span class="comment"># parse six inputs at once</span>
nori -j 6 -o merged.pdf --list inputs.txt""",
        "rails_code": """require "open3"

Dir.mktmpdir do |dir|
  inputs = pdfs.each_with_index.map do |pdf, i|
    File.join(dir, "#{i}.pdf").tap { |path| File.binwrite(path, pdf) }
  end
  output = File.join(dir, "merged.pdf")
  _out, err, status = Open3.capture3("nori", "-o", output, *inputs)
  raise "PDF merge failed: #{err}" unless status.success?
  File.binread(output)
end""",
        "copy": "Copy", "copied": "Copied", "copy_failed": "Could not copy",
        "footer_license": "MIT License", "footer_github": "GitHub",
        "aria_nav": "Site", "aria_fixture": "Input PDF", "aria_fixture_time": "Input PDF (time)", "aria_fixture_memory": "Input PDF (memory)",
        "brand_aria": "nori home",
        "h1": ["Thousands of PDFs,", "pasted into one."],
        "lede": "nori merges PDF files into one. It reads one input, pastes what its pages need onto the output, and only then opens the next. Memory use therefore stays around the size of the largest single input, however many files you merge.",
        "paste_memory": "memory", "paste_memory_value": "5.7 MB", "paste_memory_note": "still this at 2,000 sheets",
        "paste_caption": "One sheet at a time: read it, paste what its pages need, let it go. However many sheets, only one is in hand.",
        "cards": [("6 MB", "peak memory for 2,000 files (5.4 to 16 MB across three kinds of PDF and two machines)"), ("16×", "faster than qpdf merging 40 random PDFs from Wikimedia Commons (18× on Linux)")],
        "chart_section_lede": "The x axis is the number of files. nori's line barely moves while the input grows 200-fold. On the Mac, lopdf's line stops where the next step would not fit in its 16 GB. The buttons above each chart switch between the two machines and between the input PDFs.",
    },
}


def fmt_time(s, lang):
    return f"{s * 1000:,.0f} ms" if s < 1 else f"{s:,.2f} s"


def fmt_size(b):
    if b >= 1e9:
        return f"{b / 1e9:,.2f} GB"
    return f"{b / 1e6:,.1f} MB" if b >= 1e6 else f"{b / 1e3:,.0f} KB"


def load():
    """One entry per machine. The tool names (nori -j6 on the Mac, nori -j8 on Linux) come from the file."""
    data = {}
    for machine in MACHINES:
        results = json.loads(RESULTS[machine].read_text())
        d = data[machine] = {"tools": list(results["tools"]), "fixtures": {}, "corpora": results.get("corpora", {})}
        for fixture in results["fixtures"]:
            d["fixtures"][fixture["name"]] = {
                "pages": fixture["pages"], "objects": fixture["objects"], "bytes": fixture["bytes"],
                "source": fixture.get("source") or {}, "cases": {c["count"]: c for c in fixture["cases"]}}
    return data


def bar_class(tool):
    return "bar-norij" if tool.startswith("nori -j") else f"bar-{tool}"


def key_of(name):
    return name.removesuffix(".pdf")


def chart(data, key, t, machine):
    """SVG line chart of peak memory against file count, one line per tool."""
    tools = data["tools"]
    cases = data["fixtures"][key]["cases"]
    counts = sorted(cases)
    w, h = 640, 380
    left, right, top, bottom = 72, 150, 28, 52
    pw, ph = w - left - right, h - top - bottom
    ymax = max(e["rss_bytes"] for c in cases.values() for e in c["tools"].values() if "rss_bytes" in e)
    step = 1e9 if ymax > 2e9 else 250e6 if ymax > 500e6 else 100e6 if ymax > 200e6 else 25e6
    ymax = (int(ymax / step) + 1) * step
    xs = {c: left + pw * i / (len(counts) - 1) for i, c in enumerate(counts)}
    y = lambda v: top + ph - ph * v / ymax
    out = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-labelledby="chart-{machine}-{key_of(key)}-title">',
           f'<title id="chart-{machine}-{key_of(key)}-title">{t["chart_title"]}: {t["fixture_label"][key]}（{t["machine_label"][machine]}）</title>']
    tick = step
    while tick <= ymax:
        yy = y(tick)
        label = f"{tick / 1e9:g} GB" if step >= 1e9 else f"{tick / 1e6:g} MB"
        out.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left + pw}" y2="{yy:.1f}" stroke="var(--rule-light)"/>')
        out.append(f'<text x="{left - 10}" y="{yy + 4:.1f}" text-anchor="end" class="tick">{label}</text>')
        tick += step
    out.append(f'<line x1="{left}" y1="{top + ph}" x2="{left + pw}" y2="{top + ph}" stroke="var(--rule)"/>')
    for c in counts:
        out.append(f'<text x="{xs[c]:.1f}" y="{top + ph + 24}" text-anchor="middle" class="tick">{c:,}</text>')
    out.append(f'<text x="{left + pw / 2:.1f}" y="{h - 6}" text-anchor="middle" class="tick">{t["files"]}</text>')
    styles = {"nori": ("var(--nori)", "3.5", ""), "nori -j": ("var(--nori)", "2", "6 5"),
              "qpdf": ("var(--ink-soft)", "2.5", ""), "lopdf": ("var(--ink-faint)", "2.5", "6 5")}
    labels = []
    for tool in tools:
        points = [(c, cases[c]["tools"][tool]["rss_bytes"]) for c in counts
                  if tool in cases[c]["tools"] and "rss_bytes" in cases[c]["tools"][tool]]
        if not points:
            continue
        color, width, dash = styles["nori -j" if tool.startswith("nori -j") else tool]
        path = " ".join(f"{xs[c]:.1f},{y(v):.1f}" for c, v in points)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="{width}"{dash_attr} stroke-linejoin="round"/>')
        for c, v in points:
            out.append(f'<circle cx="{xs[c]:.1f}" cy="{y(v):.1f}" r="4" fill="{color}"/>')
        c, v = points[-1]
        if c == counts[-1]:
            labels.append([xs[c] + 10, y(v) + 4, tool, fmt_size(v), color, tool == "nori"])
        else:
            # A line cut short ends mid-chart; its label goes above the last point.
            out.append(f'<text x="{xs[c]:.1f}" y="{y(v) - 10:.1f}" text-anchor="middle" class="label" fill="{color}">{tool} {fmt_size(v)}</text>')
    # Labels sit at the end of their line, kept above the axis and apart from
    # each other; the lines near zero are pushed up in turn.
    labels.sort(key=lambda l: -l[1])
    floor = top + ph - 2
    for i, label in enumerate(labels):
        limit = floor if i == 0 else labels[i - 1][1] - 18
        label[1] = min(label[1], limit)
    for x, yy, tool, value, color, bold in labels:
        weight = ' font-weight="700"' if bold else ""
        out.append(f'<text x="{x:.1f}" y="{yy:.1f}" class="label" fill="{color}"{weight}>{tool} {value}</text>')
    out.append("</svg>")
    return "\n".join(out)


def chart_caption(d, key, t):
    """The caption's numbers come from the last measured file count on that machine."""
    cases = d["fixtures"][key]["cases"]
    last = max(cases)
    tools = cases[last]["tools"]
    lopdf_count = max(c for c in cases if "rss_bytes" in cases[c]["tools"].get("lopdf", {}))
    lopdf_value = fmt_size(cases[lopdf_count]["tools"]["lopdf"]["rss_bytes"])
    lopdf_last = (t["lopdf_last"].format(value=lopdf_value) if lopdf_count == last
                  else t["lopdf_cut"].format(count=f"{lopdf_count:,}", value=lopdf_value))
    return t["chart_caption"][key].format(
        count=f"{last:,}", pages=f"{cases[last]['pages']:,}", nori=fmt_size(tools["nori"]["rss_bytes"]),
        qpdf=fmt_size(tools["qpdf"]["rss_bytes"]), lopdf_last=lopdf_last)


def bench_rows(data, key, metric, t):
    tools = data["tools"]
    cases = data["fixtures"][key]["cases"]
    rows = []
    for count in sorted(cases):
        case = cases[count]
        entries = {tool: case["tools"].get(tool) for tool in tools}
        values = {tool: e[metric] for tool, e in entries.items() if e and metric in e}
        biggest = max(values.values())
        fmt = fmt_time if metric == "time_s" else fmt_size
        bars = []
        spoken = []
        for tool in tools:
            if tool in values:
                v = values[tool]
                bars.append(f'<div class="bar {bar_class(tool)}"><span>{tool} <b>{fmt(v, t["lang"]) if metric == "time_s" else fmt(v)}</b></span>'
                            f'<div class="bar-fill" style="--w: {100 * v / biggest:.2f}%"></div></div>')
                spoken.append(f"{tool} {fmt(v, t['lang']) if metric == 'time_s' else fmt(v)}")
            else:
                bars.append(f'<div class="bar bar-none"><span>{tool} <b>{t["not_measured"]}</b></span><div></div></div>')
        if "qpdf" in values:
            if metric == "time_s":
                ratio = values["qpdf"] / values["nori"]
                big = f"{ratio:.1f} {t['ratio_time']}" if t["lang"] == "ja" else f"{ratio:.1f}{t['ratio_time']}"
                small = t["ratio_time_small"]
            else:
                ratio = values["nori"] / values["qpdf"]
                big = f"1/{1 / ratio:.0f}" if ratio < 0.1 else f"{100 * ratio:.0f}%"
                small = t["ratio_memory_small"]
            ratio_html = f'<p class="bench-ratio"><span class="visually-hidden">{"、".join(spoken) if t["lang"] == "ja" else ", ".join(spoken)}. </span>{big}<small>{small}</small></p>'
        else:
            ratio_html = f'<p class="bench-ratio bench-ratio-none"><span class="visually-hidden">{", ".join(spoken)}. </span><small>{t["ratio_none"]}</small></p>'
        rows.append(f'''        <li class="bench-row">
          <p class="bench-name"><b>{count:,}</b> {t["files"]}<span>{case["pages"]:,} {t["pages"]}</span></p>
          <div class="bench-bars" aria-hidden="true">
{chr(10).join("            " + b for b in bars)}
          </div>
          {ratio_html}
        </li>''')
    return "\n".join(rows)


def fixture_buttons(t, group, aria):
    return (f'<div class="modes" role="group" aria-label="{aria}" data-group="{group}">'
            + "".join(f'<button type="button" data-fixture="{key_of(k)}" aria-pressed="{"true" if i == 0 else "false"}">{t["fixture_short"][k]}</button>' for i, k in enumerate(FIXTURES[t["lang"]]))
            + "</div>")


def machine_buttons(t, group):
    """Mac / Linux switch; every group on the page switches together."""
    return (f'<div class="modes modes-machine" role="group" aria-label="{t["aria_machine"]}" data-group="{group}">'
            + "".join(f'<button type="button" data-machine="{m}" aria-pressed="{"true" if i == 0 else "false"}">{t["machine_short"][m]}</button>' for i, m in enumerate(MACHINES))
            + "</div>")


def per_machine(data, t, render):
    """Renders a block once per machine; only the first is visible until a button is pressed."""
    return "\n".join(render(data[m], m, "" if i == 0 else " hidden") for i, m in enumerate(MACHINES))


def fixture_table(data, t):
    """One row per benchmark PDF: what it is, where it comes from, how it is built."""
    rows = []
    for name in FIXTURES[t["lang"]]:
        f = data[MACHINES[0]]["fixtures"][name]
        src = f["source"]
        link = f'<a href="{src["page"]}" target="_blank" rel="noopener">{t["fixture_label"][name]}</a>' if src else t["fixture_label"][name]
        rows.append(f'          <tr><td>{link}</td><td>{t["fixture_desc"][name]}</td><td>{f["pages"]}</td><td>{f["objects"]:,}</td><td>{fmt_size(f["bytes"])}</td></tr>')
    return "\n".join(rows)


def corpus_table(d, machine, hidden, t, key):
    """Time, memory and output size of one machine's corpus run, plus the note under it."""
    corpus = d["corpora"][key]
    tools = d["tools"]
    cells = []
    for metric, fmt in [("time_s", lambda v: fmt_time(v, t["lang"])), ("rss_bytes", fmt_size), ("output_bytes", fmt_size)]:
        cells.append("".join(f'<td>{fmt(corpus["tools"][n][metric]) if n in corpus["tools"] and metric in corpus["tools"][n] else "-"}</td>' for n in tools))
    r = corpus["tools"]
    largest = max(f["bytes"] for f in corpus["files"])
    note = t["corpus_note"][key].format(
        pages=f"{corpus['pages']:,}", nori_time=fmt_time(r["nori"]["time_s"], t["lang"]),
        vs_qpdf=ratio_words(r["qpdf"]["time_s"] / r["nori"]["time_s"], t),
        vs_lopdf=ratio_words(r["lopdf"]["time_s"] / r["nori"]["time_s"], t),
        nori_mem=fmt_size(r["nori"]["rss_bytes"]), largest=fmt_size(largest))
    return f'''      <div class="corpus-run" data-machine="{machine}"{hidden}>
      <div class="table-scroll">
        <table class="corpus">
          <thead><tr><th></th>{"".join(f"<th>{n}</th>" for n in tools)}</tr></thead>
          <tbody>
            <tr><th>{t["time_title"]}</th>{cells[0]}</tr>
            <tr><th>{t["memory_title"]}</th>{cells[1]}</tr>
            <tr><th>{t["output_title"]}</th>{cells[2]}</tr>
          </tbody>
        </table>
      </div>
      <p class="bench-lede">{note}</p>
      </div>'''


def ratio_words(ratio, t):
    """'2 倍' / '2×', or '16 倍' / '16×'; one decimal below 10."""
    n = f"{ratio:.1f}" if ratio < 10 else f"{ratio:.0f}"
    return f"{n} {t['ratio_time']}" if t["lang"] == "ja" else f"{n}{t['ratio_time']}"


def corpus_block(data, t, key):
    corpus = data[MACHINES[0]]["corpora"].get(key)
    if not corpus:
        return ""
    files = "\n".join(
        f'            <li><a href="{f["source"]["page"]}" target="_blank" rel="noopener">{f["source"]["title"].removeprefix("File:").removesuffix(".pdf")}</a><span>{f["pages"]} {t["pages"]} · {f["objects"]:,} {t["objects"]} · {fmt_size(f["bytes"])} · {f["source"]["license"]}</span></li>'
        for f in corpus["files"] if f.get("source"))
    total_bytes = sum(f["bytes"] for f in corpus["files"])
    tables = per_machine(data, t, lambda d, m, hidden: corpus_table(d, m, hidden, t, key))
    return f'''      <div class="bench-head">
        <h3 class="bench-title">{t["corpus_title"][key]}</h3>
        {machine_buttons(t, f"corpus-{key}")}
      </div>
      <p class="bench-lede">{t["corpus_lede"][key].format(files=len(corpus["files"]), pages=f"{corpus['pages']:,}", size=fmt_size(total_bytes))}</p>
{tables}
      <details class="method">
        <summary>{t["corpus_files"]}</summary>
        <div class="method-body">
          <ol class="corpus-files">
{files}
          </ol>
        </div>
      </details>
'''


def page(data, t):
    site = "https://champierre.github.io/nori/"
    nav = "\n".join(f'      <a href="{href}">{label}</a>' for href, label in t["nav"])
    h1 = "".join(f"<span>{line}</span>" for line in t["h1"])
    charts = per_machine(data, t, lambda d, m, hidden: "\n".join(
        f'      <figure class="chart-figure" data-fixture="{key_of(k)}" data-machine="{m}"{"" if i == 0 and not hidden else " hidden"}>\n{chart(d, k, t, m)}\n        <figcaption>{chart_caption(d, k, t)}</figcaption>\n      </figure>'
        for i, k in enumerate(FIXTURES[t["lang"]])))
    sheets = "\n".join(f'          <span class="paste-sheet" style="--i: {i}"></span>' for i in range(8))
    cards = "\n".join(f"      <li><b>{big}</b><span>{small}</span></li>" for big, small in t["cards"])
    flow = lambda steps: "".join(f"<li>{s}</li>" for s in steps)
    points = "\n".join(f"        <li><strong>{title}</strong><span>{body}</span></li>" for title, body in t["how_points"])
    notes = "\n".join(f"        <li><strong>{title}</strong><span>{body}</span></li>" for title, body in t["notes"])
    lists = {}
    for metric in ["time_s", "rss_bytes"]:
        lists[metric] = per_machine(data, t, lambda d, m, hidden, metric=metric: "\n".join(
            f'      <ul class="bench" data-fixture="{key_of(k)}" data-machine="{m}"{"" if i == 0 and not hidden else " hidden"}>\n{bench_rows(d, k, metric, t)}\n      </ul>'
            for i, k in enumerate(FIXTURES[t["lang"]])))
    corpora = "\n".join(corpus_block(data, t, key) for key in CORPORA[t["lang"]])
    scope = lambda items: "\n".join(f"            <li>{i}</li>" for i in items)
    return f'''<!doctype html>
<html lang="{t["lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t["title"]}</title>
<meta name="description" content="{t["description"]}">
<meta property="og:title" content="{t["title"]}">
<meta property="og:description" content="{t["description"]}">
<meta property="og:type" content="website">
<meta property="og:url" content="{site}{t["dir"]}">
<meta property="og:image" content="{site}images/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" hreflang="ja" href="{site}">
<link rel="alternate" hreflang="en" href="{site}en/">
<link rel="alternate" hreflang="x-default" href="{site}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect x='2' y='2' width='28' height='28' rx='3' fill='%23D9472B'/%3E%3Crect x='8' y='9' width='16' height='4' fill='%23fff'/%3E%3Crect x='8' y='19' width='16' height='4' fill='%23fff'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=BIZ+UDGothic:wght@400;700&family=Zen+Kaku+Gothic+New:wght@400;700;900&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body id="top">
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="./" aria-label="{t["brand_aria"]}">
      <span class="seal" aria-hidden="true">糊</span>
      <span class="brand-name">nori</span>
    </a>
    <nav class="site-nav" aria-label="{t["aria_nav"]}">
{nav}
      <a href="https://github.com/champierre/nori" target="_blank" rel="noopener">GitHub</a>
    </nav>
    <a class="lang-switch" href="{t["alt_href"]}" hreflang="{t["alt_lang"]}" lang="{t["alt_lang"]}">{t["alt_label"]}</a>
  </div>
</header>

<main>
  <section class="hero" aria-labelledby="hero-title">
    <div class="wrap hero-grid">
      <div class="hero-copy">
        <h1 id="hero-title">{h1}</h1>
        <p class="lede">{t["lede"]}</p>
        <div class="actions">
          <a class="button button-primary" href="#install">{t["install_button"]}</a>
          <a class="button" href="https://github.com/champierre/nori" target="_blank" rel="noopener">{t["github_button"]}</a>
        </div>
      </div>

      <figure class="paste" aria-labelledby="paste-caption">
        <div class="paste-stage" aria-hidden="true">
          <div class="paste-strip"></div>
{sheets}
          <div class="paste-gauge"><span>{t["paste_memory"]}</span><i></i><b>{t["paste_memory_value"]}</b><em>{t["paste_memory_note"]}</em></div>
        </div>
        <figcaption id="paste-caption">{t["paste_caption"]}</figcaption>
      </figure>
    </div>
    <ul class="wrap cards">
{cards}
    </ul>
  </section>

  <section class="section" id="how" aria-labelledby="how-title">
    <div class="wrap split">
      <div>
        <h2 id="how-title">{t["how_title"]}</h2>
        <p>{t["how_p1"]}</p>
        <p>{t["how_p2"]}</p>
      </div>
      <div>
        <div class="flows">
          <div class="flow flow-all">
            <p class="flow-title">{t["flow_all_title"]}<span>{t["flow_all_memory"]}</span></p>
            <ol class="flow-steps">{flow(t["flow_all"])}</ol>
          </div>
          <div class="flow flow-nori">
            <p class="flow-title">{t["flow_nori_title"]}<span>{t["flow_nori_memory"]}</span></p>
            <ol class="flow-steps flow-loop">{flow(t["flow_nori"])}</ol>
          </div>
        </div>
        <ul class="points">
{points}
        </ul>
      </div>
    </div>
  </section>

  <section class="section" id="benchmark" aria-labelledby="benchmark-title">
    <div class="wrap">
      <h2 id="benchmark-title">{t["bench_title"]}</h2>
      <p>{t["bench_p1"]}</p>
      <p>{t["bench_p2"]}</p>
      <div class="table-scroll">
        <table class="fixtures">
          <thead><tr><th>{t["fixture_col"]}</th><th>{t["fixture_desc_col"]}</th><th>{t["pages_col"]}</th><th>{t["objects_col"]}</th><th>{t["size_col"]}</th></tr></thead>
          <tbody>
{fixture_table(data, t)}
          </tbody>
        </table>
      </div>

      <div class="bench-head">
        <h3 class="bench-title">{t["chart_title"]}</h3>
        <div class="mode-groups">{machine_buttons(t, "chart")}{fixture_buttons(t, "chart", t["aria_fixture"])}</div>
      </div>
      <p class="bench-lede">{t["chart_section_lede"]}</p>
      <div class="chart-sheet">
{charts}
      </div>

      <div class="bench-head">
        <h3 class="bench-title">{t["time_title"]}</h3>
        <div class="mode-groups">{machine_buttons(t, "time")}{fixture_buttons(t, "time", t["aria_fixture_time"])}</div>
      </div>
      <p class="bench-lede">{t["bench_lede_time"]}</p>
{lists["time_s"]}

      <div class="bench-head">
        <h3 class="bench-title">{t["memory_title"]}</h3>
        <div class="mode-groups">{machine_buttons(t, "memory")}{fixture_buttons(t, "memory", t["aria_fixture_memory"])}</div>
      </div>
      <p class="bench-lede">{t["bench_lede_memory"]}</p>
{lists["rss_bytes"]}

      <ul class="bench-notes">
{notes}
      </ul>

{corpora}
      <details class="method">
        <summary>{t["method_summary"]}</summary>
        <div class="method-body">
          <p>{t["method_p1"]}</p>
          <div class="cmd"><pre><code>nori -o output.pdf input-00001.pdf input-00002.pdf ...
nori -j 6 -o output.pdf input-00001.pdf input-00002.pdf ...

qpdf --warning-exit-0 --empty --pages input-00001.pdf input-00002.pdf ... -- output.pdf

lopdf-merge -o output.pdf input-00001.pdf input-00002.pdf ...</code></pre><button class="copy" type="button">{t["copy"]}</button></div>
          <p>{t["method_p2"]}</p>
        </div>
      </details>
    </div>
  </section>

  <section class="section" id="scope" aria-labelledby="scope-title">
    <div class="wrap">
      <h2 id="scope-title">{t["scope_title"]}</h2>
      <div class="scope">
        <div>
          <h3>{t["scope_yes_title"]}</h3>
          <ul>
{scope(t["scope_yes"])}
          </ul>
        </div>
        <div>
          <h3>{t["scope_no_title"]}</h3>
          <ul>
{scope(t["scope_no"])}
          </ul>
        </div>
      </div>
    </div>
  </section>

  <section class="section" id="install" aria-labelledby="install-title">
    <div class="wrap">
      <h2 id="install-title">{t["install_title"]}</h2>
      <p>{t["install_p"]}</p>
      <div class="cmd"><pre><code>cargo install --git https://github.com/champierre/nori
nori --version</code></pre><button class="copy" type="button">{t["copy"]}</button></div>
    </div>
  </section>

  <section class="section" id="usage" aria-labelledby="usage-title">
    <div class="wrap split">
      <div>
        <h2 id="usage-title">{t["usage_title"]}</h2>
        <p>{t["usage_p1"]}</p>
        <p>{t["usage_p2"]}</p>
        <p>{t["usage_p3"]}</p>
      </div>
      <div class="usage">
        <div>
          <h3>{t["cli_title"]}</h3>
          <div class="cmd"><pre><code>{t["cli_code"]}</code></pre><button class="copy" type="button">{t["copy"]}</button></div>
        </div>
        <div>
          <h3>{t["rails_title"]}</h3>
          <div class="cmd"><pre><code>{t["rails_code"]}</code></pre><button class="copy" type="button">{t["copy"]}</button></div>
        </div>
      </div>
    </div>
  </section>
</main>

<footer class="site-footer">
  <div class="wrap">
    <a class="brand" href="./">
      <span class="seal" aria-hidden="true">糊</span>
      <span class="brand-name">nori</span>
    </a>
    <div class="footer-links">
      <a href="https://github.com/champierre/nori" target="_blank" rel="noopener">{t["footer_github"]}</a>
      <a href="https://github.com/champierre/nori/blob/main/LICENSE" target="_blank" rel="noopener">{t["footer_license"]}</a>
      <span>© 2026 Junya Ishihara</span>
    </div>
  </div>
</footer>
<script>
(() => {{
  // Input PDF and machine toggles: every group switches together.
  const state = {{ fixture: document.querySelector("button[data-fixture]").dataset.fixture, machine: "{MACHINES[0]}" }};
  const apply = () => {{
    document.querySelectorAll("button[data-fixture]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.fixture === state.fixture)));
    document.querySelectorAll("button[data-machine]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.machine === state.machine)));
    document.querySelectorAll("[data-machine]:not(button)").forEach((el) => {{
      el.hidden = el.dataset.machine !== state.machine || ("fixture" in el.dataset && el.dataset.fixture !== state.fixture);
    }});
  }};
  document.querySelectorAll("button[data-fixture], button[data-machine]").forEach((button) => {{
    button.addEventListener("click", () => {{
      if (button.dataset.fixture) state.fixture = button.dataset.fixture;
      if (button.dataset.machine) state.machine = button.dataset.machine;
      apply();
    }});
  }});
  // Copy buttons.
  document.querySelectorAll(".cmd").forEach((block) => {{
    const button = block.querySelector(".copy");
    button.addEventListener("click", async () => {{
      const text = block.querySelector("code").innerText;
      try {{
        await navigator.clipboard.writeText(text);
        button.textContent = "{t["copied"]}";
      }} catch {{
        button.textContent = "{t["copy_failed"]}";
      }}
      setTimeout(() => {{ button.textContent = "{t["copy"]}"; }}, 2000);
    }});
  }});
}})();
</script>
</body>
</html>
'''


CSS = """  /* Kraft paper, white sheets, sumi ink, and one color: the red of a tube of paste. */
  :root {
    --kraft: #E9DFC9;
    --kraft-dark: #D9CBAE;
    --sheet: #FFFDF8;
    --ink: #1F1A14;
    --ink-soft: #5A5146;
    --ink-faint: #9A8F7E;
    --rule: #C9BBA0;
    --rule-light: #E6DCC8;
    --nori: #D9472B;
    --nori-dark: #B8371F;
    --nori-pale: #F5D6CD;
    --gothic: "Zen Kaku Gothic New", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif;
    --code: "BIZ UDGothic", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
    --gutter: clamp(16px, 4vw, 48px);
    --paper-shadow: 0 1px 0 var(--rule), 0 6px 14px rgba(31, 26, 20, 0.08);
  }
  *, *::before, *::after { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
  body { margin: 0; background: var(--kraft); color: var(--ink); font-family: var(--gothic); font-size: 1.0625rem; line-height: 1.9; }
  a { color: inherit; text-underline-offset: 0.2em; text-decoration-thickness: 1px; }
  a:hover { text-decoration-thickness: 2px; }
  p { margin: 0 0 1em; }
  code { font-family: var(--code); font-size: 0.9em; }
  .wrap { max-width: 1180px; margin-inline: auto; padding-inline: var(--gutter); }
  .visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

  .seal { display: inline-grid; place-items: center; width: 2.4rem; height: 2.4rem; border-radius: 3px; background: var(--nori); font-weight: 900; font-size: 1.3rem; line-height: 1; color: var(--sheet); transform: rotate(-4deg); }
  .site-header { padding-block: 20px; }
  .site-header .wrap { display: flex; flex-wrap: wrap; align-items: center; gap: 16px 32px; }
  .brand { display: inline-flex; align-items: center; gap: 12px; text-decoration: none; color: var(--ink); }
  .brand-name { font-family: var(--code); font-size: 1.25rem; font-weight: 700; letter-spacing: 0.02em; }
  .site-nav { display: flex; flex-wrap: wrap; gap: clamp(12px, 3vw, 28px); font-size: 0.9375rem; margin-inline-start: auto; }
  .site-nav a { text-decoration: none; }
  .site-nav a:hover { text-decoration: underline; text-decoration-color: var(--nori); }
  .lang-switch { flex: none; padding: 2px 10px; border: 1px solid var(--ink-faint); border-radius: 2px; font-size: 0.875rem; text-decoration: none; color: var(--ink-soft); }

  .hero { padding-block: clamp(24px, 5vw, 64px) clamp(40px, 6vw, 72px); }
  .hero-grid { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 6fr); gap: clamp(32px, 5vw, 72px); align-items: center; }
  .hero h1 { margin: 0 0 24px; font-weight: 900; font-size: clamp(1.8rem, 3.1vw, 3rem); line-height: 1.3; letter-spacing: 0.01em; color: var(--ink); font-feature-settings: "palt" 1; }
  .hero h1 span { display: block; white-space: nowrap; }
  .lede { margin: 0 0 32px; max-width: 30em; }
  .actions { display: flex; flex-wrap: wrap; gap: 12px; }
  .button { display: inline-flex; align-items: center; min-height: 48px; padding: 10px 22px; border: 2px solid var(--ink); border-radius: 3px; font-weight: 700; text-decoration: none; color: var(--ink); background: transparent; }
  .button:hover { text-decoration: none; background: var(--sheet); }
  .button-primary { background: var(--nori); border-color: var(--nori); color: var(--sheet); }
  .button-primary:hover { background: var(--nori-dark); border-color: var(--nori-dark); }

  /* Sheets fly in one by one and stick to a strip of paste; the memory gauge below never changes. */
  .paste { margin: 0; padding: clamp(16px, 2.5vw, 28px); background: var(--sheet); border-radius: 3px; box-shadow: var(--paper-shadow); }
  .paste-stage { position: relative; height: 230px; overflow: hidden; }
  .paste-strip { position: absolute; left: 0; bottom: 84px; height: 8px; width: 100%; background: linear-gradient(90deg, var(--nori) 0 88%, transparent); transform-origin: left; animation: strip 9.6s linear infinite; }
  .paste-sheet { position: absolute; left: calc(14px + var(--i) * 11.4%); bottom: 92px; width: 9.5%; min-width: 34px; height: 64px; background: var(--sheet); border: 1.5px solid var(--ink); border-radius: 2px; box-shadow: 2px 3px 0 rgba(31, 26, 20, 0.12);
    background-image: linear-gradient(var(--ink-faint), var(--ink-faint)), linear-gradient(var(--ink-faint), var(--ink-faint)), linear-gradient(var(--ink-faint), var(--ink-faint));
    background-size: 60% 1.5px, 70% 1.5px, 50% 1.5px; background-position: 20% 30%, 20% 50%, 20% 70%; background-repeat: no-repeat;
    animation: sheet 9.6s ease-out infinite; animation-delay: calc(var(--i) * 0.9s); }
  @keyframes sheet {
    0% { transform: translate(260px, -140px) rotate(12deg); opacity: 0; }
    3% { opacity: 1; }
    8% { transform: translate(0, 0) rotate(0deg); }
    9.5% { transform: translate(0, 2px) scale(1.03, 0.97); }
    11% { transform: translate(0, 0); }
    88% { transform: translate(0, 0); opacity: 1; }
    94% { opacity: 0; }
    100% { transform: translate(260px, -140px) rotate(12deg); opacity: 0; }
  }
  @keyframes strip {
    0% { transform: scaleX(0.06); }
    70% { transform: scaleX(1); }
    92% { transform: scaleX(1); }
    100% { transform: scaleX(0.06); }
  }
  .paste-gauge { position: absolute; left: 0; bottom: 8px; display: flex; align-items: center; gap: 10px; font-size: 0.8125rem; color: var(--ink-soft); }
  .paste-gauge i { display: block; width: 44px; height: 12px; background: var(--nori); }
  .paste-gauge b { font-family: var(--code); color: var(--ink); }
  .paste-gauge em { font-style: normal; color: var(--ink-faint); }
  .paste figcaption { margin-top: 12px; font-size: 0.875rem; color: var(--ink-soft); line-height: 1.7; }
  @media (prefers-reduced-motion: reduce) {
    .paste-sheet, .paste-strip { animation: none; }
  }

  .cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: clamp(16px, 2.5vw, 32px); margin: clamp(40px, 5vw, 64px) auto 0; padding-block: 0; list-style: none; }
  .cards li { position: relative; padding: 22px 24px 20px; background: var(--sheet); border-radius: 2px; box-shadow: var(--paper-shadow); }
  .cards li:nth-child(1) { transform: rotate(-1deg); }
  .cards li:nth-child(2) { transform: rotate(1deg); }
  .cards li::before { content: ""; position: absolute; top: -8px; left: 50%; width: 36px; height: 14px; margin-left: -18px; background: var(--nori); opacity: 0.85; transform: rotate(-3deg); }
  .cards b { display: block; font-family: var(--code); font-weight: 700; font-size: 2.4rem; line-height: 1.1; color: var(--nori); }
  .cards span { display: block; margin-top: 6px; font-size: 0.875rem; color: var(--ink-soft); line-height: 1.6; }

  /* Each section is a sheet pasted onto the kraft paper, with a dab of paste at the corner. */
  .section { position: relative; max-width: 1180px; margin: clamp(24px, 3vw, 40px) auto; padding-block: clamp(40px, 6vw, 80px); background: var(--sheet); border-radius: 3px; box-shadow: var(--paper-shadow); }
  .section::before { content: ""; position: absolute; top: -6px; left: 36px; width: 46px; height: 16px; background: var(--nori); opacity: 0.85; transform: rotate(-2deg); }
  .section h2 { margin: 0 0 20px; font-weight: 900; font-size: clamp(1.5rem, 2.6vw, 2.1rem); line-height: 1.4; color: var(--ink); font-feature-settings: "palt" 1; word-break: keep-all; overflow-wrap: anywhere; }
  .section h3 { margin: 0 0 12px; font-size: 1.125rem; color: var(--ink); }
  .split { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: clamp(32px, 5vw, 72px); align-items: start; }

  .flows { display: grid; gap: 16px; }
  .flow { padding: 18px 20px; border: 1px solid var(--rule); border-radius: 2px; background: var(--kraft); }
  .flow-nori { border: 2px solid var(--nori); background: var(--sheet); }
  .flow-title { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 4px 16px; margin: 0 0 10px; font-weight: 700; color: var(--ink); }
  .flow-nori .flow-title { color: var(--nori); }
  .flow-title span { font-weight: 400; font-size: 0.875rem; color: var(--ink-soft); }
  .flow-steps { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0; padding: 0; list-style: none; font-size: 0.9375rem; }
  .flow-steps li { padding: 6px 12px; border: 1px solid var(--ink-faint); border-radius: 2px; background: var(--sheet); }
  .flow-steps li + li::before { content: "→"; position: relative; left: -12px; margin-right: -6px; color: var(--ink-faint); }
  .flow-all .flow-steps li:first-child { border-width: 1px 1px 1px 10px; border-left-color: var(--ink-faint); }
  .flow-loop li:last-child::after { content: " ↺"; color: var(--nori); }
  .points { margin: 28px 0 0; padding: 0; list-style: none; }
  .points li { display: grid; gap: 2px; padding-block: 14px; border-top: 1px solid var(--rule-light); font-size: 0.9375rem; }
  .points li:last-child { border-bottom: 1px solid var(--rule-light); }
  .points strong { color: var(--ink); }
  .points span { color: var(--ink-soft); }

  .modes { display: inline-flex; border: 2px solid var(--ink); border-radius: 3px; overflow: hidden; }
  .modes button { padding: 6px 14px; border: 0; background: var(--sheet); color: var(--ink); font: inherit; font-size: 0.875rem; cursor: pointer; }
  .modes button + button { border-left: 2px solid var(--ink); }
  .modes button[aria-pressed="true"] { background: var(--nori); color: var(--sheet); }
  .bench-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px 24px; margin: 48px 0 4px; }
  .mode-groups { display: flex; flex-wrap: wrap; gap: 8px 16px; }
  .corpus-run { margin-top: 12px; }
  .bench-title { margin: 0 !important; }
  .bench-lede { font-size: 0.9375rem; color: var(--ink-soft); }
  .chart-sheet { padding: clamp(12px, 2vw, 24px); border: 1px solid var(--rule-light); border-radius: 2px; }
  .chart-figure { margin: 0; }
  .chart { display: block; width: 100%; max-width: 760px; height: auto; margin-inline: auto; }
  .chart .tick { font-family: var(--code); font-size: 12px; fill: var(--ink-soft); }
  .chart .label { font-family: var(--code); font-size: 13px; }
  .chart-figure figcaption { margin-top: 10px; font-size: 0.875rem; color: var(--ink-soft); line-height: 1.7; }
  .bench { margin: 16px 0 0; padding: 0; list-style: none; border-top: 1px solid var(--rule-light); }
  .bench-row { display: grid; grid-template-columns: 9em minmax(0, 1fr) 8em; gap: 12px 24px; align-items: center; padding-block: 16px; border-bottom: 1px solid var(--rule-light); }
  .bench-name { margin: 0; font-size: 1rem; color: var(--ink); }
  .bench-name b { font-family: var(--code); font-size: 1.25rem; }
  .bench-name span { display: block; font-size: 0.8125rem; color: var(--ink-soft); }
  .bench-bars { display: grid; gap: 6px; }
  .bar { display: grid; grid-template-columns: 11em minmax(0, 1fr); gap: 12px; align-items: center; font-size: 0.8125rem; color: var(--ink-soft); }
  .bar b { color: var(--ink); font-family: var(--code); }
  .bar-fill { height: 12px; width: var(--w); min-width: 2px; background: var(--nori); }
  .bar-norij .bar-fill { background: repeating-linear-gradient(90deg, var(--nori) 0 6px, transparent 6px 9px); }
  .bar-qpdf .bar-fill { background: var(--ink-soft); }
  .bar-lopdf .bar-fill { background: var(--ink-faint); }
  .bar-none b { color: var(--ink-faint); font-weight: 400; }
  .bench-ratio { margin: 0; font-family: var(--code); font-weight: 700; font-size: 1.7rem; line-height: 1.2; color: var(--nori); text-align: right; }
  .bench-ratio small { display: block; font-family: var(--gothic); font-weight: 400; font-size: 0.75rem; color: var(--ink-soft); }
  .bench-ratio-none small { font-size: 0.8125rem; }
  .bench-notes { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 clamp(32px, 5vw, 72px); margin: 40px 0 0; padding: 0; list-style: none; }
  .bench-notes li { display: grid; gap: 2px; padding-block: 16px; border-top: 1px solid var(--rule-light); font-size: 0.9375rem; }
  .bench-notes strong { color: var(--ink); }
  .bench-notes span { color: var(--ink-soft); }
  .table-scroll { overflow-x: auto; margin: 8px 0 16px; }
  .fixtures, .corpus { width: 100%; border-collapse: collapse; font-size: 0.9375rem; }
  .fixtures th, .fixtures td, .corpus th, .corpus td { padding: 8px 12px; border-bottom: 1px solid var(--rule-light); text-align: left; vertical-align: top; }
  .fixtures th, .corpus thead th { font-size: 0.8125rem; color: var(--ink-soft); font-weight: 400; }
  .corpus thead th { text-align: right; }
  .fixtures td:nth-child(n+3), .fixtures th:nth-child(n+3), .corpus td { text-align: right; font-family: var(--code); white-space: nowrap; }
  .fixtures td:first-child { white-space: nowrap; }
  .corpus tbody th { white-space: nowrap; }
  .corpus td:nth-child(2), .corpus td:nth-child(3) { color: var(--nori); font-weight: 700; }
  .corpus-files { margin: 0; padding-left: 1.6em; font-size: 0.875rem; }
  .corpus-files li { padding-block: 3px; }
  .corpus-files span { display: block; color: var(--ink-faint); font-size: 0.8125rem; }
  .method { margin-top: 32px; border-top: 2px solid var(--ink); }
  .method summary { padding-block: 12px; font-weight: 700; cursor: pointer; }
  .method-body { padding-bottom: 8px; font-size: 0.9375rem; }

  .scope { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: clamp(32px, 5vw, 72px); margin-top: 8px; }
  .scope ul { margin: 0; padding-left: 1.2em; }
  .scope li { padding-block: 4px; }
  .scope li::marker { color: var(--nori); }

  .cmd { position: relative; margin: 0 0 16px; background: var(--ink); color: var(--sheet); border-radius: 3px; }
  .cmd pre { margin: 0; padding: 18px 20px; overflow-x: auto; font-family: var(--code); font-size: 0.9375rem; line-height: 1.7; }
  .cmd code { font-size: inherit; }
  .cmd .comment { color: var(--rule); }
  .copy { position: absolute; top: 8px; right: 8px; padding: 4px 10px; border: 1px solid var(--ink-faint); border-radius: 2px; background: transparent; color: var(--sheet); font: inherit; font-size: 0.75rem; cursor: pointer; }
  .copy:hover { background: var(--ink-soft); }
  .usage { display: grid; grid-template-columns: minmax(0, 1fr); gap: 32px; }

  .site-footer { padding-block: 40px 72px; font-size: 0.9375rem; color: var(--ink-soft); }
  .site-footer .wrap { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 24px; }
  .footer-links { display: flex; flex-wrap: wrap; gap: 24px; }

  @media (max-width: 1200px) {
    .section { margin-inline: var(--gutter); }
  }
  @media (max-width: 900px) {
    .hero-grid, .split, .bench-notes, .scope { grid-template-columns: minmax(0, 1fr); }
    .cards { grid-template-columns: minmax(0, 1fr); }
    .bench-row { grid-template-columns: minmax(0, 1fr); }
    .bench-ratio { text-align: left; }
    .site-nav { margin-inline-start: 0; }
  }
  @media (max-width: 560px) {
    .bar { grid-template-columns: minmax(0, 1fr); gap: 2px; }
    .paste-stage { height: 200px; }
  }"""


def main():
    data = load()
    (HERE / "index.html").write_text(page(data, T["ja"]), encoding="utf-8")
    (HERE / "en" / "index.html").write_text(page(data, T["en"]), encoding="utf-8")
    print("wrote docs/index.html and docs/en/index.html")


if __name__ == "__main__":
    main()
