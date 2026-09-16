# ebooks

Reproducible EPUB builds of freely licensed texts. One directory per book,
each with its own `build.py` and `NOTES.md`; finished EPUBs land in `dist/`.

| Book | Source | Build |
|---|---|---|
| Bahá’í Sacred Writings | bahai.org Reference Library (official XHTML) | `cd bahai-sacred-writings && ./build.py` |

## General process (what has worked)

1. **Look for an official structured download before scraping.** The
   bahai.org library offers PDF, DOCX and single-file XHTML for each title.
   Single-file XHTML is the best input: no pagination artefacts, full
   diacritics, and the structure is recoverable even when it is expressed as
   CSS classes instead of heading tags.
2. **Preprocess to clean semantic HTML** with a small stdlib-only Python
   script (headings, paragraph numbers, drop decorative elements, add a
   colophon). Keep the script strict: fail on any inline element it has not
   been told about, so a source change cannot silently drop markup.
3. **pandoc → EPUB 3** with `--toc --split-level=2`, a metadata YAML and a
   small CSS file. pandoc is installed via Homebrew.
4. **Verify**: passage count, and a full visible-text diff of source body vs
   EPUB body (built into `build.py`); then `epubcheck` on the result.
5. **Copyright**: record the licence terms and source URL in `NOTES.md` and in
   the EPUB's colophon and Dublin Core metadata.

Tools: pandoc (`brew install pandoc`), epubcheck (`brew install epubcheck`),
Python 3 (stdlib only). Calibre is not required, but useful for previewing
and for converting onward to Kindle formats.

## Licence

Two different things live in this repository:

- **The texts** in `*/source/` and `dist/` are not ours. *Bahá’í Sacred
  Writings* is Copyright © Bahá’í International Community and is used here
  under the terms at <https://www.bahai.org/legal>: the copyright notice must
  accompany any use, the meaning of the text must remain unaltered, and
  commercial use requires their prior permission. This is an unofficial
  rendering, not endorsed by the Bahá’í International Community. If you
  represent the copyright holder and have any concern, open an issue and the
  file will be taken down promptly.
- **Everything else** (build scripts, stylesheets, notes, and this README) is
  dedicated to the public domain under [CC0 1.0](LICENSE). Use it however you
  like; no attribution required.

## Credits

Built by Bill Baker with [Claude Code](https://claude.com/claude-code)
(Claude Fable 5.1), which investigated the source formats, wrote the build
pipeline and verification, and drafted these notes.
