import frappe
from frappe import _

def validate_variation_rules(doc, method=None):
    contract = frappe.get_doc("Contract", doc.contract)
    if contract.status != "Active":
        frappe.throw(_("Variations are only allowed on active contracts."))
    if doc.status in ("Submitted","Under Technical Review","Under Financial Review","Pending Approval","Approved","Implemented") and not doc.justification:
        frappe.throw(_("Variation justification is required."))
    if doc.variation_type == "Cost Adjustment" and not doc.financial_impact:
        frappe.throw(_("Cost Adjustment variation requires financial impact."))
    if doc.variation_type == "Time Extension" and not doc.time_extension_days:
        frappe.throw(_("Time Extension variation requires extension days."))

def handle_variation_events(doc, method=None):
    if doc.status != "Implemented":
        return
    contract = frappe.get_doc("Contract", doc.contract)
    if getattr(doc, "revised_contract_value", None):
        contract.contract_value = doc.revised_contract_value
    if getattr(doc, "revised_end_date", None):
        contract.end_date = doc.revised_end_date
    contract.save(ignore_permissions=True)
