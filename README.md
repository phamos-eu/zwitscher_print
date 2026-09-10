# zwitscher Print

A minimal Frappe app that adds a **`chrome-stamp`** PDF generator.

## Why

The `zwitscher Angebot` print format uses frappe v16's core Chrome PDF generator,
which renders a page as three separately-rasterised strips (header band + body +
footer band) and stacks them with pypdf. Any full-bleed letterhead graphic that
crosses the body/footer boundary is split across two of those strips, and the
sub-pixel position of the seam depends on the Chromium build's text-layout
rounding — which differs between macOS (CoreText) and the Linux
`chrome-headless-shell` used in production. Result: a visible white hairline /
diagonal jog through the bottom-left and bottom-right corner triangles on prod.

## What it does

`chrome-stamp` runs frappe's normal `chrome` generator untouched (page numbers,
repeating footer, pagination all preserved), then merges a single full-page
letterhead PDF **under every page**. The artwork is one object per page, so no
seam can exist, and the output is identical on every OS / Chromium version.

The stamp image is `zwitscher_print/stationery/zwitscher-angebot-a4.png`
(extracted from the original reference Angebot PDF).

## Install

```bash
bench get-app /path/to/zwitscher_print        # or: bench get-app <git-url>
bench --site <site> install-app zwitscher_print
bench --site <site> migrate                    # adds "chrome-stamp" to the Print Format options
```

Then set the print format's **PDF Generator** field to `chrome-stamp`
(the `zwitscher Angebot` format is switched automatically on install).

## Adding another format

Edit `STAMPS` in `zwitscher_print/chrome_stamp.py` and drop the A4 stamp PNG
into `zwitscher_print/stationery/`.
