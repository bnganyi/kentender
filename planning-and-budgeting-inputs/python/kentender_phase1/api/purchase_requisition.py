from frappe.utils import flt

from __future__ import annotations

import frappe
from frappe import _

from kentender_phase1.utils import create_commitment_from_requisition, get_available_plan_item_balance


def validate(doc, method=None):
    if not doc.procurement_plan_item:
        frappe.throw(_("Procurement Plan Item is required."))
    if flt(doc.estimated_cost) <= 0:
        frappe.throw(_("Estimated cost must be greater than zero."))

    available = get_available_plan_item_balance(doc.procurement_plan_item)
    if flt(doc.estimated_cost) > available:
        frappe.throw(_("Estimated cost exceeds the remaining approved APP balance for the selected Procurement Plan Item."))


def on_submit(doc, method=None):
    create_commitment_from_requisition(doc)
