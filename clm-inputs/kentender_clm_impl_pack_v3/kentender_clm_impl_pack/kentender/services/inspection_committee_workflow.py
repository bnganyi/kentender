import frappe
from frappe import _

def validate_inspection_committee_rules(doc, method=None):
    existing = frappe.db.get_value("Inspection Committee Member", {
        "contract": doc.contract, "employee": doc.employee, "status": ["in", ["Approved", "Active"]]
    }, "name")
    if existing and existing != doc.name:
        frappe.throw(_("Employee is already appointed to this contract's inspection committee."))
    if getattr(doc, "member_type", None) == "Technical Specialist" and not getattr(doc, "qualification", None):
        frappe.throw(_("Technical Specialist appointments require qualification details."))

def handle_inspection_committee_events(doc, method=None):
    pass
