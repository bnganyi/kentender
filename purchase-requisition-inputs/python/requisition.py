from __future__ import annotations

import json
from typing import Iterable

import frappe
from frappe import _
from frappe.utils import now_datetime


MATERIAL_FIELDS = {
    "required_by_date",
    "justification",
    "delivery_location",
    "budget_reference",
    "program_code",
    "cost_center",
    "project",
    "request_date",
    "department",
}


def validate_requisition(doc, method=None):
    _validate_header(doc)
    _validate_items(doc)
    _compute_totals(doc)
    _set_budget_status(doc)
    _ensure_approval_rows(doc)
    _run_anti_split_checks(doc)
    _enforce_post_approval_lock(doc)


def before_submit(doc, method=None):
    if not doc.items:
        frappe.throw(_("At least one requisition item is required before submit."))
    if doc.source_mode == "One-Off":
        _ensure_exception_exists(doc, "One-Off")
    if doc.emergency_flag:
        _ensure_exception_exists(doc, "Emergency")
    if doc.budget_status == "Blocked":
        frappe.throw(_("Budget status is Blocked. Resolve budget issues before submit."))
    doc.submitted_on = now_datetime()


def on_submit(doc, method=None):
    if doc.status != "Approved":
        return
    _create_commitments(doc)
    _create_snapshot(doc, "Approval")
    doc.db_set("approved_on", now_datetime())
    doc.db_set("tender_readiness_status", "Ready for Tender")


def on_cancel(doc, method=None):
    _release_commitments(doc, reason="Document cancelled")
    _create_snapshot(doc, "Cancellation")
    doc.db_set("cancelled_on", now_datetime())


def on_update_after_submit(doc, method=None):
    _enforce_post_approval_lock(doc)


def _validate_header(doc):
    required = ["entity", "department", "requestor", "financial_year", "requisition_type", "source_mode", "request_date", "required_by_date", "justification", "delivery_location", "currency"]
    for fieldname in required:
        if not doc.get(fieldname):
            frappe.throw(_("{0} is required.").format(fieldname.replace("_", " ").title()))
    if doc.source_mode == "One-Off" and not doc.one_off_flag:
        frappe.throw(_("One-Off source mode requires one_off_flag to be enabled."))
    if doc.required_by_date and doc.request_date and doc.required_by_date < doc.request_date:
        frappe.throw(_("Required by date cannot be earlier than request date."))


def _validate_items(doc):
    if not doc.items:
        frappe.throw(_("At least one requisition item is required."))
    total = 0
    for idx, row in enumerate(doc.items, start=1):
        row.line_number = idx
        if not row.item_description:
            frappe.throw(_("Item description is required on row {0}.").format(idx))
        if not row.technical_specification:
            frappe.throw(_("Technical specification is required on row {0}.").format(idx))
        if row.quantity is None or row.quantity <= 0:
            frappe.throw(_("Quantity must be greater than zero on row {0}.").format(idx))
        if row.estimated_unit_cost is None or row.estimated_unit_cost <= 0:
            frappe.throw(_("Estimated unit cost must be greater than zero on row {0}.").format(idx))
        row.estimated_total_cost = (row.quantity or 0) * (row.estimated_unit_cost or 0)
        total += row.estimated_total_cost
        if doc.source_mode == "APP Linked" and not row.procurement_plan_item:
            frappe.throw(_("APP-linked requisitions require Procurement Plan Item on row {0}.").format(idx))
        if doc.source_mode == "APP Linked" and row.procurement_plan_item:
            _validate_against_plan_item(doc, row, idx)
    doc.total_estimated_cost = total


def _validate_against_plan_item(doc, row, idx):
    # Placeholder lookup logic. Replace with actual APP balance service.
    remaining_balance = getattr(row, "remaining_app_balance", None) or row.estimated_total_cost
    row.remaining_app_balance = remaining_balance
    if row.estimated_total_cost > remaining_balance:
        frappe.throw(_("Row {0} exceeds remaining APP balance.").format(idx))


def _compute_totals(doc):
    doc.total_estimated_cost = sum((row.estimated_total_cost or 0) for row in doc.items)
    doc.total_committed_amount = frappe.db.sql("""
        select coalesce(sum(committed_amount - released_amount), 0)
        from `tabPurchase Requisition Commitment`
        where purchase_requisition=%s and status in ('Active', 'Partially Consumed', 'Consumed')
    """, doc.name)[0][0] if doc.name else 0


def _set_budget_status(doc):
    # Placeholder: replace with actual rules + budget service.
    if not doc.items:
        doc.budget_status = "Unchecked"
        return
    over_limit = any((row.estimated_total_cost or 0) > (row.remaining_app_balance or row.estimated_total_cost) for row in doc.items)
    doc.budget_status = "Blocked" if over_limit else "Available"


def _ensure_approval_rows(doc):
    if doc.approvals:
        return
    default_route = [
        ("Submission", "Requestor"),
        ("HoD Review", "Head of Department"),
        ("Finance Review", "Finance/Budget Officer"),
        ("AO Review", "Accounting Officer"),
        ("Procurement Review", "Procurement Officer"),
        ("Final Approval", "Head of Procurement"),
    ]
    for stage, role in default_route:
        doc.append("approvals", {
            "approval_stage": stage,
            "approver_role": role,
            "action": "Pending",
        })


def _run_anti_split_checks(doc):
    # Heuristic placeholder. Replace with search across recent requisitions and APP items.
    near_threshold = [row for row in doc.items if (row.estimated_total_cost or 0) > 0 and (row.estimated_total_cost or 0) % 100000 < 5000]
    if near_threshold and not doc.exception_flag:
        doc.exception_flag = 1


def _enforce_post_approval_lock(doc):
    if doc.is_new():
        return
    if doc.status not in {"Approved", "Cancelled", "Closed"}:
        return
    old_doc = doc.get_doc_before_save()
    if not old_doc:
        return
    changed_fields = [field for field in MATERIAL_FIELDS if old_doc.get(field) != doc.get(field)]
    item_changed = len(old_doc.items) != len(doc.items)
    if not item_changed:
        for i, row in enumerate(doc.items):
            if i >= len(old_doc.items):
                item_changed = True
                break
            old_row = old_doc.items[i]
            for field in ["procurement_plan_item", "item_description", "technical_specification", "quantity", "estimated_unit_cost", "budget_head", "cost_center", "project", "funding_source"]:
                if old_row.get(field) != row.get(field):
                    item_changed = True
                    break
            if item_changed:
                break
    if changed_fields or item_changed:
        frappe.throw(_("Approved requisitions cannot be materially edited directly. Use Purchase Requisition Amendment."))


def _ensure_exception_exists(doc, exception_type: str):
    exists = frappe.db.exists("Purchase Requisition Exception", {"purchase_requisition": doc.name, "exception_type": exception_type, "status": ["!=", "Rejected"]})
    if not exists:
        frappe.throw(_("{0} exception record is required before submit.").format(exception_type))


def _create_commitments(doc):
    for row in doc.items:
        if frappe.db.exists("Purchase Requisition Commitment", {"purchase_requisition": doc.name, "requisition_item_idx": row.idx, "status": ["in", ["Active", "Partially Consumed", "Consumed"]]}):
            continue
        commitment = frappe.get_doc({
            "doctype": "Purchase Requisition Commitment",
            "purchase_requisition": doc.name,
            "requisition_item_idx": row.idx,
            "entity": doc.entity,
            "financial_year": doc.financial_year,
            "budget_head": row.budget_head,
            "cost_center": row.cost_center,
            "project": row.project,
            "committed_amount": row.estimated_total_cost,
            "status": "Active",
            "created_from_stage": "Requisition Approval",
            "created_on": now_datetime(),
        })
        commitment.insert(ignore_permissions=True)


def _release_commitments(doc, reason: str):
    names = frappe.get_all("Purchase Requisition Commitment", filters={"purchase_requisition": doc.name, "status": ["in", ["Active", "Partially Consumed", "Consumed"]]}, pluck="name")
    for name in names:
        c = frappe.get_doc("Purchase Requisition Commitment", name)
        c.released_amount = (c.committed_amount or 0) - (c.actualized_amount or 0)
        c.status = "Released"
        c.released_on = now_datetime()
        c.release_reason = reason
        c.save(ignore_permissions=True)


def _create_snapshot(doc, snapshot_type: str):
    snapshot = frappe.get_doc({
        "doctype": "Purchase Requisition Snapshot",
        "purchase_requisition": doc.name,
        "snapshot_type": snapshot_type,
        "snapshot_json": json.dumps(doc.as_dict(), default=str),
        "created_by": frappe.session.user,
        "created_on": now_datetime(),
    })
    snapshot.insert(ignore_permissions=True)
