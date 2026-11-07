#!/usr/bin/env python3
"""Picks random PDFs on Wikimedia Commons and downloads them for the benchmark.

`select` asks Commons for PDFs in random order (CirrusSearch `srsort=random`), keeps the ones
small enough to merge in quantity, and writes the list with sizes, page counts and licenses to
bench/public-pdfs.json, so the same set can be fetched again later. `fetch` downloads that list
into bench/inputs/public/. Standard library only.

Usage: fetch.py select [--count 40] [--max-bytes 3000000] [--max-pages 60]
       fetch.py fetch
"""
import argparse
import json
import pathlib
import random
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
LIST = HERE / "public-pdfs.json"
PUBLIC = HERE / "inputs" / "public"
API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "nori-benchmark/0.1 (https://github.com/champierre/nori)"


def get(url):
    """Commons rate-limits bursts (HTTP 429); wait and retry rather than fail the whole run."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            return urllib.request.urlopen(request, timeout=120)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            time.sleep(30 * (attempt + 1))


def api(**params):
    params["format"] = "json"
    return json.load(get(API + "?" + urllib.parse.urlencode(params)))


def random_titles(limit):
    result = api(action="query", list="search", srnamespace=6, srsearch="filemime:application/pdf",
                 srsort="random", srlimit=limit, srinfo="", srprop="")
    return [hit["title"] for hit in result["query"]["search"]]


def info(titles):
    """Size, page count, mime, URL and license of each title, in batches of 50."""
    out = {}
    for i in range(0, len(titles), 50):
        result = api(action="query", titles="|".join(titles[i:i + 50]), prop="imageinfo",
                     iiprop="url|size|mime|extmetadata", iiextmetadatafilter="LicenseShortName|Artist")
        for page in result["query"]["pages"].values():
            if "imageinfo" not in page:
                continue
            ii = page["imageinfo"][0]
            meta = ii.get("extmetadata", {})
            out[page["title"]] = {
                "title": page["title"],
                "url": ii["url"],
                "page": ii["descriptionurl"],
                "bytes": ii["size"],
                "pages": ii.get("pagecount"),
                "mime": ii["mime"],
                "license": meta.get("LicenseShortName", {}).get("value", ""),
            }
    return out


def select(args):
    random.seed(args.seed)
    titles = random_titles(500)
    details = info(titles)
    kept = [d for d in details.values()
            if d["mime"] == "application/pdf" and d["pages"] and d["bytes"] <= args.max_bytes
            and d["pages"] <= args.max_pages]
    random.shuffle(kept)
    kept = kept[:args.count]
    for i, d in enumerate(kept, 1):
        d["name"] = f"public-{i:02d}.pdf"
    LIST.write_text(json.dumps({"seed": args.seed, "files": kept}, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(kept)} of {len(details)} random PDFs kept; written to {LIST.name}")
    for d in kept:
        print(f"{d['name']}: {d['pages']:>3} pages {d['bytes'] / 1e6:5.2f} MB {d['license']:<14} {d['title']}")


def fetch(args):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    files = json.loads(LIST.read_text())["files"]
    for d in files:
        target = PUBLIC / d["name"]
        if target.is_file() and target.stat().st_size == d["bytes"]:
            continue
        target.write_bytes(get(d["url"]).read())
        print(f"{d['name']}: {d['bytes']:,} bytes from {d['page']}")
        time.sleep(2)
    print(f"{len(files)} files in {PUBLIC}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("select")
    s.add_argument("--count", type=int, default=40)
    s.add_argument("--max-bytes", type=int, default=3_000_000)
    s.add_argument("--max-pages", type=int, default=60)
    s.add_argument("--seed", type=int, default=20261107)
    s.set_defaults(run=select)
    f = sub.add_parser("fetch")
    f.set_defaults(run=fetch)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
