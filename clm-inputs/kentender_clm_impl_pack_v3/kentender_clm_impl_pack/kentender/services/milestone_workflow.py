import frappe
from frappe import _
from kentender.services.quality_integration import create_quality_inspection_for_task

def validate_task_milestone_rules(doc, method=None):
    if not getattr(doc, "is_contract_milestone", 0):
        return
    if getattr(doc, "milestone_status", None) and not getattr(doc, "contract", None):
        frappe.throw(_("Contract is required for milestone tasks."))
    if doc.milestone_status == "Completed by Supplier" and not getattr(doc, "supplier_confirmed", 0):
        frappe.throw(_("Supplier confirmation is required before milestone completion."))
    if doc.milestone_status in ("Accepted", "Rejected", "Payment Eligible") and getattr(doc, "quality_inspection_required", 0):
        qi = frappe.db.get_value("Quality Inspection", {"reference_type":"Task","reference_name":doc.name}, "name")
        if not qi:
            frappe.throw(_("Quality Inspection is required before milestone acceptance."))
    if doc.contract_type == "Goods" and doc.milestone_status in ("Accepted","Payment Eligible"):
        pr = frappe.db.get_value("Purchase Receipt", {"contract":doc.contract,"milestone_task":doc.name}, "name")
        if not pr:
            frappe.throw(_("Goods milestones require a linked Purchase Receipt before acceptance."))

def handle_task_milestone_events(doc, method=None):
    if not getattr(doc, "is_contract_milestone", 0):
        return
    if doc.milestone_status == "Sent for Inspection" and getattr(doc, "quality_inspection_required", 0):
        existing = frappe.db.get_value("Quality Inspection", {"reference_type":"Task","reference_name":doc.name}, "name")
        if not existing:
            create_quality_inspection_for_task(doc.name)
