"""`chrome-stamp` PDF generator.

Runs frappe's core `chrome` generator unchanged, then merges a single full-page
letterhead PDF *under* every page. One image object per page => the body/footer
PDF-merge seam that split the corner triangles can no longer exist, and the
result is identical across operating systems and Chromium builds.
"""

import io
import os

import frappe

GENERATOR = "chrome-stamp"
_STATIONERY_DIR = os.path.join(os.path.dirname(__file__), "stationery")

# print format name -> A4 stamp PNG in stationery/
STAMPS = {
	"zwitscher Angebot": "zwitscher-angebot-a4.png",
}

# cache: (stamp_file, width_pt, height_pt) -> one-page stamp PDF bytes
_stamp_cache: dict = {}


def _stamp_pdf(stamp_file: str, width: float, height: float) -> bytes:
	key = (stamp_file, round(width, 2), round(height, 2))
	if key not in _stamp_cache:
		import fitz  # PyMuPDF, already a bench dependency (used by the print pipeline)

		path = os.path.join(_STATIONERY_DIR, stamp_file)
		doc = fitz.open()
		page = doc.new_page(width=width, height=height)
		page.insert_image(fitz.Rect(0, 0, width, height), filename=path, keep_proportion=False)
		_stamp_cache[key] = doc.tobytes()
		doc.close()
	return _stamp_cache[key]


def _resolve_stamp(print_format) -> str | None:
	name = getattr(print_format, "name", None) or (print_format if isinstance(print_format, str) else None)
	return STAMPS.get(name)


def get_pdf(print_format=None, html=None, options=None, output=None, pdf_generator=None):
	if pdf_generator != GENERATOR:
		return None

	from pypdf import PdfReader, PdfWriter

	from frappe.utils.pdf import get_chrome_pdf

	options = options or {}

	# 1. produce the base PDF through frappe's normal chrome pipeline
	base_bytes = get_chrome_pdf(print_format, html, options, None, pdf_generator="chrome")
	if not base_bytes:
		# chrome generator produced nothing -> let the caller fall through
		return None

	reader = PdfReader(io.BytesIO(base_bytes))

	stamp_file = _resolve_stamp(print_format)
	writer = PdfWriter()

	if stamp_file and os.path.exists(os.path.join(_STATIONERY_DIR, stamp_file)):
		first = reader.pages[0]
		w = float(first.mediabox.width)
		h = float(first.mediabox.height)
		stamp_page = PdfReader(io.BytesIO(_stamp_pdf(stamp_file, w, h))).pages[0]
		for page in reader.pages:
			# stamp goes UNDER the chrome content (which is transparent except
			# where it actually paints text / rules / the teal table header)
			page.merge_page(stamp_page, over=False)
			writer.add_page(page)
	else:
		frappe.log_error(
			f"zwitscher_print: no stationery stamp for print format {print_format!r}; "
			"returning un-stamped chrome PDF",
			"chrome-stamp",
		)
		for page in reader.pages:
			writer.add_page(page)

	password = options.get("password")
	if password:
		writer.encrypt(password)

	if output is not None:
		output.append_pages_from_reader(reader)
		return output

	buf = io.BytesIO()
	writer.write(buf)
	return buf.getvalue()
