from __future__ import annotations

import frappe
from frappe.utils import now_datetime
from erpnext.setup.utils import get_exchange_rate


def generate_approval_chain(doc, method) -> None:
    if not getattr(doc, "company", None):
        frappe.throw("Company is required to generate approval chain")
    if not getattr(doc, "estimated_budget", None):
        frappe.throw("Estimated Budget is required to generate approval chain")

    matrix = frappe.get_all(
        "Approval Matrix",
        filters={"company": doc.company},
        fields=["min_amount", "max_amount", "approval_level", "role"],
        order_by="approval_level asc",
    )

    doc.set("approvals", [])

    for row in matrix:
        if row.min_amount is None or row.max_amount is None:
            continue
        if row.min_amount <= doc.estimated_budget <= row.max_amount:
            doc.append(
                "approvals",
                {
                    "approval_level": row.approval_level,
                    "approver_role": row.role,
                    "status": "Pending",
                },
            )

    if not doc.approvals:
        frappe.throw(
            "No Approval Matrix rule matches this estimated budget for the selected company"
        )

    doc.status = "Under Review"


def validate_plan_item(doc, method) -> None:
    if not doc.item_code:
        frappe.throw("Item is required")

    # IMPORTANT: populate approvals during validation so changes persist on submit.
    # Frappe does not automatically re-save changes made in `on_submit`.
    if getattr(doc, "docstatus", 0) == 1:
        generate_approval_chain(doc, method)


@frappe.whitelist()
def approve_plan_item(docname: str) -> str:
    doc = frappe.get_doc("Procurement Plan Item", docname)
    roles = frappe.get_roles(frappe.session.user)

    pending_levels = sorted({r.approval_level for r in doc.approvals if r.status == "Pending"})
    if not pending_levels:
        frappe.throw("No pending approvals found")

    current_level = pending_levels[0]
    approved_any = False

    for row in doc.approvals:
        if row.status != "Pending":
            continue
        if row.approval_level != current_level:
            continue
        if row.approver_role not in roles:
            continue

        row.status = "Approved"
        row.approved_by = frappe.session.user
        approved_any = True

    if not approved_any:
        frappe.throw(
            f"You are not authorized to approve level {current_level} for this Plan Item"
        )

    if all(r.status == "Approved" for r in doc.approvals):
        doc.status = "Approved"

    doc.save()
    return doc.status


def validate_tender(doc, method) -> None:
    plan_item = frappe.get_doc("Procurement Plan Item", doc.procurement_plan_item)
    if plan_item.status != "Approved":
        frappe.throw("Plan Item must be approved before creating Tender")


def validate_submission(doc, method) -> None:
    tender = frappe.get_doc("Tender", doc.tender)
    if tender.status != "Published":
        frappe.throw("Tender is not open")
    if tender.submission_deadline and now_datetime() > tender.submission_deadline:
        frappe.throw("Submission deadline passed")
    set_exchange(doc)
    validate_supplier_compliance(doc.supplier)

    # Phase 2: compute weighted evaluation score (if score rows exist).
    if doc.meta.get_field("total_score"):
        doc.total_score = calculate_total_score(doc)


def calculate_total_score(submission) -> float:
    """Compute weighted score using Evaluation Criteria weights."""
    total = 0.0
    any_row_scored = False

    for row in (getattr(submission, "scores", None) or []):
        if not row.criteria:
            continue
        if row.score is None:
            continue

        any_row_scored = True
        weight = frappe.db.get_value("Evaluation Criteria", row.criteria, "weight") or 0
        total += float(row.score or 0) * float(weight)

    # If there are no score rows, keep total_score at 0.
    # award_tender will decide whether scores are mandatory.
    return float(total) if any_row_scored else 0.0


def set_exchange(doc) -> None:
    company = frappe.db.get_value("Tender", doc.tender, "company")
    company_currency = frappe.get_cached_value("Company", company, "default_currency")
    doc.exchange_rate = get_exchange_rate(doc.currency, company_currency)
    doc.base_amount = (doc.quoted_amount or 0) * (doc.exchange_rate or 0)


def validate_supplier_compliance(supplier: str) -> None:
    status = frappe.db.get_value(
        "Supplier Compliance Profile",
        {"supplier": supplier},
        "status",
    )
    if status != "Verified":
        frappe.throw("Supplier not compliant")


def recheck_supplier_compliance() -> None:
    suppliers = frappe.get_all("Supplier", pluck="name")
    for supplier in suppliers:
        frappe.enqueue("kentender.kentender.api.run_check", supplier=supplier)


def run_check(supplier: str) -> None:
    profile_name = frappe.db.get_value(
        "Supplier Compliance Profile",
        {"supplier": supplier},
        "name",
    )
    if not profile_name:
        profile = frappe.get_doc(
            {
                "doctype": "Supplier Compliance Profile",
                "supplier": supplier,
                "status": "Verified",
                "last_checked": now_datetime(),
            }
        )
        profile.insert()
    else:
        frappe.db.set_value(
            "Supplier Compliance Profile",
            profile_name,
            {"status": "Verified", "last_checked": now_datetime()},
        )


def _resolve_warehouse(company: str, item_code: str) -> str | None:
    # 1) Company-specific Item Default
    warehouse = frappe.db.get_value(
        "Item Default",
        {"parent": item_code, "company": company},
        "default_warehouse",
    )
    if warehouse:
        return warehouse

    # 2) Any warehouse under same company
    warehouse = frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")
    return warehouse


@frappe.whitelist()
def award_tender(tender_name: str, submission_name: str) -> str:
    tender = frappe.get_doc("Tender", tender_name)

    # Phase 2: choose the winner by highest weighted total_score.
    winner = _select_winning_submission(tender_name, submission_name)
    submission = frappe.get_doc("Tender Submission", winner)
    plan_item = frappe.get_doc("Procurement Plan Item", tender.procurement_plan_item)
    is_stock_item = frappe.db.get_value("Item", plan_item.item_code, "is_stock_item")
    warehouse = _resolve_warehouse(tender.company, plan_item.item_code) if is_stock_item else None

    if is_stock_item and not warehouse:
        frappe.throw(
            "No warehouse found for this stock item. Set Item Default warehouse, Company default warehouse, or create a warehouse for the company."
        )

    po = frappe.get_doc(
        {
            "doctype": "Purchase Order",
            "supplier": submission.supplier,
            "company": tender.company,
            "currency": submission.currency,
            "conversion_rate": submission.exchange_rate,
            "schedule_date": now_datetime().date(),
            "items": [
                {
                    "item_code": plan_item.item_code,
                    "qty": plan_item.qty,
                    "rate": submission.quoted_amount,
                    "warehouse": warehouse,
                }
            ],
        }
    )
    po.insert()
    po.submit()

    tender.purchase_order = po.name
    tender.status = "Awarded"
    tender.save()

    return po.name


def _select_winning_submission(tender_name: str, preferred_submission: str | None) -> str:
    submission_names = frappe.get_all(
        "Tender Submission",
        filters={"tender": tender_name},
        pluck="name",
    )
    if not submission_names:
        frappe.throw("No Tender Submissions found for this tender")

    best_name = None
    best_total = None
    best_quote = None

    preferred_total = None
    preferred_quote = None
    preferred_is_best_candidate = False

    for sub_name in submission_names:
        sub = frappe.get_doc("Tender Submission", sub_name)

        # Ensure total_score exists (covers older records that may not have been rescored).
        total = (
            sub.total_score
            if getattr(sub, "total_score", None) not in (None, 0)
            else calculate_total_score(sub)
        )
        total = float(total or 0)

        # If we have no score rows, disqualify for Phase 2 winner selection.
        # (You can relax this later if you want a fallback ranking.)
        scores = getattr(sub, "scores", None) or []
        has_scoring = bool(scores and any(r.criteria for r in scores))
        if not has_scoring:
            continue

        quote = float(sub.quoted_amount or 0)

        if best_total is None or total > best_total or (total == best_total and quote < best_quote):
            best_total = total
            best_quote = quote
            best_name = sub_name

        # Track preferred submission's evaluation values (if it has scoring).
        if preferred_submission and sub_name == preferred_submission:
            preferred_total = total
            preferred_quote = quote
            preferred_is_best_candidate = True

    if best_name:
        # Prefer the submission passed by the caller only if it matches the computed best.
        if preferred_submission and preferred_is_best_candidate:
            if float(preferred_total or 0) == float(best_total or 0) and float(preferred_quote or 0) == float(best_quote or 0):
                return preferred_submission
        return best_name

    # If scoring rows are missing on all submissions, we fail fast.
    frappe.throw("Cannot award: evaluation scores are missing for all Tender Submissions")

