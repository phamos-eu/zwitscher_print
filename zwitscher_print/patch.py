"""Wrap `frappe.utils.pdf.get_chrome_pdf` so that the finished Chrome PDF for a
registered print format gets a full-page letterhead painted behind every page.

Why a wrapper and not a `pdf_generator` hook:
  * the print format stays on the stock `pdf_generator = "chrome"`, so the
    normal single-pass pipeline runs (page numbers, bands, pagination);
  * we never call `get_chrome_pdf` a second time from inside the request —
    re-entering frappe's chrome pipeline within one request intermittently
    corrupts the page-number footer clones.

`frappe.call` resolves the `pdf_generator` hook by dotted string at call time,
so replacing the attribute on the module is enough for the desk PDF button,
`frappe.get_print(..., as_pdf=True)` and `attach_print` alike.
"""

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

		stamp_path = resolve_stamp(print_format)
		if not stamp_path:
			return result

		try:
			if isinstance(result, (bytes, bytearray)):
				return stamp_pdf_bytes(bytes(result), stamp_path)
			# result is a PdfWriter (output was passed in): re-stamp its pages
			import io

			from pypdf import PdfReader, PdfWriter

			buf = io.BytesIO()
			result.write(buf)
			stamped = stamp_pdf_bytes(buf.getvalue(), stamp_path)
			result.pages.clear() if hasattr(result, "pages") else None
			new = PdfReader(io.BytesIO(stamped))
			fresh = PdfWriter()
			fresh.append_pages_from_reader(new)
			return fresh
		except Exception:
			frappe.log_error(title="zwitscher_print: letterhead stamp failed")
			return result

	get_chrome_pdf.__dict__[_PATCHED_FLAG] = True
	pdf_mod.get_chrome_pdf = get_chrome_pdf
