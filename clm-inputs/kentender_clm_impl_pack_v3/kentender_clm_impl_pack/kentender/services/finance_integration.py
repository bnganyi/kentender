import frappe
from frappe import _
from frappe.utils import nowdate

def validate_purchase_invoice_certificate(doc, method=None):
    if not getattr(doc, "contract", None):
        return
    if not getattr(doc, "acceptance_certificate", None):
        frappe.throw(_("Purchase Invoice requires a valid Acceptance Certificate."))
    cert = frappe.get_doc("Acceptance Certificate", doc.acceptance_certificate)
    if getattr(cert, "workflow_state", None) != "Issued":
        frappe.throw(_("Acceptance Certificate must be issued."))
    if cert.contract != doc.contract:
        frappe.throw(_("Acceptance Certificate does not belong to the selected Contract."))

def create_retention_ledger_entry_from_invoice(doc, method=None):
    if not getattr(doc, "contract", None):
        return
    contract = frappe.get_doc("Contract", doc.contract)
    pct = float(getattr(contract, "retention_percentage", 0) or 0)
    if pct <= 0:
        return
    retained_amount = float(doc.grand_total or 0) * pct / 100.0
    if retained_amount <= 0:
        return
    from kentender.services.retention_workflow import get_contract_retention_balance
    balance = get_contract_retention_balance(contract.name) + retained_amount
    ledger = frappe.get_doc({
        "doctype": "Retention Ledger",
        "contract": contract.name,
        "purchase_invoice": doc.name,
        "retention_type": "Deduction",
        "posting_date": getattr(doc, "posting_date", None) or nowdate(),
        "amount": retained_amount,
        "balance_after_transaction": balance,
        "status": "Held",
        "remarks": f"Retention deducted from Purchase Invoice {doc.name}",
    })
    ledger.insert(ignore_permissions=True)
