"""Full-page letterhead stamp for the zwitscher Angebot PDF.

The stock v16 Chrome generator renders each page as three separately-rasterised
strips (header band + body + footer band) stacked with pypdf. A full-bleed
letterhead graphic that crosses the body/footer boundary is split between two of
those strips, and the sub-pixel seam position depends on the Chromium build's
text-layout rounding (macOS CoreText vs. Linux chrome-headless-shell) — hence the
visible hairline through the bottom corner triangles on production.

`patch.py` wraps `get_chrome_pdf` and calls `stamp_pdf_bytes()` here to place the
whole letterhead as one image behind every finished page. One object per page =>
no seam, identical on every OS / Chromium version.

Only Pillow + pypdf are used (both are frappe dependencies) — no PyMuPDF, which
is not installed on a stock bench / Frappe Cloud.
"""

import io
import os

import frappe

# package fallback copy (used in dev; on a real install the image is a File doc)
_STATIONERY_DIR = os.path.join(os.path.dirname(__file__), "stationery")

# print format name -> stamp image basename. Installed by install_prod.py as a
# public File named exactly this (reachable at /files/<basename>); the same file
# is shipped in stationery/ as a dev fallback.
STAMPS = {
	"zwitscher Angebot": "zwitscher-angebot-a4.png",
}


def resolve_stamp(print_format) -> bytes | None:
	"""Stamp image bytes for a print format, or None.

	Public File named <basename> first (works on Frappe Cloud regardless of how
	the app package is built), then the copy bundled under stationery/.
	"""
	name = getattr(print_format, "name", None)
	if not name and isinstance(print_format, str):
		name = print_format
	basename = STAMPS.get(name or "")
	if not basename:
		return None

	if frappe.db.get_value("File", {"file_name": basename, "is_private": 0}, "name"):
		try:
			path = frappe.utils.get_files_path(basename, is_private=False)
			if os.path.exists(path):
				return open(path, "rb").read()
			return frappe.get_doc("File", {"file_name": basename, "is_private": 0}).get_content()
		except Exception:
			frappe.log_error(title="zwitscher_print: could not read stamp File")

	pkg = os.path.join(_STATIONERY_DIR, basename)
	if os.path.exists(pkg):
		return open(pkg, "rb").read()

	return None


def _stamp_page_pdf(image_bytes: bytes, width_pt: float, height_pt: float) -> bytes:
	"""A one-page PDF exactly ``width_pt`` x ``height_pt`` holding the image at
	full bleed. Pillow writes the PDF; the page size is the image size / DPI, so
	we pick the DPI that makes it land on the target point size."""
	from PIL import Image

	im = Image.open(io.BytesIO(image_bytes))
	if im.mode not in ("RGB", "L"):
		im = im.convert("RGB")
	# points = px / dpi * 72  ->  dpi = px * 72 / points
	dpi_x = im.width * 72.0 / width_pt
	dpi_y = im.height * 72.0 / height_pt
	buf = io.BytesIO()
	im.save(buf, format="PDF", resolution=min(dpi_x, dpi_y), dpi=(dpi_x, dpi_y))
	return buf.getvalue()


def stamp_pdf_bytes(pdf_bytes: bytes, image_bytes: bytes) -> bytes:
	"""Return ``pdf_bytes`` with ``image_bytes`` placed behind every page."""
	from pypdf import PdfReader, PdfWriter

	base = PdfReader(io.BytesIO(pdf_bytes))
	first = base.pages[0]
	stamp_pdf = _stamp_page_pdf(
		image_bytes, float(first.mediabox.width), float(first.mediabox.height)
	)

	writer = PdfWriter()
	for page in base.pages:
		# the letterhead page is the canvas; the chrome content is merged on top,
		# so the content page (footer bands, page-number clones) is only
		# referenced, never rewritten.
		canvas = PdfReader(io.BytesIO(stamp_pdf)).pages[0]
		canvas.merge_page(page, over=True)
		writer.add_page(canvas)

	out = io.BytesIO()
	writer.write(out)
	return out.getvalue()
