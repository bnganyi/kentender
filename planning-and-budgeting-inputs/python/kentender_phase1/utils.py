from __future__ import annotations

import hashlib
from typing import Iterable

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime


def generate_app_number(entity: str, financial_year: str) -> str:
    entity_code = (entity or "ENT")[:4].upper().replace(" ", "")
    fy_code = (financial_year or "FY").replace("-", "")[-4:]
    count = frappe.db.count("Procurement Plan", filters={"entity": entity, "financial_year": financial_year}) + 1
    return f"APP-{entity_code}-{fy_code}-{count:03d}"


def assert_active_policy_profile(policy_profile: str, entity: str, financial_year: str) -> None:
    if not policy_profile:
        frappe.throw(_("Policy Profile is required."))
    status = frappe.db.get_value("Procurement Policy Profile", policy_profile, "status")
    if status != "Active":
        frappe.throw(_("Procurement Policy Profile must be Active before the APP can progress."))


def ensure_single_active_original_app(doc) -> None:
    if doc.plan_type != "Annual" or doc.revision_type in {"Supplementary", "Formal Revision", "Administrative Update"}:
        return
    existing = frappe.get_all(
        "Procurement Plan",
        filters={
            "entity": doc.entity,
            "financial_year": doc.financial_year,
            "plan_type": "Annual",
            "name": ["!=", doc.name or ""],
            "status": ["in", ["Approved", "Published", "Locked"]],
        },
        pluck="name",
    )
    if existing:
        frappe.throw(_("Another active annual APP already exists for this entity and financial year: {0}").format(existing[0]))


def recalculate_plan_totals(doc) -> None:
    rows = frappe.get_all(
        "Procurement Plan Item",
        filters={"parent_plan": doc.name},
        fields=["estimated_cost", "reserved_budget_amount", "committed_amount", "actual_amount"],
    ) if doc.name else []
    doc.total_budget = sum(flt(r.estimated_cost) for r in rows)
    doc.total_planned_amount = doc.total_budget
    doc.total_reserved_amount = sum(flt(r.reserved_budget_amount) for r in rows)
    doc.total_committed_amount = sum(flt(r.committed_amount) for r in rows)
    doc.total_actual_amount = sum(flt(r.actual_amount) for r in rows)


def derive_national_priority_from_objective(objective_name: str) -> str | None:
    if not objective_name:
        return None
    return frappe.db.get_value("Strategic Objective", objective_name, "priority")


def derive_method_recommendation(doc) -> str:
    rules = frappe.get_all(
        "Procurement Threshold Rule",
        filters={"active": 1, "procurement_type": doc.procurement_type},
        fields=["name", "category", "minimum_amount", "maximum_amount", "recommended_method"],
    )
    value = flt(doc.estimated_cost)
    for rule in rules:
        if (not rule.category or rule.category == doc.category) and flt(rule.minimum_amount) <= value <= flt(rule.maximum_amount):
            return rule.recommended_method
    return doc.procurement_method


def get_risk_rating(doc) -> tuple[float, str]:
    score = 0.0
    if flt(doc.estimated_cost) >= 10000000:
        score += 40
    elif flt(doc.estimated_cost) >= 1000000:
        score += 20
    if doc.procurement_method in {"Direct Procurement", "Restricted Tender"}:
        score += 25
    if doc.emergency_flag:
        score += 20
    if doc.recurring_flag:
        score += 5
    level = "Low" if score < 25 else "Medium" if score < 50 else "High"
    return score, level


def assert_budget_available(doc) -> dict:
    # Starter placeholder. Replace with company/fiscal-year budget aggregation against ERPNext Budget/GL docs.
    planned = flt(doc.approved_planned_cost or doc.estimated_cost)
    if planned <= 0:
        return {"status": "Blocked", "message": "Invalid planned amount"}
    return {"status": "Available", "message": "Starter implementation assumes budget availability service will be wired in Phase 1 integration."}


def detect_anti_split_candidates(doc) -> dict:
    matches = frappe.get_all(
        "Procurement Plan Item",
        filters={
            "name": ["!=", doc.name or ""],
            "responsible_department": doc.responsible_department,
            "budget_head": doc.budget_head,
            "category": doc.category,
            "quarter": doc.quarter,
        },
        fields=["name", "estimated_cost", "description"],
        limit=10,
    )
    return {"block": len(matches) >= 2, "matches": matches}


def log_sensitive_field_changes(doc, sensitive_fields: Iterable[str]) -> None:
    if doc.is_new():
        return
    previous = doc.get_doc_before_save()
    if not previous:
        return
    for fieldname in sensitive_fields:
        old = previous.get(fieldname)
        new = doc.get(fieldname)
        if old != new:
            frappe.get_doc({
                "doctype": "Budget Override Record",
                "reference_doctype": doc.doctype,
                "reference_name": doc.name,
                "override_type": "Amount" if fieldname == "estimated_cost" else "Timing" if "date" in fieldname or fieldname == "quarter" else "Method" if fieldname == "procurement_method" else "Budget",
                "field_name": fieldname,
                "old_value": str(old),
                "new_value": str(new),
                "reason": doc.override_reason or "Tracked field change",
                "requested_by": frappe.session.user,
                "status": "Draft",
            }).insert(ignore_permissions=True)


def create_published_snapshot(doc) -> None:
    payload = frappe.as_json(doc.as_dict(), indent=2)
    hash_value = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    frappe.get_doc({
        "doctype": "Published Plan Record",
        "procurement_plan": doc.name,
        "publication_type": "Internal",
        "published_by": frappe.session.user,
        "published_on": now_datetime(),
        "pdf_attachment": "PENDING_GENERATED_EXPORT.pdf",
        "hash_value": hash_value,
        "notes": "Starter snapshot placeholder. Replace attachment generation in implementation.",
    }).insert(ignore_permissions=True)


def lock_procurement_plan(doc) -> None:
    doc.db_set("locked_on", now_datetime(), update_modified=False)
    doc.db_set("locked_by", frappe.session.user, update_modified=False)


def create_revision_snapshot(doc) -> None:
    # Replace with dedicated snapshot DocType if desired.
    pass


def supersede_previous_plan_version(plan_name: str) -> None:
    if plan_name:
        frappe.db.set_value("Procurement Plan", plan_name, "status", "Superseded")


def get_available_plan_item_balance(plan_item_name: str) -> float:
    row = frappe.db.get_value(
        "Procurement Plan Item",
        plan_item_name,
        ["approved_planned_cost", "committed_amount", "actual_amount"],
        as_dict=True,
    ) or {}
    planned = flt(row.get("approved_planned_cost"))
    committed = flt(row.get("committed_amount"))
    actual = flt(row.get("actual_amount"))
    return max(planned - max(committed, actual), 0)


def create_commitment_from_requisition(doc) -> None:
    plan_item = frappe.get_doc("Procurement Plan Item", doc.procurement_plan_item)
    commitment = frappe.get_doc({
        "doctype": "Procurement Commitment",
        "commitment_number": frappe.generate_hash(length=10).upper(),
        "procurement_plan_item": plan_item.name,
        "entity": frappe.db.get_value("Procurement Plan", plan_item.parent_plan, "entity"),
        "financial_year": frappe.db.get_value("Procurement Plan", plan_item.parent_plan, "financial_year"),
        "budget_head": plan_item.budget_head,
        "cost_center": plan_item.cost_center,
        "commitment_stage": "Requisition Commitment",
        "committed_amount": doc.estimated_cost,
        "status": "Active",
        "created_from_doc_type": doc.doctype,
        "created_from_doc_name": doc.name,
    })
    commitment.insert(ignore_permissions=True)
