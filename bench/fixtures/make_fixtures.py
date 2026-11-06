#!/usr/bin/env python3
"""Builds the benchmark inputs: one 14-page statement rendered by LibreOffice and by Chrome.

The same HTML goes through both so the two PDFs differ only in how the producer builds a
PDF (fonts, object count), which is what the benchmark wants to show.
Needs LibreOffice, Google Chrome, qpdf and the Noto Sans JP font.
"""
import pathlib
import random
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PAGES = 14
ROWS = int(sys.argv[1]) if len(sys.argv) > 1 else 15
SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def html():
    random.seed(1)
    items = ["基本料金", "通話料", "データ通信料", "オプション利用料", "機器レンタル料", "工事費", "手数料", "割引", "消費税"]
    pages = []
    for p in range(1, PAGES + 1):
        rows = "".join(
            f"<tr><td>{p:02d}-{i:03d}</td><td>{random.choice(items)}</td><td align='right'>{random.randint(1, 20)}</td>"
            f"<td align='right'>{random.randint(100, 99999):,}</td><td align='right'>{random.randint(100, 999999):,}</td></tr>"
            for i in range(1, ROWS + 1))
        pages.append(f"""
<div class="page">
  <h1>ご利用明細書</h1>
  <p>2026年11月分　お客様番号 100{p:04d}　{p} / {PAGES} ページ</p>
  <p>平素は格別のご高配を賜り、厚く御礼申し上げます。2026年11月分のご利用内容は下記のとおりです。ご確認のうえ、お支払期日までにお振込みくださいますようお願い申し上げます。</p>
  <table border="1" cellpadding="4" cellspacing="0" width="100%"><thead><tr><th>明細番号</th><th>項目</th><th>数量</th><th>単価（円）</th><th>金額（円）</th></tr></thead><tbody>{rows}</tbody></table>
  <p><small>本書に関するお問い合わせ: 株式会社サンプル通信 お客様センター 0120-000-000（平日 9:00〜18:00）</small></p>
</div>""")
    return f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8"><title>ご利用明細書</title>
<style>
@page {{ size: A4; margin: 15mm; }}
body {{ font-family: "Noto Sans JP"; font-size: 10pt; }}
.page {{ page-break-after: always; }}
h1 {{ font-size: 18pt; }}
</style></head><body>{''.join(pages)}</body></html>"""


def page_count(pdf):
    return int(subprocess.run(["qpdf", "--show-npages", str(pdf)], capture_output=True, text=True, check=True).stdout)


def main():
    source = HERE / "statement.html"
    source.write_text(html(), encoding="utf-8")

    libreoffice = HERE / "statement-libreoffice.pdf"
    subprocess.run([SOFFICE, "--headless", "--convert-to",
                    'pdf:writer_web_pdf_Export:{"UseTaggedPDF":{"type":"boolean","value":"false"}}',
                    "--outdir", str(HERE), str(source)], check=True, capture_output=True)
    (HERE / "statement.pdf").rename(libreoffice)

    chrome = HERE / "statement-chrome.pdf"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={chrome}", source.as_uri()], check=True, capture_output=True)

    for pdf in [libreoffice, chrome]:
        pages = page_count(pdf)
        print(f"{pdf.name}: {pages} pages, {pdf.stat().st_size:,} bytes")
        if pages != PAGES:
            sys.exit(f"{pdf.name} has {pages} pages, wanted {PAGES}; adjust ROWS")


if __name__ == "__main__":
    main()
