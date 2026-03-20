from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_phase1.utils import (
    assert_active_policy_profile,
    ensure_single_active_original_app,
    generate_app_number,
    recalculate_plan_totals,
    create_published_snapshot,
    lock_procurement_plan,
)


def before_insert(doc, method=None):
    if not doc.app_number:
        doc.app_number = generate_app_number(doc.entity, doc.financial_year)


def validate(doc, method=None):
    required = [
        "entity", "financial_year", "budget_reference", "budget_approval_date",
        "budget_approved_by", "policy_profile", "created_by_department",
    ]
    for fieldname in required:
        if not doc.get(fieldname):
            frappe.throw(_("{0} is required").format(doc.meta.get_label(fieldname)))

    assert_active_policy_profile(doc.policy_profile, doc.entity, doc.financial_year)
    ensure_single_active_original_app(doc)
    recalculate_plan_totals(doc)

    if doc.plan_type in {"Supplementary", "Revision"} and not doc.parent_plan_version:
        frappe.throw(_("Parent Plan Version is required for supplementary or revision records."))

    if doc.status in {"Published", "Locked", "Superseded"} and doc.has_value_changed("status"):
        # additional permission checks can be added here
        pass


def on_submit(doc, method=None):
    doc.db_set("submission_date", now_datetime(), update_modified=False)
    recalculate_plan_totals(doc)


def on_update_after_submit(doc, method=None):
    if doc.status == "Published" and not doc.published_date:
        doc.db_set("published_date", now_datetime(), update_modified=False)
        create_published_snapshot(doc)
    if doc.status == "Locked" and not doc.locked_on:
        lock_procurement_plan(doc)
