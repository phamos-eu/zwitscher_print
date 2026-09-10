# Frappe Cloud diagnostic for the letterhead stamp.
#   bench --site <site> console
#   >>> exec(open("apps/zwitscher_print/fc_diag.py").read())

import io

import frappe

print("app installed :", "zwitscher_print" in frappe.get_installed_apps())
print("before_request:", frappe.get_hooks("before_request"))

import frappe.utils.pdf as _P

frappe.get_attr("zwitscher_print.patch.apply")()
print("patched       :", getattr(_P.get_chrome_pdf, "_zwitscher_print_stamped", False))

from zwitscher_print.chrome_stamp import STAMPS, resolve_stamp

for name, base in STAMPS.items():
	url = frappe.db.get_value("File", {"file_name": base, "is_private": 0}, "file_url")
	got = resolve_stamp(name)
	print(f"stamp {name!r}: File={url}  bytes={len(got) if got else None}")

print("print format  :", frappe.db.get_value(
	"Print Format", "zwitscher Angebot", ["pdf_generator", "disabled"], as_dict=True))

from frappe.translate import print_language
from pypdf import PdfReader

q = frappe.get_all("Quotation", limit=1, pluck="name")
if q:
	with print_language("de"):
		pdf = frappe.get_print("Quotation", q[0], print_format="zwitscher Angebot",
			as_pdf=True, pdf_generator="chrome")
	pages = PdfReader(io.BytesIO(pdf)).pages
	imgs = [len(p.images) for p in pages]
	print(f"render {q[0]}: {len(pages)} pages, images/page={imgs}",
		"<-- OK" if all(imgs) else "<-- STAMP MISSING")

for e in frappe.get_all("Error Log", filters={"method": ["like", "%zwitscher_print%"]},
	fields=["creation", "method"], order_by="creation desc", limit=5):
	print("error log:", e.creation, e.method)
