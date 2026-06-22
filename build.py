#!/usr/bin/env python3
"""
build.py — PDF assembler for The Thread

Usage:
    python build.py

Requires:
    pip install weasyprint beautifulsoup4

Outputs:
    output/the-thread.pdf
"""

import os
import re
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

HTML_FILES = [
    ("00-cover.html",                               None,         None),
    ("00-toc.html",                                 None,         None),
    ("00-introduction.html",                        "Introduction", "The Customer's Data Journey"),
    ("ch1-knowing-your-customer.html",              "Chapter 1",  "Knowing Your Customer"),
    ("ch2-capturing-the-request.html",              "Chapter 2",  "Capturing the Request"),
    ("ch3-estimating-with-confidence.html",         "Chapter 3",  "Estimating with Confidence"),
    ("ch4-quoting-for-clarity.html",                "Chapter 4",  "Quoting for Clarity"),
    ("ch5-managing-the-order.html",                 "Chapter 5",  "Managing the Order"),
    ("ch6-delivering-on-the-promise.html",          "Chapter 6",  "Delivering on the Promise"),
    ("ch7-when-things-change.html",                 "Chapter 7",  "When Things Change"),
    ("ch8-the-customers-voice.html",                "Chapter 8",  "The Customer's Voice"),
    ("ch9-measuring-performance.html",              "Chapter 9",  "Measuring Performance"),
    ("ch10-building-a-sales-intelligence-system.html", "Chapter 10", "Building a Sales Intelligence System"),
]

# ---------------------------------------------------------------------------
# HTML transformation
# ---------------------------------------------------------------------------

def strip_px_overrides(html: str) -> str:
    """
    Remove hardcoded pixel width/height from inline <style> blocks.
    These were authored for browser preview (816px = letter at 96dpi)
    but break WeasyPrint's zero-margin page layout.
    Strips: width:816px  min-height:1056px  height:1056px
    """
    def clean_style_block(m):
        tag_open, content, tag_close = m.group(1), m.group(2), m.group(3)
        # Remove the specific px-locked properties
        content = re.sub(r'\bwidth\s*:\s*816px\s*;?', 'width:100%;', content)
        content = re.sub(r'\bmin-height\s*:\s*1056px\s*;?', '', content)
        content = re.sub(r'\bheight\s*:\s*1056px\s*;?', '', content)
        return tag_open + content + tag_close

    return re.sub(
        r'(<style[^>]*>)(.*?)(</style>)',
        clean_style_block,
        html,
        flags=re.DOTALL | re.IGNORECASE
    )


def transform_html(html: str, ch_label: str, ch_title: str) -> str:
    """
    Prepare HTML for natural WeasyPrint pagination:
    - Strip inline px width/height overrides
    - Remove .content-page wrappers (unwrap children)
    - Remove .page-footer divs
    - Inject a .running-header div for the CSS running element
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[ERROR] beautifulsoup4 is required: pip install beautifulsoup4")
        sys.exit(1)

    # Strip pixel-locked styles first (works on all files incl. cover/TOC)
    html = strip_px_overrides(html)

    soup = BeautifulSoup(html, 'html.parser')

    # Remove all page footer divs
    for el in soup.find_all('div', class_='page-footer'):
        el.decompose()

    # Unwrap all content-page containers
    for el in soup.find_all('div', class_='content-page'):
        el.unwrap()

    # Inject running header as first child of <body>
    body = soup.find('body')
    if body and ch_label:
        hdr = soup.new_tag('div', attrs={'class': 'running-header'})
        book = soup.new_tag('span', attrs={'class': 'rh-book'})
        book.string = 'The Thread'
        sep = soup.new_tag('span', attrs={'class': 'rh-sep'})
        sep.string = '  ·  '
        ch = soup.new_tag('span', attrs={'class': 'rh-chapter'})
        ch.string = f'{ch_label}: {ch_title}'
        hdr.append(book); hdr.append(sep); hdr.append(ch)
        body.insert(0, hdr)

    return str(soup)


def transform_all(html: str) -> str:
    """Apply strip_px_overrides to files that don't get the full transform (cover, TOC)."""
    return strip_px_overrides(html)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_weasyprint():
    try:
        import weasyprint
        return weasyprint
    except ImportError:
        print("[ERROR] WeasyPrint is not installed. Run: pip install weasyprint")
        sys.exit(1)


def validate_files():
    missing = [f for name, _, _ in HTML_FILES if not (HTML_DIR / name).exists()
               and missing.append(name) is None]
    missing = []
    for name, _, _ in HTML_FILES:
        if not (HTML_DIR / name).exists():
            missing.append(str(HTML_DIR / name))
    if missing:
        print("[ERROR] Missing HTML files:")
        for m in missing:
            print(f"        {m}")
        sys.exit(1)


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
    for i, (name, ch_label, ch_title) in enumerate(HTML_FILES, 1):
        path = HTML_DIR / name
        label = name.replace(".html", "")
        print(f"  [{i:02d}/{len(HTML_FILES)}] Rendering {label} ...", end="", flush=True)
        t0 = time.time()

        raw_html = path.read_text(encoding='utf-8')

        if ch_label is not None:
            # Chapter files: full transform (strip px, unwrap content-page, add header)
            html = transform_html(raw_html, ch_label, ch_title)
        else:
            # Cover and TOC: strip px overrides only
            html = transform_all(raw_html)

        doc = weasyprint.HTML(string=html, base_url=str(path)).render()

        elapsed = time.time() - t0
        print(f" {len(doc.pages)}pp ({elapsed:.1f}s)")
        documents.append(doc)

    print()
    print("  Assembling pages ...", end="", flush=True)
    t0 = time.time()

    all_pages = []
    for doc in documents:
        all_pages.extend(doc.pages)

    combined = documents[0].copy(pages=all_pages)
    combined.write_pdf(target=str(OUTPUT_FILE))

    elapsed = time.time() - t0
    size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)

    print(f" done ({elapsed:.1f}s)")
    print()
    print(f"  Output : {OUTPUT_FILE}")
    print(f"  Pages  : {len(all_pages)}")
    print(f"  Size   : {size_mb:.2f} MB")
    print()


if __name__ == "__main__":
    build()
