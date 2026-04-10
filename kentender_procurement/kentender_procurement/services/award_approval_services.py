# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Award approval workflow, return, reject, and deviation gating (PROC-STORY-081, 082)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from kentender.services.audit_event_service import log_audit_event

AD = "Award Decision"
AAR = "Award Approval Record"
ARR = "Award Return Record"
ADR = "Award Deviation Record"
EA = "Evaluator Assignment"

SOURCE_MODULE = "kentender_procurement.award_approval_services"
EVT_STEP = "award.decision.approval_step"
EVT_FINAL = "award.decision.final_approved"
EVT_REJECT = "award.decision.rejected"
EVT_RETURN = "award.decision.returned_for_revision"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _procuring_entity_for_award(doc) -> str | None:
	tn = _norm(doc.tender)
	if not tn:
		return None
	return frappe.db.get_value("Tender", tn, "procuring_entity")


def _actor() -> str:
	return _norm(frappe.session.user) or "Administrator"


def _actor_role() -> str:
	roles = frappe.get_roles(_actor()) or ["Guest"]
	return roles[0]


def _assert_not_active_evaluator(evaluation_session_id: str, user: str) -> None:
	sn = _norm(evaluation_session_id)
	u = _norm(user)
	if not sn or not u:
		return
	if frappe.db.exists(
		EA,
		{"evaluation_session": sn, "evaluator_user": u, "assignment_status": "Active"},
	):
		frappe.throw(
			_("Active evaluators on this session cannot approve the award (separation of duty)."),
			frappe.ValidationError,
			title=_("Separation of duty"),
		)


def _material_deviation_from_recommendation(doc) -> bool:
	rb = _norm(doc.recommended_bid_submission)
	ab = _norm(doc.approved_bid_submission)
	rs = _norm(doc.recommended_supplier)
	asup = _norm(doc.approved_supplier)
	if not ab:
		return False
	if rb != ab or rs != asup:
		return True
	ra, aa = doc.recommended_amount, doc.approved_amount
	if ra is not None and aa is not None:
		try:
			if abs(float(ra) - float(aa)) > 1e-6:
				return True
		except (TypeError, ValueError):
			if str(ra) != str(aa):
				return True
	elif ra is not None or aa is not None:
		return True
	return False


def _assert_deviation_handling_complete(doc) -> None:
	if not _material_deviation_from_recommendation(doc):
		return
	if not int(doc.is_deviation_from_recommendation or 0):
		frappe.throw(
			_("Deviation from recommendation must be flagged before final approval."),
			frappe.ValidationError,
			title=_("Deviation required"),
		)
	dn = _norm(doc.deviation_record)
	if not dn:
		frappe.throw(
			_("Award Deviation Record is required when the approved outcome differs from the recommendation."),
			frappe.ValidationError,
			title=_("Missing deviation record"),
		)
	if not frappe.db.exists(ADR, dn):
		frappe.throw(_("Invalid deviation record."), frappe.ValidationError)
	ad_link = _norm(frappe.db.get_value(ADR, dn, "award_decision"))
	if ad_link != _norm(doc.name):
		frappe.throw(_("Deviation record must reference this award."), frappe.ValidationError)
	st = _norm(frappe.db.get_value(ADR, dn, "status"))
	if st != "Acknowledged":
		frappe.throw(
			_("Deviation handling must be acknowledged before final approval."),
			frappe.ValidationError,
			title=_("Deviation incomplete"),
		)


def approve_award_step(
	award_decision_id: str,
	*,
	workflow_step: str,
	decision_level: str,
	action_type: str = "Recommend",
	comments: str | None = None,
	actor_user: str | None = None,
) -> dict[str, Any]:
	"""Append an **Award Approval Record**; block active evaluators for this session."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	actor = _norm(actor_user) or _actor()
	doc = frappe.get_doc(AD, an)
	_assert_not_active_evaluator(doc.evaluation_session, actor)

	frappe.get_doc(
		{
			"doctype": AAR,
			"award_decision": an,
			"workflow_step": _norm(workflow_step) or "—",
			"decision_level": _norm(decision_level) or "—",
			"approver_user": actor,
			"approver_role": _actor_role() if actor == _actor() else (frappe.get_roles(actor) or ["Guest"])[0],
			"action_type": _norm(action_type) or "Recommend",
			"action_datetime": now_datetime(),
			"comments": _norm(comments) or None,
		}
	).insert(ignore_permissions=True)

	if _norm(doc.workflow_state) == "Draft":
		doc.workflow_state = "In Progress"
	if _norm(doc.approval_status) == "Draft":
		doc.approval_status = "Pending"
	doc.save(ignore_permissions=True)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_STEP,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"workflow_step": workflow_step, "action_type": action_type}),
		reason=_("Award approval step"),
		event_datetime=now_datetime(),
	)

	return {"name": an, "workflow_state": doc.workflow_state, "approval_status": doc.approval_status}


def final_approve_award(
	award_decision_id: str,
	*,
	comments: str | None = None,
	actor_user: str | None = None,
) -> dict[str, Any]:
	"""Final server-side approval; enforces deviation handling and separation of duty."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	actor = _norm(actor_user) or _actor()
	doc = frappe.get_doc(AD, an)
	_assert_not_active_evaluator(doc.evaluation_session, actor)
	_assert_deviation_handling_complete(doc)

	frappe.get_doc(
		{
			"doctype": AAR,
			"award_decision": an,
			"workflow_step": "Final",
			"decision_level": "Final",
			"approver_user": actor,
			"approver_role": _actor_role() if actor == _actor() else (frappe.get_roles(actor) or ["Guest"])[0],
			"action_type": "Approve",
			"action_datetime": now_datetime(),
			"comments": _norm(comments) or None,
		}
	).insert(ignore_permissions=True)

	ts = now_datetime()
	doc.status = "Approved"
	doc.workflow_state = "Approved"
	doc.approval_status = "Approved"
	doc.final_approval_datetime = ts
	doc.approval_decision_date = get_datetime(ts).date()
	if not int(doc.standstill_required or 0):
		doc.ready_for_contract_creation = 1
	else:
		doc.ready_for_contract_creation = 0
	doc.save(ignore_permissions=True)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_FINAL,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"status": "Approved"}),
		reason=_("Award final approval"),
		event_datetime=ts,
	)

	return {"name": an, "status": doc.status, "ready_for_contract_creation": doc.ready_for_contract_creation}


def reject_award(
	award_decision_id: str,
	*,
	comments: str | None = None,
	actor_user: str | None = None,
) -> dict[str, Any]:
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	actor = _norm(actor_user) or _actor()
	doc = frappe.get_doc(AD, an)
	_assert_not_active_evaluator(doc.evaluation_session, actor)

	frappe.get_doc(
		{
			"doctype": AAR,
			"award_decision": an,
			"workflow_step": "Final",
			"decision_level": "Final",
			"approver_user": actor,
			"approver_role": _actor_role() if actor == _actor() else (frappe.get_roles(actor) or ["Guest"])[0],
			"action_type": "Reject",
			"action_datetime": now_datetime(),
			"comments": _norm(comments) or None,
		}
	).insert(ignore_permissions=True)

	doc.status = "Rejected"
	doc.workflow_state = "Rejected"
	doc.approval_status = "Rejected"
	doc.ready_for_contract_creation = 0
	doc.save(ignore_permissions=True)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_REJECT,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"status": "Rejected"}),
		reason=_("Award rejected"),
		event_datetime=now_datetime(),
	)

	return {"name": an, "status": doc.status}


def return_award_for_revision(
	award_decision_id: str,
	*,
	return_reason: str,
	return_type: str = "Other",
	actor_user: str | None = None,
) -> dict[str, Any]:
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	actor = _norm(actor_user) or _actor()
	doc = frappe.get_doc(AD, an)
	_assert_not_active_evaluator(doc.evaluation_session, actor)

	if not _norm(return_reason):
		frappe.throw(_("Return reason is required."), frappe.ValidationError)

	frappe.get_doc(
		{
			"doctype": ARR,
			"award_decision": an,
			"returned_by_user": actor,
			"return_type": _norm(return_type) or "Other",
			"return_reason": _norm(return_reason),
			"returned_on": now_datetime(),
		}
	).insert(ignore_permissions=True)

	doc.workflow_state = "Returned"
	doc.status = "In Progress"
	doc.approval_status = "Draft"
	doc.ready_for_contract_creation = 0
	doc.save(ignore_permissions=True)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_RETURN,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"workflow_state": "Returned"}),
		reason=_("Award returned for revision"),
		event_datetime=now_datetime(),
	)

	return {"name": an, "workflow_state": doc.workflow_state}


def detect_award_deviation(award_decision_id: str) -> dict[str, Any]:
	"""Return whether the approved outcome materially differs from the recommendation (PROC-STORY-082)."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))
	doc = frappe.get_doc(AD, an)
	return {
		"material_deviation": _material_deviation_from_recommendation(doc),
		"flagged": bool(int(doc.is_deviation_from_recommendation or 0)),
		"deviation_record": _norm(doc.deviation_record) or None,
	}
