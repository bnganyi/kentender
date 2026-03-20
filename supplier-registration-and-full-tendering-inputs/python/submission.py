
import frappe
from frappe.utils import now_datetime

def validate_submission(doc, method=None):
    if not doc.tender or not doc.supplier:
        frappe.throw("Tender and supplier are required.")
    supplier_status = frappe.db.get_value("Supplier Master", doc.supplier, "supplier_status")
    if supplier_status in {"Suspended", "Debarred", "Blacklisted"}:
        frappe.throw("This supplier is not eligible to submit a bid.")
    # TODO: validate category eligibility, security rules, required attachments, and deadline.

def enforce_submission_lock(doc, method=None):
    tender = frappe.get_doc("Tender", doc.tender)
    if tender.closing_datetime and now_datetime() >= tender.closing_datetime:
        if doc.submission_status in {"Draft", "Submitted"}:
            doc.submission_status = "Locked"
        doc.read_only_after_deadline = 1
        doc.sealed_flag = 1
