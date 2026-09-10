"""zwitscher_print — Frappe Cloud diagnostic.
Run in the site's bench console (Frappe Cloud dashboard -> site -> Console, or
`bench --site <site> console`):

    exec(open('/home/frappe/frappe-bench/apps/zwitscher_print/fc_diag.py').read())

...or just paste the body. It checks every link in the chain.
"""
import os

import frappe

print("== app / hooks ==")
print("  installed on site:", "zwitscher_print" in frappe.get_installed_apps())
try:
    import zwitscher_print

    print("  package version :", getattr(zwitscher_print, "__version__", "?"),
          "  path:", os.path.dirname(zwitscher_print.__file__))
except Exception as e:
    print("  package import FAILED:", e)

print("  before_request hooks:", frappe.get_hooks("before_request"))
print("  before_job hooks    :", frappe.get_hooks("before_job"))

print("\n== patch applied? ==")
import frappe.utils.pdf as _P

print("  get_chrome_pdf patched (now):",
      getattr(_P.get_chrome_pdf, "_zwitscher_print_stamped", False))
try:
    frappe.get_attr("zwitscher_print.patch.apply")()
    print("  after manual apply()      :",
          getattr(_P.get_chrome_pdf, "_zwitscher_print_stamped", False))
except Exception as e:
    print("  manual apply() FAILED:", e)

print("\n== stamp image ==")
try:
    from zwitscher_print.chrome_stamp import STAMPS, _STATIONERY_DIR, resolve_stamp

    print("  STAMPS map          :", STAMPS)
    for name, base in STAMPS.items():
        row = frappe.db.get_value(
            "File", {"file_name": base, "is_private": 0}, ["file_url", "file_size"]
        )
        pkg = os.path.join(_STATIONERY_DIR, base)
        b = resolve_stamp(name)
        print(f"  '{name}':")
        print(f"     File(public) row : {row}")
        print(f"     package fallback : {pkg}  exists={os.path.exists(pkg)}")
        print(f"     resolve_stamp()  : {len(b) if b else None} bytes")
except Exception as e:
    import traceback

    traceback.print_exc()

print("\n== print format ==")
pf = frappe.db.get_value(
    "Print Format", "zwitscher Angebot", ["pdf_generator", "disabled"], as_dict=True
)
print("  zwitscher Angebot:", pf)

print("\n== live render test ==")
try:
    from frappe.translate import print_language

    q = frappe.get_all("Quotation", limit=1, pluck="name")
    if q:
        with print_language("de"):
            pdf = frappe.get_print(
                "Quotation", q[0], print_format="zwitscher Angebot",
                as_pdf=True, pdf_generator="chrome",
            )
        import fitz

        d = fitz.open(stream=pdf, filetype="pdf")
        per_page = [len(p.get_images()) for p in d]
        print(f"  {q[0]}: {d.page_count} pages, images per page = {per_page}",
              "  <-- OK" if all(per_page) else "  <-- STAMP MISSING")
    else:
        print("  no Quotation to test with")
except Exception as e:
    import traceback

    traceback.print_exc()

print("\n== recent zwitscher_print errors ==")
for e in frappe.get_all(
    "Error Log",
    filters={"method": ["like", "%zwitscher_print%"]},
    fields=["creation", "method"],
    order_by="creation desc",
    limit=5,
):
    print("  ", e.creation, e.method)
