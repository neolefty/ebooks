#!/usr/bin/env python3
"""Build an EPUB of "Bahá'í Sacred Writings" from the official bahai.org XHTML.

Pipeline:  official XHTML  ->  clean semantic HTML  ->  pandoc  ->  EPUB 3

The official XHTML carries its structure as CSS classes rather than heading
tags, so this script promotes those classes to real h1/h2/h3 before pandoc
sees the file. Nothing in the text itself is altered; see NOTES.md.

Usage:  ./build.py [--fetch]      (--fetch re-downloads the source first)
"""
import datetime
import re
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_PAGE = "https://www.bahai.org/library/authoritative-texts/bahaullah/bahai-sacred-writings/"
SOURCE_URL = SOURCE_PAGE + "bahai-sacred-writings.xhtml"
SOURCE = HERE / "source" / "bahai-sacred-writings.xhtml"
CLEAN = HERE / "build" / "clean.html"
OUT = HERE.parent / "dist" / "Bahai-Sacred-Writings.epub"
NS = "{http://www.w3.org/1999/xhtml}"


def fetch():
    print("fetching", SOURCE_URL)
    urllib.request.urlretrieve(SOURCE_URL, SOURCE)


def classes(el):
    return set(el.get("class", "").split())


def inner_html(el):
    """Serialize children of el (text + inline tags) as plain HTML."""
    parts = [el.text or ""]
    for child in el:
        parts.append(serialize_inline(child))
        parts.append(child.tail or "")
    return "".join(parts)


def serialize_inline(el):
    tag = el.tag.replace(NS, "")
    cls = classes(el)
    if tag == "a" and "sf" in cls:          # invisible anchor targets
        return ""
    if tag == "a" and "td" in cls:          # passage number, e.g. 1.1
        return f'<span class="pnum">{el.text}</span>'
    if tag == "span" and "kf" in cls:       # first-word styling (drop cap)
        return inner_html(el)
    if tag in ("i", "b", "u"):          # <u> marks transliteration digraphs (Kaw<u>th</u>ar); keep
        return f"<{tag}>{inner_html(el)}</{tag}>"
    raise SystemExit(f"unexpected inline element <{tag} class={cls}>")


def transform(root):
    body = root.find(NS + "body")
    meta = {m.get("name"): m.get("content") for m in root.iter(NS + "meta")}
    out = []
    stats = {"parts": 0, "chapters": 0, "sections": 0, "passages": 0, "paras": 0}
    pending_chapter_number = None

    def walk(el):
        nonlocal pending_chapter_number
        tag = el.tag.replace(NS, "")
        cls = classes(el)
        if tag == "div" and "e" in cls:      # title block + contents list (pandoc regenerates)
            return
        if tag == "div" and "wf" in cls:     # trailing download notice; replaced by colophon
            return
        if tag in ("nav", "hr"):
            return
        if tag == "h2":                      # Part I / Part II
            stats["parts"] += 1
            out.append(f"<h1 class=\"part\">{inner_html(el)}</h1>")
            return
        if tag == "p":
            if "jb" in cls:                  # "Preface"
                out.append(f"<h1>{inner_html(el)}</h1>")
            elif "q" in cls:                 # chapter number
                pending_chapter_number = inner_html(el).strip()
            elif "l" in cls:                 # chapter title
                stats["chapters"] += 1
                out.append(f"<h2>{pending_chapter_number} {inner_html(el)}</h2>")
                pending_chapter_number = None
            elif "s" in cls:                 # section title
                stats["sections"] += 1
                out.append(f"<h3>{inner_html(el)}</h3>")
            else:
                stats["paras"] += 1
                if el.find(f"{NS}a[@class='td']") is not None:
                    stats["passages"] += 1
                out.append(f"<p>{inner_html(el)}</p>")
            return
        for child in el:
            walk(child)

    walk(body)
    out.append(colophon(meta))
    return "\n".join(out), stats, meta


def iso_date(last_modified):
    """'01 May 2026  10:00 a.m. (GMT)' -> '2026-05-01' (pandoc needs ISO)."""
    m = re.match(r"(\d{1,2} \w+ \d{4})", last_modified)
    return datetime.datetime.strptime(m.group(1), "%d %B %Y").date().isoformat() if m else ""


def verify_text(source_text, epub_path):
    """Compare every visible character of the source body against the EPUB."""
    import zipfile

    def visible(html):
        html = re.sub(r"<[^>]+>", "", html)
        html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        return re.sub(r"\s+", " ", html).strip()

    body = source_text[source_text.index("<body"):]
    body = re.sub(r'<div class="e">.*?</nav>', "", body, flags=re.S)      # title + contents list
    body = re.sub(r'<div class="wf">.*', "", body, flags=re.S)           # download notice
    expected = visible(body)

    with zipfile.ZipFile(epub_path) as z:
        names = sorted(n for n in z.namelist() if n.startswith("EPUB/text/ch"))
        got = " ".join(visible(z.read(n).decode("utf-8").split("</head>", 1)[1]) for n in names)
    got = got[: got.index("About This Edition")].strip()
    if expected != got:
        import difflib
        for line in list(difflib.unified_diff(expected.split(" "), got.split(" "), lineterm="", n=3))[:40]:
            print(line)
        raise SystemExit("TEXT MISMATCH between source and EPUB")
    print(f"text verified: {len(expected):,} characters identical to source")


def colophon(meta):
    return f"""
<h1 class="colophon">About This Edition</h1>
<p>This ebook is an unofficial EPUB rendering of <i>Bahá’í Sacred Writings</i>, a compilation of selections from the writings of Bahá’u’lláh and ‘Abdu’l‑Bahá, made from the XHTML edition published by the Bahá’í Reference Library at <a href="{SOURCE_PAGE}">{SOURCE_PAGE}</a>.</p>
<p>The text has not been altered. Only the presentation was changed to suit ebook readers: headings, a table of contents, and paragraph styling. Passage numbers are preserved from the original.</p>
<p>Source last modified: {meta.get("last-modified", "unknown")}.</p>
<p>Copyright © Bahá’í International Community. Used under the terms found at <a href="https://www.bahai.org/legal">www.bahai.org/legal</a>. Not for commercial use.</p>
"""


def main():
    if "--fetch" in sys.argv:
        fetch()
    text = SOURCE.read_text(encoding="utf-8")
    text = re.sub(r"<style>.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text)
    root = ET.fromstring(text)
    html, stats, meta = transform(root)

    CLEAN.parent.mkdir(exist_ok=True)
    CLEAN.write_text(html, encoding="utf-8")
    OUT.parent.mkdir(exist_ok=True)

    # cross-check against the raw source
    src_passages = len(re.findall(r'<a class="td">', text))
    if src_passages != stats["passages"]:
        raise SystemExit(f"passage count mismatch: source {src_passages}, output {stats['passages']}")
    print("structure:", stats)

    cmd = [
        "pandoc", str(CLEAN), "-f", "html", "-t", "epub3", "-o", str(OUT),
        "--metadata-file", str(HERE / "metadata.yaml"),
        "--metadata", f"date={iso_date(meta.get('last-modified', ''))}",
        "--css", str(HERE / "epub.css"),
        "--toc", "--toc-depth=3", "--split-level=2",
    ]
    subprocess.run(cmd, check=True)
    print("wrote", OUT, OUT.stat().st_size, "bytes")
    verify_text(text, OUT)
    if shutil.which("epubcheck"):
        subprocess.run(["epubcheck", "-q", str(OUT)], check=True)
        print("epubcheck: ok")
    else:
        print("epubcheck not installed (brew install epubcheck); skipped validation")


if __name__ == "__main__":
    main()
