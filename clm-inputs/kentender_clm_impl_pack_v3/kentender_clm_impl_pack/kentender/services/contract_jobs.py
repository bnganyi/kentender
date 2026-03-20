import frappe
from frappe.utils import nowdate

def monitor_contract_expiry():
    contracts = frappe.get_all("Contract", filters={"status": ["in", ["Active","Suspended"]]}, fields=["name","end_date"])
    today = nowdate()
    for c in contracts:
        if c.end_date and c.end_date < today:
            frappe.db.set_value("Contract", c.name, "status", "Closed")

def monitor_dlp_expiry():
    contracts = frappe.get_all("Contract", filters={"dlp_status": "Active"}, fields=["name","dlp_end_date"])
    today = nowdate()
    for c in contracts:
        if c.dlp_end_date and c.dlp_end_date < today:
            frappe.db.set_value("Contract", c.name, "dlp_status", "Completed")
