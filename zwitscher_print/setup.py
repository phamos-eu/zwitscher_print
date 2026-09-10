import frappe

PF_NAME = "zwitscher Angebot"
GENERATOR = "chrome-stamp"


def ensure_pdf_generator_option():
	"""Append `chrome-stamp` to the Print Format `pdf_generator` Select options
	via a Property Setter (idempotent). Safe to run on every migrate."""
	meta = frappe.get_meta("Print Format")
	field = meta.get_field("pdf_generator")
	if not field:
		return

	options = [o for o in (field.options or "").split("\n") if o != ""]
	if GENERATOR in options:
		return

	options.append(GENERATOR)
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	make_property_setter(
		"Print Format",
		"pdf_generator",
		"options",
		"\n".join(options),
		"Text",
		validate_fields_for_doctype=False,
	)
	frappe.clear_cache(doctype="Print Format")


def after_install():
	ensure_pdf_generator_option()
	if frappe.db.exists("Print Format", PF_NAME):
		frappe.db.set_value("Print Format", PF_NAME, "pdf_generator", GENERATOR)
		frappe.clear_cache(doctype="Print Format")
