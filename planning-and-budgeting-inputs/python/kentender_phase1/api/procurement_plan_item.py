from frappe.utils import flt

from __future__ import annotations

import frappe
from frappe import _

from kentender_phase1.utils import (
    assert_budget_available,
    derive_national_priority_from_objective,
    detect_anti_split_candidates,
    derive_method_recommendation,
    get_risk_rating,
    log_sensitive_field_changes,
)


SENSITIVE_FIELDS = {
    "estimated_cost", "procurement_method", "quarter", "budget_head",
    "cost_center", "planned_tender_date", "planned_award_date"
}


def before_save(doc, method=None):
    recommended = derive_method_recommendation(doc)
    doc.system_recommended_method = recommended
    score, level = get_risk_rating(doc)
    doc.risk_score = score
    doc.risk_level = level


def validate(doc, method=None):
    if flt(doc.estimated_cost) <= 0:
        frappe.throw(_("Estimated cost must be greater than zero."))

    if not doc.parent_plan:
        frappe.throw(_("Parent Plan is required."))

    derived_priority = derive_national_priority_from_objective(doc.strategic_objective)
    if derived_priority and doc.national_priority and derived_priority != doc.national_priority:
        frappe.throw(_("National Priority must match the selected Strategic Objective."))
    elif derived_priority and not doc.national_priority:
        doc.national_priority = derived_priority

    if doc.procurement_method != doc.system_recommended_method and not doc.method_override_reason:
        frappe.throw(_("Method Override Reason is required when the selected method differs from the recommended method."))

    if doc.emergency_flag and not doc.override_reason:
        frappe.throw(_("Override Reason / emergency justification is required for emergency procurement."))

    budget_result = assert_budget_available(doc)
    doc.budget_status = budget_result["status"]

    anti_split = detect_anti_split_candidates(doc)
    if anti_split["block"]:
        frappe.throw(_("Potential procurement fragmentation detected. Review aggregation before approval."))


def on_update(doc, method=None):
    log_sensitive_field_changes(doc, SENSITIVE_FIELDS)
