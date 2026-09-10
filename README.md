# zwitscher Print

A minimal Frappe app that paints a **full-page letterhead behind every page** of
the `zwitscher Angebot` PDF.

## The problem it fixes

Frappe v16's core Chrome PDF generator renders a page as three separately
rasterised strips — header band + body + footer band — stacked with pypdf. A
full-bleed letterhead graphic that crosses the body↔footer boundary is split
across two of those strips, and the sub-pixel position of the seam depends on the
Chromium build's text-layout rounding. macOS (CoreText) and the Linux
`chrome-headless-shell` used in production round differently, so the corner
triangles that look continuous locally show a white hairline / diagonal jog on
production.

## How it works

`zwitscher_print/patch.py` wraps `frappe.utils.pdf.get_chrome_pdf` at boot
(imported from `hooks.py`). After the stock generator produces the PDF for a
registered print format, PyMuPDF's `insert_image(overlay=False)` paints the whole
letterhead as **one image behind every finished page** — without rewriting the
page content, so page numbers / bands / pagination are untouched.

One image object per page ⇒ no seam is possible, and the output is byte-for-byte
independent of OS and Chromium version.

The print format keeps the stock `pdf_generator = "chrome"`. Nothing re-enters
the Chrome pipeline (doing so within one request intermittently corrupts the
page-number footer clones).

* stamp artwork: `zwitscher_print/stationery/zwitscher-angebot-a4.png`
  (extracted from the original reference Angebot PDF — includes the two teal
  margin marks)
* format → stamp mapping: `STAMPS` in `zwitscher_print/chrome_stamp.py`

## Install

```bash
bench get-app /path/to/zwitscher_print          # or a git URL
bench --site <site> install-app zwitscher_print
```

Restart the bench (or `bench --site <site> clear-cache`) so every worker picks up
the wrapper. No Print Format changes are needed — `after_install` makes sure the
`zwitscher Angebot` format is on `pdf_generator = "chrome"`.

## Add another format

Drop `<name>.png` (A4, full bleed) into `zwitscher_print/stationery/` and add a
`"Print Format Name": "<name>.png"` line to `STAMPS`.
