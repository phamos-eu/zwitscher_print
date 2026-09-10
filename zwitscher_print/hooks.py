app_name = "zwitscher_print"
app_title = "zwitscher Print"
app_publisher = "phamos GmbH"
app_description = "Full-page letterhead stamp for the zwitscher Angebot PDF (seam-free corners)."
app_email = "support@phamos.eu"
app_license = "MIT"

from zwitscher_print.patch import apply as _apply_letterhead_stamp_patch

_apply_letterhead_stamp_patch()

before_request = ["zwitscher_print.patch.before_request"]
before_job = ["zwitscher_print.patch.before_job"]

after_install = "zwitscher_print.setup.after_install"
