
import frappe

def validate_supplier_application(doc, method=None):
    if not doc.supplier_name or not doc.legal_name or not doc.tax_id:
        frappe.throw("Supplier name, legal name, and tax ID are required.")
    duplicate = frappe.db.exists("Supplier Master", {
        "tax_id": doc.tax_id,
        "registration_number": doc.registration_number
    })
    if duplicate:
        frappe.throw("A supplier with the same tax ID and registration number already exists.")
    # TODO: verify mandatory compliance documents based on supplier type/category rules.

def sync_supplier_master(doc, method=None):
    if doc.application_status != "Approved":
        return
    # TODO: create or update Supplier Master; map approved categories and verified documents.

def validate_supplier_master(doc, method=None):
    if doc.supplier_status in {"Suspended", "Debarred", "Blacklisted"}:
        doc.registration_status = doc.registration_status or "Approved"
    # TODO: enforce controlled status transitions via Supplier Status Action only.
