import frappe

# formats that must stay on the stock chrome generator for the wrapper to fire
_FORMATS = ["zwitscher Angebot", "zwitscher Lieferschein"]


def after_install():
	changed = False
	for name in _FORMATS:
		if frappe.db.exists("Print Format", name):
			if frappe.db.get_value("Print Format", name, "pdf_generator") != "chrome":
				frappe.db.set_value("Print Format", name, "pdf_generator", "chrome")
				changed = True
	if changed:
		frappe.clear_cache(doctype="Print Format")
