import frappe
from frappe import _

def validate_termination_rules(doc, method=None):
    if not getattr(doc, "termination_reason", None):
        frappe.throw(_("Termination reason is required."))
    if getattr(doc, "workflow_state", None) in ("Pending Accounting Officer Approval","Approved","Executed"):
        if not getattr(doc, "legal_advice_reference", None):
            frappe.throw(_("Legal advice reference is required before termination approval."))
    if getattr(doc, "workflow_state", None) == "Executed":
        if not getattr(doc, "approved_by", None):
            frappe.throw(_("Approved by is required before execution."))
        if getattr(doc, "settlement_status", None) != "Completed":
            frappe.throw(_("Settlement of accounts must be completed before executing termination."))
        if not getattr(doc, "notice_issued_to_supplier", 0):
            frappe.throw(_("Supplier notice must be issued before executing termination."))

def handle_termination_events(doc, method=None):
    if getattr(doc, "workflow_state", None) == "Executed":
        frappe.db.set_value("Contract", doc.contract, "status", "Terminated")
