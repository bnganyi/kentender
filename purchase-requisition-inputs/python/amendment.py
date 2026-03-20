from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import now_datetime


def on_submit(doc, method=None):
    req = frappe.get_doc("Purchase Requisition", doc.purchase_requisition)
    if req.linked_tender_count and doc.amendment_type in {"Scope", "Quantity", "Budget"}:
        frappe.throw(_("Material amendments are blocked after tender handoff. Cancel/reissue or handle through procurement change control."))
    _apply_changes(req, doc)
    _create_snapshot(req, doc)


def _apply_changes(req, amendment):
    # Placeholder only: apply changes from child table when modeled in the app.
    req.add_comment("Edit", _("Amendment {0} approved.").format(amendment.name))
    req.save(ignore_permissions=True)


def _create_snapshot(req, amendment):
    snap = frappe.get_doc({
        "doctype": "Purchase Requisition Snapshot",
        "purchase_requisition": req.name,
        "snapshot_type": "Amendment Approval",
        "snapshot_json": json.dumps({"requisition": req.as_dict(), "amendment": amendment.as_dict()}, default=str),
        "created_by": frappe.session.user,
        "created_on": now_datetime(),
    })
    snap.insert(ignore_permissions=True)
