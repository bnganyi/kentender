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
    submission = frappe.get_doc("Tender Submission", submission_name)
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

