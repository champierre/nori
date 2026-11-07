#!/usr/bin/env python3
"""Compare nori, qpdf and lopdf merging PDFs.

Two kinds of run. With --fixture, bench/inputs/ gets 10 to 2,000 copies of that PDF and each
tool merges them, which shows how time and memory grow with the number of files. With
--corpus, every PDF in a directory (the random Commons PDFs that fetch.py downloads) is merged
once, which shows that real-world files of every make come through. Each tool runs as a
command line program, the way an application would call it. Wall-clock time and peak memory
come from /usr/bin/time; the output is then checked with qpdf (page count and `qpdf --check`).
Standard library only.

Every tool runs with the open-file limit raised, because qpdf keeps every input open and the
default limit on macOS (256) is below the larger counts.

Usage: bench.py --fixture PDF [--counts 10,100,1000,2000] [--runs 5] [--warmup 1] [--jobs N]
                [--max-count TOOL=N ...] [--nori PATH] [--lopdf-merge PATH] [--qpdf PATH]
       bench.py --corpus bench/inputs/public [--runs 5] ...
A tool whose binary is missing is skipped. Results accumulate in bench/results-macos.json or
bench/results-linux.json (one entry per fixture, plus the corpus); the tables used in the
README are printed at the end.
"""
import argparse
import json
import os
import pathlib
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
INPUTS = HERE / "inputs"
OUTPUTS = HERE / "outputs"
RESULTS = HERE / f"results-{'macos' if sys.platform == 'darwin' else sys.platform}.json"
OPEN_FILES = 8192


class ToolFailed(Exception):
    def __init__(self, name, code, stderr):
        super().__init__(f"{name} failed with exit code {code}")
        self.code, self.stderr = code, stderr


def tools(args):
    """Command builders, keyed by tool name. A tool whose binary is missing is left out."""
    all_tools = {
        "nori": (args.nori, lambda ins, out: [args.nori, "-o", str(out), *map(str, ins)]),
        f"nori -j{args.jobs}": (args.nori, lambda ins, out: [
            args.nori, "-j", str(args.jobs), "-o", str(out), *map(str, ins),
        ]),
        "qpdf": (args.qpdf, lambda ins, out: [
            args.qpdf, "--warning-exit-0", "--empty", "--pages", *map(str, ins), "--", str(out),
        ]),
        "lopdf": (args.lopdf_merge, lambda ins, out: [args.lopdf_merge, "-o", str(out), *map(str, ins)]),
    }
    if args.jobs < 2:
        del all_tools[f"nori -j{args.jobs}"]
    return {name: (binary, build) for name, (binary, build) in all_tools.items()
            if shutil.which(binary) or pathlib.Path(binary).is_file()}


def timed_run(command):
    """Runs a command under /usr/bin/time; returns (seconds, peak RSS in bytes)."""
    flag = "-l" if sys.platform == "darwin" else "-v"
    # sh raises the limit and execs the tool, so /usr/bin/time still measures the tool itself.
    wrapped = ["/bin/sh", "-c", f'ulimit -n {OPEN_FILES} 2>/dev/null; exec "$0" "$@"', *command]
    start = time.perf_counter()
    result = subprocess.run(["/usr/bin/time", flag, *wrapped], capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    if result.returncode != 0:
        raise ToolFailed(command[0], result.returncode, result.stderr[-2000:])
    if sys.platform == "darwin":
        rss = int(re.search(r"(\d+)\s+maximum resident set size", result.stderr).group(1))
    else:
        rss = int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", result.stderr).group(1)) * 1024
    return elapsed, rss


def prepare_inputs(fixture, count):
    directory = INPUTS / f"{fixture.stem}-{count}"
    paths = [directory / f"{i:05d}.pdf" for i in range(1, count + 1)]
    if not all(p.is_file() for p in paths):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True)
        for p in paths:
            shutil.copyfile(fixture, p)
    return paths


def page_count(qpdf, pdf):
    """Pages as qpdf counts them; a file qpdf can read only with warnings still has a count."""
    result = subprocess.run([qpdf, "--warning-exit-0", "--show-npages", str(pdf)], capture_output=True, text=True)
    return int(result.stdout) if result.returncode == 0 else None


def check(qpdf, pdf):
    """Whether qpdf reads the whole file without errors (warnings are allowed)."""
    return subprocess.run([qpdf, "--warning-exit-0", "--check", str(pdf)], capture_output=True).returncode == 0


def human_size(n):
    return f"{n / 1e6:,.1f} MB" if n < 1e9 else f"{n / 1e9:,.2f} GB"


def human_time(s):
    return f"{s * 1000:,.0f} ms" if s < 1 else f"{s:,.2f} s"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixture", type=pathlib.Path, action="append", default=[],
                        help="input PDF to copy 10 to 2,000 times (repeatable)")
    parser.add_argument("--corpus", type=pathlib.Path,
                        help="directory of PDFs to merge once, all together, instead of copies of a fixture")
    parser.add_argument("--counts", default="10,100,1000,2000")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1,
                        help="also run nori with this many parse threads (default: CPU count)")
    parser.add_argument("--max-count", action="append", default=[], metavar="TOOL=N",
                        help="run TOOL only up to N inputs, e.g. lopdf=100 (repeatable)")
    parser.add_argument("--nori", default=str(ROOT / "target" / "release" / "nori"))
    parser.add_argument("--lopdf-merge", default=str(ROOT / "target" / "release" / "lopdf-merge"))
    parser.add_argument("--qpdf", default="qpdf")
    parser.add_argument("--keep", action="store_true", help="leave the copied inputs and merged outputs on disk")
    parser.add_argument("--tables-only", action="store_true", help="print the tables from the results file and exit")
    args = parser.parse_args()
    if args.tables_only:
        print_tables(json.loads(RESULTS.read_text()))
        return

    fixtures = args.fixture
    if not fixtures and not args.corpus:
        sys.exit("give --fixture PDF and/or --corpus DIR (or --tables-only)")
    counts = [int(c) for c in args.counts.split(",")]
    max_counts = {name: int(n) for name, n in (item.split("=") for item in args.max_count)}
    available = tools(args)
    if not available:
        sys.exit("no tools found")
    OUTPUTS.mkdir(exist_ok=True)

    # Fixtures measured earlier stay in the file, so each can be run with its own limits.
    results = json.loads(RESULTS.read_text()) if RESULTS.is_file() else {}
    results.update({
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "runs": args.runs,
        "tools": {name: version(name, binary) for name, (binary, _) in available.items()},
    })
    results["fixtures"] = [f for f in results.get("fixtures", []) if f["name"] not in {x.name for x in fixtures}]
    if args.corpus:
        # Keyed by directory name, so the all-Commons set and the Japanese set sit side by side.
        results.setdefault("corpora", {})[args.corpus.name] = measure_corpus(args, available)
        results.pop("corpus", None)
        RESULTS.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    for fixture in fixtures:
        entry = {"name": fixture.name, "bytes": fixture.stat().st_size, "pages": page_count(args.qpdf, fixture),
                 "objects": object_count(args.qpdf, fixture), "source": source(fixture.name), "cases": []}
        results["fixtures"].append(entry)
        results["fixtures"].sort(key=lambda f: f["name"])
        print(f"== {fixture.name}: {entry['pages']} pages, {entry['objects']} objects, {human_size(entry['bytes'])}")
        for count in counts:
            inputs = prepare_inputs(fixture, count)
            case = {"count": count, "pages": count * entry["pages"], "input_bytes": count * entry["bytes"],
                    "tools": {}}
            entry["cases"].append(case)
            for name, (_, build) in available.items():
                if count > max_counts.get(name, count):
                    print(f"[{count:>5}] {name:<10} skipped (--max-count)", flush=True)
                    continue
                case["tools"][name] = measure(args, name, build, inputs, case["pages"],
                                              OUTPUTS / f"{fixture.stem}-{count}-{name.replace(' ', '')}.pdf")
            RESULTS.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
            if not args.keep:
                # Thousands of copies and their merged outputs run to gigabytes; keep the disk clear.
                shutil.rmtree(inputs[0].parent, ignore_errors=True)
                for out in OUTPUTS.glob(f"{fixture.stem}-{count}-*.pdf"):
                    out.unlink()

    print()
    print_tables(results)


def measure_corpus(args, available):
    """Merges every PDF in the corpus directory once, in name order."""
    inputs = sorted(args.corpus.glob("*.pdf"))
    files = [{"name": p.name, "bytes": p.stat().st_size, "pages": page_count(args.qpdf, p),
              "objects": object_count(args.qpdf, p), "source": source(p.name)} for p in inputs]
    pages = sum(f["pages"] or 0 for f in files)
    print(f"== corpus {args.corpus}: {len(inputs)} files, {pages} pages, "
          f"{human_size(sum(f['bytes'] for f in files))}")
    tools = {}
    for name, (_, build) in available.items():
        tools[name] = measure(args, name, build, inputs, pages, OUTPUTS / f"corpus-{name.replace(' ', '')}.pdf")
    return {"directory": str(args.corpus.relative_to(ROOT)) if args.corpus.is_relative_to(ROOT) else str(args.corpus),
            "files": files, "pages": pages, "tools": tools}


def source(name):
    """Title, Commons page and license of a PDF listed in one of the public-pdfs*.json files, else None."""
    for listing in HERE.glob("public-pdfs*.json"):
        for d in json.loads(listing.read_text())["files"]:
            if d["name"] == name:
                return {"title": d["title"], "page": d["page"], "license": d["license"]}
    return None


def version(name, binary):
    if name == "lopdf":
        # lopdf-merge has no --version; the crate version is what matters.
        lock = (ROOT / "Cargo.lock").read_text()
        match = re.search(r'name = "lopdf"\nversion = "([^"]+)"', lock)
        return f"lopdf {match.group(1)}" if match else ""
    out = subprocess.run([binary, "--version"], capture_output=True, text=True).stdout.strip().splitlines()
    return out[0] if out else ""


def object_count(qpdf, pdf):
    out = subprocess.run([qpdf, "--show-xref", str(pdf)], capture_output=True, text=True).stdout
    return sum(1 for line in out.splitlines() if "offset" in line or "stream" in line)


def measure(args, name, build, inputs, expected_pages, out):
    times, rsss = [], []
    try:
        for run in range(args.warmup + args.runs):
            out.unlink(missing_ok=True)
            elapsed, rss = timed_run(build(inputs, out))
            if run >= args.warmup:
                times.append(elapsed)
                rsss.append(rss)
    except ToolFailed as e:
        print(f"[{len(inputs):>5}] {name:<10} FAILED: {e}\n{e.stderr}", flush=True)
        return {"error": str(e)}
    entry = {
        "time_s": statistics.median(times),
        "time_min_s": min(times),
        "time_max_s": max(times),
        "rss_bytes": statistics.median(rsss),
        "rss_max_bytes": max(rsss),
        "output_bytes": out.stat().st_size,
        "pages": page_count(args.qpdf, out),
        "check_ok": check(args.qpdf, out),
    }
    ok = "ok" if entry["check_ok"] and entry["pages"] == expected_pages else "BAD OUTPUT"
    print(f"[{len(inputs):>5}] {name:<10} {human_time(entry['time_s']):>10}  "
          f"{human_size(entry['rss_bytes']):>10}  {human_size(entry['output_bytes']):>10}  {ok}", flush=True)
    return entry


def print_tables(results):
    names = list(results["tools"])
    print(f"median of {results['runs']} runs, {results['platform']}, {results['cpu_count']} CPUs")
    for key, corpus in results.get("corpora", {}).items():
        print(f"\n## corpus {key}: {len(corpus['files'])} files, {corpus['pages']:,} pages\n")
        print("| | " + " | ".join(names) + " |")
        print("|---|" + "---:|" * len(names))
        for metric, label, fmt in [("time_s", "Time", human_time), ("rss_bytes", "Peak memory", human_size),
                                   ("output_bytes", "Output size", human_size)]:
            cells = [fmt(corpus["tools"][n][metric]) if n in corpus["tools"] and metric in corpus["tools"][n] else "-"
                     for n in names]
            print(f"| {label} | " + " | ".join(cells) + " |")
    for fixture in results["fixtures"]:
        print(f"\n## {fixture['name']} ({fixture['pages']} pages, {fixture['objects']} objects, "
              f"{human_size(fixture['bytes'])})")
        for metric, label, fmt in [("time_s", "Time", human_time), ("rss_bytes", "Peak memory", human_size),
                                   ("output_bytes", "Output size", human_size)]:
            print(f"\n{label}\n")
            print("| Files | Pages | " + " | ".join(names) + " |")
            print("|---:|---:|" + "---:|" * len(names))
            for case in fixture["cases"]:
                cells = []
                for name in names:
                    entry = case["tools"].get(name)
                    cells.append(fmt(entry[metric]) if entry and metric in entry else "-")
                print(f"| {case['count']:,} | {case['pages']:,} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
