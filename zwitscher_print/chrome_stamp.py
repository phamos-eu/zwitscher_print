"""Full-page letterhead stamp for the zwitscher Angebot PDF.

The stock v16 Chrome generator renders each page as three separately-rasterised
strips (header band + body + footer band) stacked with pypdf. A full-bleed
letterhead graphic that crosses the body/footer boundary is split between two of
those strips, and the sub-pixel seam position depends on the Chromium build's
text-layout rounding (macOS CoreText vs. Linux chrome-headless-shell) — hence the
visible hairline through the bottom corner triangles on production.

`patch.py` wraps `get_chrome_pdf` and calls `stamp_pdf_bytes()` here to paint the
whole letterhead as one image behind every finished page. One object per page =>
no seam, identical on every OS / Chromium version.
"""

import os

import frappe

# package fallback copy (used in dev; on a real install the image is a File doc)
_STATIONERY_DIR = os.path.join(os.path.dirname(__file__), "stationery")

# print format name -> stamp image basename (a public File named exactly this,
# i.e. reachable at /files/<basename>, installed by install_prod.py; the same
# name is also shipped in stationery/ as a dev fallback).
STAMPS = {
	"zwitscher Angebot": "zwitscher-angebot-a4.png",
}


def resolve_stamp(print_format) -> bytes | None:
	"""Return the stamp image bytes for a print format, or None.

	Looks for a public File named exactly <basename> first (works on Frappe
	Cloud, where the app package may not ship data files), then the copy bundled
	in the app under stationery/.
	"""
	name = getattr(print_format, "name", None)
	if not name and isinstance(print_format, str):
		name = print_format
	basename = STAMPS.get(name or "")
	if not basename:
		return None

	file_url = frappe.db.get_value("File", {"file_name": basename, "is_private": 0}, "file_url")
	if file_url:
		try:
			path = frappe.utils.get_files_path(basename, is_private=0)
			if os.path.exists(path):
				return open(path, "rb").read()
			# File row exists but bytes are elsewhere (e.g. S3) — read via the doc
			return frappe.get_doc("File", {"file_name": basename, "is_private": 0}).get_content()
		except Exception:
			frappe.log_error(title="zwitscher_print: could not read stamp File")

	pkg = os.path.join(_STATIONERY_DIR, basename)
	if os.path.exists(pkg):
		return open(pkg, "rb").read()

	return None


def stamp_pdf_bytes(pdf_bytes: bytes, stamp_image: bytes) -> bytes:
	"""Return ``pdf_bytes`` with ``stamp_image`` painted behind every page.

	PyMuPDF's ``insert_image(overlay=False)`` adds the image as a new bottom
	layer without rewriting existing page content, so frappe's pypdf-merged
	header/footer bands and page-number clones stay intact.
	"""
	import fitz  # PyMuPDF — already a bench dependency (used by the print pipeline)

	doc = fitz.open(stream=pdf_bytes, filetype="pdf")
	try:
		for page in doc:
			page.insert_image(
				page.rect,
				stream=stamp_image,
				overlay=False,
				keep_proportion=False,
			)
		return doc.tobytes(deflate=True, garbage=3)
	finally:
		doc.close()
