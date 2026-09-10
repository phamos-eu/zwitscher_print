app_name = "zwitscher_print"
app_title = "zwitscher Print"
app_publisher = "zwitscher IT"
app_description = "Seam-free Angebot PDF: full-page letterhead stamp over frappe's chrome generator."
app_email = "support@zwitscher.it"
app_license = "MIT"

# --- the extra PDF generator -------------------------------------------------
# frappe iterates frappe.get_hooks("pdf_generator") and takes the first hook
# that returns a truthy value. Ours only acts when pdf_generator == "chrome-stamp"
# and returns None otherwise, so ordering vs. frappe / print_designer is moot.
pdf_generator = ["zwitscher_print.chrome_stamp.get_pdf"]

# make "chrome-stamp" selectable on the Print Format "PDF Generator" field, and
# point the zwitscher Angebot format at it.
after_install = "zwitscher_print.setup.after_install"
after_migrate = "zwitscher_print.setup.ensure_pdf_generator_option"
