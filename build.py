#!/usr/bin/env python3
"""
build.py — PDF assembler for The Thread

Usage:
    python build.py

Requires:
    pip install weasyprint

Outputs:
    output/the-thread.pdf
"""

import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.resolve()
HTML_DIR = ROOT / "html"
OUTPUT_DIR = ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "the-thread.pdf"

# Ordered list of HTML files — front matter first, then chapters in sequence
HTML_FILES = [
    "00-cover.html",
    "00-toc.html",
    "00-introduction.html",
    "ch1-knowing-your-customer.html",
    "ch2-capturing-the-request.html",
    "ch3-estimating-with-confidence.html",
    "ch4-quoting-for-clarity.html",
    "ch5-managing-the-order.html",
    "ch6-delivering-on-the-promise.html",
    "ch7-when-things-change.html",
    "ch8-the-customers-voice.html",
    "ch9-measuring-performance.html",
    "ch10-building-a-sales-intelligence-system.html",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_weasyprint():
    try:
        import weasyprint
        return weasyprint
    except ImportError:
        print("[ERROR] WeasyPrint is not installed.")
        print("        Run: pip install weasyprint")
        sys.exit(1)


def validate_files():
    missing = []
    for name in HTML_FILES:
        path = HTML_DIR / name
        if not path.exists():
            missing.append(str(path))
    if missing:
        print("[ERROR] Missing HTML files:")
        for m in missing:
            print(f"        {m}")
        sys.exit(1)


def file_url(path: Path) -> str:
    """Convert a Path to a file:// URL WeasyPrint can resolve CSS from."""
    return path.as_uri()


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    weasyprint = check_weasyprint()
    validate_files()

    OUTPUT_DIR.mkdir(exist_ok=True)

    print()
    print("  The Thread — PDF Build")
    print("  " + "─" * 44)

    documents = []
    for i, name in enumerate(HTML_FILES, 1):
        path = HTML_DIR / name
        label = name.replace(".html", "")
        print(f"  [{i:02d}/{len(HTML_FILES)}] Rendering {label} ...", end="", flush=True)
        t0 = time.time()
        doc = weasyprint.HTML(filename=str(path)).render()
        elapsed = time.time() - t0
        page_count = len(doc.pages)
        print(f" {page_count}pp ({elapsed:.1f}s)")
        documents.append(doc)

    print()
    print("  Assembling pages ...", end="", flush=True)
    t0 = time.time()

    # Combine all rendered documents into a single page list
    all_pages = []
    for doc in documents:
        all_pages.extend(doc.pages)

    # Write using the first document as the base (carries metadata/fonts)
    combined = documents[0].copy(pages=all_pages)
    combined.write_pdf(target=str(OUTPUT_FILE))

    elapsed = time.time() - t0
    size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    total_pages = len(all_pages)

    print(f" done ({elapsed:.1f}s)")
    print()
    print(f"  Output : {OUTPUT_FILE}")
    print(f"  Pages  : {total_pages}")
    print(f"  Size   : {size_mb:.2f} MB")
    print()


if __name__ == "__main__":
    build()
