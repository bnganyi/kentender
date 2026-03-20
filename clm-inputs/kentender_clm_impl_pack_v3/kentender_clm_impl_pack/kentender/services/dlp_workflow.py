import frappe
from frappe import _

def validate_defect_case_rules(doc, method=None):
    contract = frappe.get_doc("Contract", doc.contract)
    if getattr(contract, "dlp_status", None) not in ("Active","Reopened"):
        frappe.throw(_("Defect Liability Case can only be opened during an active or reopened DLP."))

def reopen_contract_for_defect(contract_name: str):
    contract = frappe.get_doc("Contract", contract_name)
    contract.dlp_status = "Reopened"
    contract.status = "Active"
    contract.save(ignore_permissions=True)

def handle_defect_case_events(doc, method=None):
    if getattr(doc, "status", None) == "Escalated" and getattr(doc, "severity", None) in ("High","Critical"):
        reopen_contract_for_defect(doc.contract)
