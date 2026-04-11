# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-004 / WF-007 / WF-009: policy matching, ordering, and SoD delegation."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.services.separation_of_duty_service import (
	ParticipationRecord,
	has_blocking_sod_violation,
)


def _norm_str(val) -> str:
	if val is None:
		return ""
	return str(val).strip()


def _match_optional_str(policy_value, document_value) -> bool:
	"""If policy sets a non-empty constraint, require equality when the document supplies a value."""
	pv = _norm_str(policy_value)
	if not pv:
		return True
	dv = _norm_str(document_value)
	if not dv:
		return True
	return dv == pv


def _match_optional_bool(policy_int, document_value) -> bool:
	"""If policy flag is set and document has an explicit value, they must align (0/1)."""
	try:
		pi = int(policy_int or 0)
	except (TypeError, ValueError):
		pi = 0
	if not pi:
		return True
	if document_value is None:
		return True
	try:
		di = int(document_value)
	except (TypeError, ValueError):
		return False
	return di == pi


def policy_matches_document(policy_name: str, business_doc: Document) -> bool:
	"""Return True if *business_doc* satisfies *policy_name* matching rules (conservative)."""
	pol = frappe.get_doc("KenTender Workflow Policy", policy_name)
	if not pol.active:
		return False
	if _norm_str(pol.applies_to_doctype) != business_doc.doctype:
		return False
	# Complaint has no procurement `category`; policy.category matches `complaint_type` (Select).
	if _norm_str(business_doc.doctype) == "Complaint":
		cat_ok = _match_optional_str(pol.category, business_doc.get("complaint_type"))
	else:
		cat_ok = _match_optional_str(pol.category, business_doc.get("category"))
	if not cat_ok:
		return False
	if not _match_optional_str(pol.procurement_method, business_doc.get("procurement_method")):
		return False
	if not _match_optional_str(pol.complexity_level, business_doc.get("complexity_level")):
		return False
	if not _match_optional_str(pol.sector, business_doc.get("sector")):
		return False
	if not _match_optional_str(pol.risk_level, business_doc.get("risk_level")):
		return False
	if not _match_optional_str(pol.contract_type, business_doc.get("contract_type")):
		return False
	if not _match_optional_bool(pol.requires_professional_opinion, business_doc.get("requires_professional_opinion")):
		return False
	if not _match_optional_bool(pol.requires_committee, business_doc.get("requires_committee")):
		return False
	amt = business_doc.get("requested_amount")
	if amt is None and _norm_str(business_doc.doctype) == "Acceptance Record":
		amt = business_doc.get("accepted_value_amount")
	if amt is not None and (pol.threshold_min or pol.threshold_max):
		try:
			val = float(amt)
		except (TypeError, ValueError):
			val = None
		if val is not None:
			if pol.threshold_min and val < float(pol.threshold_min):
				return False
			if pol.threshold_max and val > float(pol.threshold_max):
				return False
	return True


def list_matching_policies(business_doc: Document) -> list[str]:
	"""Active policies for this DocType that match document attributes, ordered for deterministic resolution."""
	rows = frappe.get_all(
		"KenTender Workflow Policy",
		filters={"applies_to_doctype": business_doc.doctype, "active": 1},
		fields=["name", "policy_code", "evaluation_order"],
	)
	matched: list[dict] = []
	for row in rows:
		if policy_matches_document(row.name, business_doc):
			matched.append(row)
	matched.sort(
		key=lambda r: (
			int(r.evaluation_order or 100),
			_norm_str(r.policy_code).lower(),
		)
	)
	return [r.name for r in matched]


def assert_no_blocking_sod(
	*,
	target_doctype: str,
	target_docname: str,
	proposed_user: str,
	proposed_action: str,
	participation_history: list[ParticipationRecord],
	proposed_role: str | None = None,
	scope_key: str | None = None,
) -> None:
	"""WF-009: thin wrapper around separation_of_duty_service."""
	if has_blocking_sod_violation(
		target_doctype=target_doctype,
		target_docname=target_docname,
		proposed_user=proposed_user,
		proposed_action=proposed_action,
		proposed_role=proposed_role,
		participation_history=participation_history,
		scope_key=scope_key,
	):
		frappe.throw(
			_("Separation of duty policy blocks this action."),
			frappe.ValidationError,
		)
