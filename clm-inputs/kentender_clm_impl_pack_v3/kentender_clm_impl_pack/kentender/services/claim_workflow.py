import frappe
from frappe import _

def validate_claim_rules(doc, method=None):
    contract = frappe.get_doc("Contract", doc.contract)
    if contract.status not in ("Active","Suspended"):
        frappe.throw(_("Claims are only allowed for active or suspended contracts."))
    if not doc.claim_type:
        frappe.throw(_("Claim type is required."))
    if doc.claim_type == "Variation Claim" and not getattr(doc, "reference_variation", None):
        frappe.throw(_("Variation Claim must reference a Contract Variation."))

def handle_claim_events(doc, method=None):
    if doc.status == "Escalated to Dispute":
        existing = frappe.db.get_value("Dispute Case", {"claim": doc.name}, "name")
        if not existing:
            dispute = frappe.get_doc({
                "doctype": "Dispute Case",
                "contract": doc.contract,
                "claim": doc.name,
                "notice_date": frappe.utils.nowdate(),
                "current_stage": "Notice of Claim",
                "status": "Open",
                "summary": f"Auto-created from Claim {doc.name}"
            })
            dispute.insert(ignore_permissions=True)
