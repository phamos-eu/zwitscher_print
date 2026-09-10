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

`zwitscher_print/patch.py` wraps `frappe.utils.pdf.get_chrome_pdf`
(via the `before_request` / `before_job` hooks, plus a module-level call for cold
workers). After the stock generator produces the PDF for a registered print
format, the whole letterhead is placed as **one image behind every finished
page** with Pillow + pypdf (both frappe dependencies — no PyMuPDF) — the content
page is only referenced, never rewritten, so page numbers / bands / pagination
are untouched.

One image object per page ⇒ no seam is possible, and the output is byte-for-byte
independent of OS and Chromium version.

The print format keeps the stock `pdf_generator = "chrome"`. Nothing re-enters
the Chrome pipeline (doing so within one request intermittently corrupts the
page-number footer clones).

* stamp artwork is loaded from a **public File** named `zwitscher-angebot-a4.png`
  (installed by `install_prod.py`, like the web fonts — this is what makes it
  work on Frappe Cloud). `zwitscher_print/stationery/…` holds a dev fallback.
* format → stamp mapping: `STAMPS` in `zwitscher_print/chrome_stamp.py`

## Install (self-hosted bench)

```bash
bench get-app /path/to/zwitscher_print          # or a git URL
bench --site <site> install-app zwitscher_print
bench restart
# then push the print format + assets (incl. the stamp File):
bench --site <site> console
>>> PF_DIR="/path/to/zwitscher_pf_wip"; exec(open(PF_DIR+"/install_prod.py").read())
```

## Install (Frappe Cloud)

1. Push this app to a Git repo (GitHub/GitLab).
2. Bench group → **Apps** → **Add App** → from your repo/branch → **Add**.
3. **Deploy** the new build, then **Add to site** on your site.
4. Open the site's **Console** and run `install_prod.py` (as above) — it uploads
   the stamp image + fonts as public Files and points the format at `chrome`.
5. Sanity check: paste `fc_diag.py` into the Console — the last line should read
   `images per page = [1, 1, …]  <-- OK`.

`after_install` makes sure the `zwitscher Angebot` format is on
`pdf_generator = "chrome"`; there are no other Print Format changes.

## Add another format

Drop `<name>.png` (A4, full bleed) into `zwitscher_print/stationery/` and add a
`"Print Format Name": "<name>.png"` line to `STAMPS`.
# zwitscher_print
