import frappe
from frappe import _

def validate_cit_rules(doc, method=None):
    contract = frappe.get_doc("Contract", doc.contract)
    if contract.status not in ("Pending Supplier Signature","Pending Accounting Officer Signature","Active","Suspended"):
        frappe.throw(_("CIT members can only be appointed for contracts that are pending signature, active, or suspended."))
    existing = frappe.db.get_value("Contract Implementation Team Member", {
        "contract": doc.contract, "employee": doc.employee, "status": ["in", ["Approved", "Active"]]
    }, "name")
    if existing and existing != doc.name:
        frappe.throw(_("Employee is already appointed to this contract's implementation team."))
    if not getattr(doc, "member_type", None):
        frappe.throw(_("Member type is required."))
    if not getattr(doc, "department", None):
        frappe.throw(_("Department is required."))

def handle_cit_events(doc, method=None):
    pass
