import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate

def get_contract_retention_balance(contract_name: str) -> float:
    rows = frappe.get_all("Retention Ledger", filters={"contract": contract_name}, fields=["retention_type", "amount"])
    balance = 0.0
    for row in rows:
        amt = float(row.amount or 0)
        if row.retention_type == "Deduction":
            balance += amt
        elif row.retention_type in ("Release","Adjustment","Forfeiture"):
            balance -= amt
    return balance

def validate_retention_release_rules(doc, method=None):
    contract = frappe.get_doc("Contract", doc.contract)
    if contract.status not in ("Closed","Active"):
        frappe.throw(_("Retention release is only allowed for active or closed contracts."))
    if doc.status in ("Pending Review","Pending Approval","Approved","Released"):
        if getdate(doc.eligible_release_date) > getdate(nowdate()):
            frappe.throw(_("Retention cannot be released before the eligible release date."))
    balance = get_contract_retention_balance(doc.contract)
    if float(doc.requested_amount or 0) <= 0:
        frappe.throw(_("Requested retention release amount must be greater than zero."))
    if float(doc.requested_amount or 0) > balance:
        frappe.throw(_("Requested retention release amount exceeds retained balance."))

def execute_retention_release(doc):
    if doc.status != "Released" or getattr(doc, "retention_ledger_entry", None):
        return
    approved_amount = float(doc.approved_amount or doc.requested_amount or 0)
    current_balance = get_contract_retention_balance(doc.contract)
    if approved_amount > current_balance:
        frappe.throw(_("Approved release amount exceeds retained balance."))
    ledger = frappe.get_doc({
        "doctype": "Retention Ledger",
        "contract": doc.contract,
        "retention_type": "Release",
        "posting_date": doc.released_on or nowdate(),
        "amount": approved_amount,
        "balance_after_transaction": current_balance - approved_amount,
        "release_date": doc.released_on or nowdate(),
        "status": "Released",
        "remarks": f"Released via Retention Release Request {doc.name}",
    })
    ledger.insert(ignore_permissions=True)
    doc.db_set("retention_ledger_entry", ledger.name, update_modified=True)

def handle_retention_release_events(doc, method=None):
    if doc.status == "Released":
        execute_retention_release(doc)

def create_due_retention_release_requests():
    pass  # policy-specific; implement once eligibility rule is finalized

def get_retention_notification_recipients(contract_name):
    users = set()
    for role in ("Head of Procurement","Head of Finance"):
        role_users = frappe.get_all("Has Role", filters={"role": role}, fields=["parent"])
        for u in role_users:
            email = frappe.db.get_value("User", u.parent, "email")
            if email:
                users.add(email)
    return list(users)

def _notify_retention_due(row, overdue=False):
    recipients = get_retention_notification_recipients(row.contract)
    if not recipients:
        return
    subject = f"Retention Release {'Overdue' if overdue else 'Upcoming'} for Contract {row.contract}"
    message = f"Retention release request {row.name} for contract {row.contract} is {'overdue' if overdue else 'due soon'}."
    frappe.sendmail(recipients=recipients, subject=subject, message=message)

def send_retention_release_reminders():
    today = getdate()
    targets = frappe.get_all("Retention Release Request", filters={
        "status": ["in", ["Draft","Pending Review","Pending Approval"]],
        "eligible_release_date": ["between", [today, add_days(today, 14)]]
    }, fields=["name","contract","eligible_release_date","requested_amount"])
    for row in targets:
        _notify_retention_due(row, overdue=False)

def send_overdue_retention_alerts():
    today = getdate()
    overdue = frappe.get_all("Retention Release Request", filters={
        "status": ["in", ["Draft","Pending Review","Pending Approval","Approved"]],
        "eligible_release_date": ["<", today]
    }, fields=["name","contract","eligible_release_date","requested_amount"])
    for row in overdue:
        _notify_retention_due(row, overdue=True)
