"""Wrap `get_chrome_pdf` to stamp a full-page letterhead behind every page."""

import frappe

_PATCHED_FLAG = "_zwitscher_print_stamped"


def apply():
	import frappe.utils.pdf as pdf_mod

	if getattr(pdf_mod.get_chrome_pdf, _PATCHED_FLAG, False):
		return

	_orig = pdf_mod.get_chrome_pdf

	def get_chrome_pdf(print_format, html, options, output, pdf_generator=None):
		result = _orig(print_format, html, options, output, pdf_generator=pdf_generator)
		if not result or pdf_generator != "chrome":
			return result

		from zwitscher_print.chrome_stamp import resolve_stamp, stamp_pdf_bytes

		stamp_image = resolve_stamp(print_format)
		if not stamp_image:
			return result

		try:
			if isinstance(result, (bytes, bytearray)):
				return stamp_pdf_bytes(bytes(result), stamp_image)

			import io

			from pypdf import PdfReader, PdfWriter

			buf = io.BytesIO()
			result.write(buf)
			stamped = stamp_pdf_bytes(buf.getvalue(), stamp_image)
			fresh = PdfWriter()
			fresh.append_pages_from_reader(PdfReader(io.BytesIO(stamped)))
			return fresh
		except Exception:
			frappe.log_error(title="zwitscher_print: letterhead stamp failed")
			return result

	get_chrome_pdf.__dict__[_PATCHED_FLAG] = True
	pdf_mod.get_chrome_pdf = get_chrome_pdf


def before_request(*args, **kwargs):
	apply()


def before_job(*args, **kwargs):
	apply()
