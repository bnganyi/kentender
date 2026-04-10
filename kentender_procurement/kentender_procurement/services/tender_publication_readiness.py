# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Publication readiness for **Tender** (PROC-STORY-032).

Used by :mod:`kentender_procurement.services.tender_workflow_actions` before publish.
Does not mutate documents.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime

from kentender_procurement.kentender_procurement.doctype.tender.tender import ORIGIN_FROM_PLAN_ITEM

TENDER_DOCTYPE = "Tender"
PPI_DOCTYPE = "Procurement Plan Item"
PP_DOCTYPE = "Procurement Plan"
CRITERIA_DOCTYPE = "Tender Criteria"
DOCUMENT_DOCTYPE = "Tender Document"
VISIBILITY_DOCTYPE = "Tender Visibility Rule"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _date_chain_reasons(doc) -> list[str]:
	"""Return human-readable reasons when schedule datetimes are not non-decreasing."""
	labels = (
		_("Publication"),
		_("Clarification deadline"),
		_("Submission deadline"),
		_("Opening"),
	)
	fields = (
		"publication_datetime",
		"clarification_deadline",
		"submission_deadline",
		"opening_datetime",
	)
	last_label: str | None = None
	last_dt = None
	out: list[str] = []
	for i, fn in enumerate(fields):
		raw = doc.get(fn)
		if raw is None:
			continue
		dt = get_datetime(raw)
		if dt is None:
			continue
		if last_dt is not None and last_label is not None and dt < last_dt:
			out.append(
				_("{0} must be on or after {1}.").format(labels[i], last_label),
			)
		last_label = labels[i]
		last_dt = dt
	return out


def _visibility_rule_required(doc) -> bool:
	mode = _norm(doc.get("supplier_eligibility_rule_mode")) or "Open"
	if mode != "Open":
		return True
	pm = _norm(doc.get("procurement_method"))
	if pm == "Restricted Bidding":
		return True
	return False


def assess_tender_publication_readiness(tender_name: str) -> dict[str, Any]:
	"""Return whether a tender is ready to publish.

	:returns: ``ok`` (bool), ``reasons`` (list of str), ``tender`` (name or None).
	"""
	tn = _norm(tender_name)
	empty: dict[str, Any] = {"ok": False, "reasons": [], "tender": tn or None}
	if not tn:
		empty["reasons"] = [_("Tender name is required.")]
		return empty
	if not frappe.db.exists(TENDER_DOCTYPE, tn):
		empty["reasons"] = [_("Tender {0} does not exist.").format(tn)]
		return empty

	doc = frappe.get_doc(TENDER_DOCTYPE, tn)
	reasons: list[str] = []

	if not doc.publication_datetime:
		reasons.append(_("Publication datetime is required before publish."))
	if not doc.submission_deadline:
		reasons.append(_("Submission deadline is required before publish."))

	reasons.extend(_date_chain_reasons(doc))

	if _norm(doc.origin_type) == ORIGIN_FROM_PLAN_ITEM:
		ppi = _norm(doc.procurement_plan_item)
		pp = _norm(doc.procurement_plan)
		if not ppi:
			reasons.append(
				_("Procurement Plan Item is required when origin type is {0}.").format(
					ORIGIN_FROM_PLAN_ITEM,
				),
			)
		elif not frappe.db.exists(PPI_DOCTYPE, ppi):
			reasons.append(_("Procurement Plan Item {0} does not exist.").format(ppi))
		if not pp:
			reasons.append(
				_("Procurement Plan is required when origin type is {0}.").format(ORIGIN_FROM_PLAN_ITEM),
			)
		elif not frappe.db.exists(PP_DOCTYPE, pp):
			reasons.append(_("Procurement Plan {0} does not exist.").format(pp))
		if ppi and pp and frappe.db.exists(PPI_DOCTYPE, ppi):
			plan_from_item = _norm(frappe.db.get_value(PPI_DOCTYPE, ppi, "procurement_plan"))
			if plan_from_item and pp and plan_from_item != pp:
				reasons.append(_("Procurement Plan must match the plan item's parent plan."))

	n_crit = frappe.db.count(CRITERIA_DOCTYPE, {"tender": tn})
	if n_crit < 1:
		reasons.append(_("At least one Tender Criteria row is required before publish."))

	n_doc = frappe.db.count(DOCUMENT_DOCTYPE, {"tender": tn})
	if n_doc < 1:
		reasons.append(_("At least one Tender Document is required before publish."))

	if _visibility_rule_required(doc):
		n_vis = frappe.db.count(VISIBILITY_DOCTYPE, {"tender": tn})
		if n_vis < 1:
			reasons.append(
				_(
					"At least one Tender Visibility Rule is required for this eligibility mode or procurement method.",
				),
			)

	return {
		"ok": len(reasons) == 0,
		"reasons": reasons,
		"tender": tn,
	}
