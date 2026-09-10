app_name = "zwitscher_print"
app_title = "zwitscher Print"
app_publisher = "zwitscher IT"
app_description = "Full-page letterhead stamp for the zwitscher Angebot PDF (seam-free corners)."
app_email = "support@zwitscher.it"
app_license = "MIT"

# Wrap frappe.utils.pdf.get_chrome_pdf on boot. hooks.py is imported early (the
# first frappe.get_hooks call), well before any PDF is generated.
from zwitscher_print.patch import apply as _apply_letterhead_stamp_patch

_apply_letterhead_stamp_patch()

after_install = "zwitscher_print.setup.after_install"
