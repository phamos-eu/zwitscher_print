import frappe

PF_NAME = "zwitscher Angebot"


def after_install():
	if frappe.db.exists("Print Format", PF_NAME):
		if frappe.db.get_value("Print Format", PF_NAME, "pdf_generator") != "chrome":
			frappe.db.set_value("Print Format", PF_NAME, "pdf_generator", "chrome")
			frappe.clear_cache(doctype="Print Format")
