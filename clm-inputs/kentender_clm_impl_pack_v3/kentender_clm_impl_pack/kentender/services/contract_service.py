import frappe
from frappe import _
from frappe.utils import now_datetime, nowdate, add_months

def activate_contract(contract_name: str) -> None:
    contract = frappe.get_doc("Contract", contract_name)
    if not contract.signed_by_supplier or not contract.signed_by_accounting_officer:
        frappe.throw(_("Contract cannot become active before both signatures are completed."))
    if not contract.project:
        from kentender.services.project_integration import create_project_for_contract
        contract.project = create_project_for_contract(contract.name)
    contract.status = "Active"
    contract.activated_on = now_datetime()
    contract.save(ignore_permissions=True)

def start_defect_liability_period(contract_name: str) -> None:
    contract = frappe.get_doc("Contract", contract_name)
    months = int(contract.defect_liability_months or 0)
    if months <= 0:
        return
    contract.dlp_start_date = nowdate()
    contract.dlp_end_date = add_months(nowdate(), months)
    contract.dlp_status = "Active"
    contract.save(ignore_permissions=True)
