# Bahá’í Sacred Writings — build notes

Source page: https://www.bahai.org/library/authoritative-texts/bahaullah/bahai-sacred-writings/
Official downloads on that page: PDF (3.6 MB), DOCX (665 kB), XHTML (1.2 MB).
Source file used: `source/bahai-sacred-writings.xhtml`, last modified 01 May 2026
(the file records this in a `<meta name="last-modified">` tag). Re-fetch with
`./build.py --fetch`.

## Licence

https://www.bahai.org/legal grants a limited, non-exclusive licence to use,
reproduce, distribute, link and display content, provided:

- the intent, character, nature and meaning of the content is unaltered;
- "Copyright © Bahá’í International Community" accompanies any use;
- commercial use needs prior permission (termsofuse@bahai.org);
- they may withdraw permission at any time.

The EPUB therefore carries the copyright line, the source URL and a link to
the terms in both its colophon page and its Dublin Core metadata, and the build
verifies the text is character-for-character identical to the source.

## Why not the DOCX or a web → markdown → Google Doc route

The DOCX uses custom paragraph styles rather than Word heading styles, so pandoc
sees one giant chapter with no TOC. Scraping the 19 web chapters and going via
Google Docs adds steps and loses the passage numbers. The XHTML is a single
file with everything needed.

## Anatomy of the official XHTML (as of 2026-05-01)

Structure is expressed with obfuscated CSS classes, not heading tags. The only
`<h3>` elements are in the front-matter contents list, which `build.py` drops
because pandoc regenerates a TOC.

| Meaning | Markup in source | Becomes |
|---|---|---|
| title block + contents list | `<div class="e">` … `<nav>` | dropped |
| "Preface" heading | `<p class="id ub jb">` | `<h1>` |
| Part I / Part II | `<h2 class="c g">` | `<h1 class="part">` |
| chapter number | `<p class="c q">` | prefixed to the chapter title |
| chapter title | `<p class="ub c l">` | `<h2>` "1 God and His Manifestations" |
| decorative rule after chapter title | `<hr class="fc">` (renders `* * *`) | dropped |
| section title | `<p class="ub s">` | `<h3>` |
| passage number (1.1, 1.2 …) | `<a class="td">` | `<span class="pnum">` |
| first word of a passage (drop-cap styling) | `<span class="kf">` | unwrapped |
| invisible anchor targets | `<a class="sf" id="…">` | dropped |
| italics / bold | `<i>`, `<b>` | kept |
| transliteration digraphs, e.g. Kaw<u>th</u>ar | `<u>` | kept (this underline is meaningful, not decoration) |
| trailing "downloaded from…" notice | `<div class="wf">` | replaced by the colophon |

Counts to expect: 2 parts, 19 chapters, 129 sections, 1687 passages, 1692
paragraphs (the extra 5 are the preface). No footnotes, tables or images.

`build.py` raises on any inline element not in the table above, so if bahai.org
changes their markup the build fails loudly instead of losing text.

## pandoc settings

- `-f html -t epub3 --toc --toc-depth=3 --split-level=2`: one XHTML file per
  chapter (24 files including title page, preface, two part pages, colophon).
- Date must be ISO; the source's "01 May 2026 10:00 a.m. (GMT)" is converted.
- Identifier is pinned to the source URL in `metadata.yaml` so rebuilds keep
  the same identity (pandoc otherwise mints a random UUID every run).
- `epub.css`: centred headings, indented justified paragraphs, small grey
  passage numbers.

## Cover

The source has no cover image, so `cover.py` generates one with ImageMagick
and `build.py` passes it to pandoc as `--epub-cover-image`. Design follows
the 2026 hardcover: dark blue linen, gold serif capitals, no author (the
title page inside credits both Bahá’u’lláh and ‘Abdu’l‑Bahá). The title is
stacked one word per line and set large so it survives as a thumbnail.
Font: macOS's bundled Hoefler Text; pass another font path as an argument
to `cover.py` on other systems. Noise seeds are fixed so rebuilds are
byte-identical.

## Ideas for refinement

- Two-level TOC only (`--toc-depth=2`) if 152 entries feels too busy on a
  reader; the h3 sections stay in the text either way.
- Kindle: `ebook-convert dist/Bahai-Sacred-Writings.epub out.azw3` with Calibre.
- The same script skeleton should work for other bahai.org Reference Library
  titles, since they share the XHTML generator; the class names may differ.
