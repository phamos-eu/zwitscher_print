import frappe

PF_NAME = "zwitscher Angebot"


def after_install():
	"""The letterhead stamp is applied by wrapping the stock `chrome` generator,
	so the print format must stay on `pdf_generator = "chrome"` (not the old
	custom `chrome-stamp` value)."""
	if frappe.db.exists("Print Format", PF_NAME):
		if frappe.db.get_value("Print Format", PF_NAME, "pdf_generator") != "chrome":
			frappe.db.set_value("Print Format", PF_NAME, "pdf_generator", "chrome")
			frappe.clear_cache(doctype="Print Format")
