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

_STATIONERY_DIR = os.path.join(os.path.dirname(__file__), "stationery")

# print format name -> A4 stamp PNG in stationery/
STAMPS = {
	"zwitscher Angebot": "zwitscher-angebot-a4.png",
}


def resolve_stamp(print_format) -> str | None:
	name = getattr(print_format, "name", None)
	if not name and isinstance(print_format, str):
		name = print_format
	fname = STAMPS.get(name or "")
	if not fname:
		return None
	path = os.path.join(_STATIONERY_DIR, fname)
	return path if os.path.exists(path) else None


def stamp_pdf_bytes(pdf_bytes: bytes, stamp_path: str) -> bytes:
	"""Return ``pdf_bytes`` with the letterhead image painted behind every page.

	PyMuPDF's ``insert_image(overlay=False)`` adds the image as a new bottom
	layer without rewriting existing page content, so frappe's pypdf-merged
	header/footer bands and page-number clones stay intact.
	"""
	import fitz  # PyMuPDF — already a bench dependency (used by the print pipeline)

	stamp = open(stamp_path, "rb").read()
	doc = fitz.open(stream=pdf_bytes, filetype="pdf")
	try:
		for page in doc:
			page.insert_image(
				page.rect,
				stream=stamp,
				overlay=False,
				keep_proportion=False,
			)
		return doc.tobytes(deflate=True, garbage=3)
	finally:
		doc.close()
