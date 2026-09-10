"""Place a full-page letterhead image behind every page of a finished PDF.

Uses only Pillow + pypdf (both frappe dependencies).
"""

import io
import os

import frappe

_STATIONERY_DIR = os.path.join(os.path.dirname(__file__), "stationery")

# print format name -> stamp image basename (a public File named exactly this,
# with a copy in stationery/ as a fallback). The zwitscher letterhead is the
# same artwork for every document type, so they share one image.
STAMPS = {
	"zwitscher Angebot": "zwitscher-angebot-a4.png",
	"zwitscher Lieferschein": "zwitscher-angebot-a4.png",
}


def resolve_stamp(print_format) -> bytes | None:
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
	"""One-page PDF exactly width_pt x height_pt holding the image at full bleed."""
	from PIL import Image

	im = Image.open(io.BytesIO(image_bytes))
	if im.mode not in ("RGB", "L"):
		im = im.convert("RGB")
	dpi_x = im.width * 72.0 / width_pt
	dpi_y = im.height * 72.0 / height_pt
	buf = io.BytesIO()
	im.save(buf, format="PDF", resolution=min(dpi_x, dpi_y), dpi=(dpi_x, dpi_y))
	return buf.getvalue()


def stamp_pdf_bytes(pdf_bytes: bytes, image_bytes: bytes) -> bytes:
	from pypdf import PdfReader, PdfWriter

	base = PdfReader(io.BytesIO(pdf_bytes))
	first = base.pages[0]
	stamp_pdf = _stamp_page_pdf(
		image_bytes, float(first.mediabox.width), float(first.mediabox.height)
	)

	writer = PdfWriter()
	for page in base.pages:
		canvas = PdfReader(io.BytesIO(stamp_pdf)).pages[0]
		canvas.merge_page(page, over=True)
		writer.add_page(canvas)

	out = io.BytesIO()
	writer.write(out)
	return out.getvalue()
