import frappe
from frappe import _

def validate_dispute_rules(doc, method=None):
    if not getattr(doc, "claim", None):
        frappe.throw(_("Dispute Case must reference a Claim."))
    if getattr(doc, "stop_work_order_issued", 0):
        if "Accounting Officer" not in frappe.get_roles():
            frappe.throw(_("Only Accounting Officer can issue a Stop Work Order."))
        if not getattr(doc, "cit_recommendation", None) or not getattr(doc, "procurement_recommendation", None):
            frappe.throw(_("Stop Work Order requires CIT and Head of Procurement recommendations."))

def handle_dispute_events(doc, method=None):
    if getattr(doc, "stop_work_order_issued", 0):
        frappe.db.set_value("Contract", doc.contract, "status", "Suspended")
