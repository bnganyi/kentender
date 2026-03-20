from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


def prepare_handoff(requisition_name: str) -> str:
    req = frappe.get_doc("Purchase Requisition", requisition_name)
    if req.status != "Approved":
        frappe.throw(_("Only approved requisitions can be handed off to tendering."))
    handoff = frappe.get_doc({
        "doctype": "Requisition Tender Handoff",
        "purchase_requisition": req.name,
        "handoff_status": "Ready",
        "prepared_by": frappe.session.user,
        "prepared_on": now_datetime(),
    })
    handoff.insert(ignore_permissions=True)
    req.db_set("tender_readiness_status", "Ready for Tender")
    return handoff.name
