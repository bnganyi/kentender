# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Award approval workflow, return, reject, and deviation gating (PROC-STORY-081, 082).

WF-012: integrates with :mod:`kentender.workflow_engine` (routes, policies, ``apply_step_decision``).
State changes to ``workflow_state`` run inside :func:`kentender.workflow_engine.safeguards.workflow_mutation_context`.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime

from kentender.services.audit_event_service import log_audit_event
from kentender.services.controlled_action_service import (
	ACTION_APPROVE,
	ACTION_SUBMIT,
	log_controlled_action_completed,
	run_controlled_action_gate,
)

ACTION_REJECT = "reject"
ACTION_RETURN = "return_for_revision"
from kentender.services.separation_of_duty_service import ParticipationRecord
from kentender.workflow_engine.actions import emit_post_transition, log_global_approval_action
from kentender.workflow_engine.execution import apply_step_decision, get_current_step_row
from kentender.workflow_engine.policies import assert_no_blocking_sod
from kentender.workflow_engine.routes import get_active_route_instance, get_or_create_active_route
from kentender.workflow_engine.safeguards import workflow_mutation_context

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

SOD_ACTION_SUBMIT = "submit"
SOD_ACTION_APPROVE = "approve"
SOD_ACTION_REJECT = "reject"
SOD_ACTION_RETURN = "return_for_revision"

WS_DRAFT = "Draft"
WS_IN_PROGRESS = "In Progress"
WS_PENDING_APPROVAL = "Pending Approval"
WS_APPROVED = "Approved"
WS_REJECTED = "Rejected"
WS_RETURNED = "Returned"

PENDING_ROUTE_STATES = frozenset({WS_IN_PROGRESS, WS_PENDING_APPROVAL})


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _procuring_entity_for_award(doc: Document) -> str | None:
	tn = _norm(doc.tender)
	if not tn:
		return None
	return frappe.db.get_value("Tender", tn, "procuring_entity")


def _actor() -> str:
	return _norm(frappe.session.user) or "Administrator"


def _actor_role() -> str:
	roles = frappe.get_roles(_actor()) or ["Guest"]
	return roles[0]


def _primary_role_for_user(user: str) -> str | None:
	roles = frappe.get_roles(user)
	skip = frozenset({"Guest", "All"})
	if "System Manager" in roles:
		return "System Manager"
	for r in roles:
		if r not in skip:
			return r
	return None


def _award_context(doc: Document) -> dict[str, Any]:
	return {"procuring_entity": _procuring_entity_for_award(doc)}


def _state_snapshot(doc: Document) -> dict[str, str]:
	return {
		"workflow_state": _norm(doc.get("workflow_state")),
		"status": _norm(doc.get("status")),
		"approval_status": _norm(doc.get("approval_status")),
	}


def _ordered_route_steps(inst: Document) -> list:
	return sorted(inst.route_steps or [], key=lambda r: int(r.step_order or 0))


def _max_step_order(inst: Document) -> int:
	steps = _ordered_route_steps(inst)
	if not steps:
		return 0
	return max(int(s.step_order or 0) for s in steps)


def _is_final_approval_step(inst: Document) -> bool:
	return int(inst.current_step_no or 0) >= _max_step_order(inst)


def _assert_route_template_supported(inst: Document) -> None:
	n = len(_ordered_route_steps(inst))
	if n < 1 or n > 2:
		frappe.throw(
			_("Award Decision approval routes must have 1 or 2 steps."),
			frappe.ValidationError,
			title=_("Unsupported route"),
		)


def _assert_gate_ok(result: Any, action: str) -> None:
	if result.ok:
		return
	frappe.throw(
		_(result.failure_reason or "Action not allowed."),
		frappe.ValidationError,
		title=_("{0} blocked").format(_(action)),
	)


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


def _aar_action_to_sod(action_type: str) -> str:
	m = {
		"Approve": SOD_ACTION_APPROVE,
		"Reject": SOD_ACTION_REJECT,
		"Return for Revision": SOD_ACTION_RETURN,
		"Recommend": "recommend",
	}
	return m.get(_norm(action_type), _norm(action_type).lower().replace(" ", "_"))


def award_participation_history(doc: Document) -> list[ParticipationRecord]:
	hist: list[ParticipationRecord] = []
	rows = frappe.get_all(
		AAR,
		filters={"award_decision": doc.name},
		fields=["approver_user", "approver_role", "action_type"],
		order_by="creation asc",
	)
	for row in rows:
		u = _norm(row.get("approver_user"))
		if not u:
			continue
		at = row.get("action_type") or ""
		role = _norm(row.get("approver_role")) or None
		if not role:
			role = _primary_role_for_user(u)
		hist.append(
			ParticipationRecord(
				user=u,
				doctype=AD,
				docname=doc.name,
				action=_aar_action_to_sod(at),
				role=role,
			)
		)
	return hist


def _assert_no_blocking_sod_award(*, doc: Document, proposed_user: str, proposed_action: str) -> None:
	assert_no_blocking_sod(
		target_doctype=AD,
		target_docname=doc.name,
		proposed_user=proposed_user,
		proposed_action=proposed_action,
		participation_history=award_participation_history(doc),
		proposed_role=_primary_role_for_user(proposed_user),
	)


def _assert_award_matches_route_for_action(doc: Document, inst: Document) -> None:
	_assert_route_template_supported(inst)
	max_o = _max_step_order(inst)
	cur = int(inst.current_step_no or 0)
	got = _norm(doc.workflow_state)
	if max_o == 1:
		if got != WS_PENDING_APPROVAL:
			frappe.throw(
				_("Award stage {0!r} does not match the active route (expected {1!r}).").format(
					got, WS_PENDING_APPROVAL
				),
				frappe.ValidationError,
				title=_("Stage mismatch"),
			)
		return
	# Two-step: step 1 expects In Progress; step 2 expects Pending Approval
	if cur == 1 and got != WS_IN_PROGRESS:
		frappe.throw(
			_("Award stage {0!r} does not match route step 1 (expected {1!r}).").format(
				got, WS_IN_PROGRESS
			),
			frappe.ValidationError,
			title=_("Stage mismatch"),
		)
	if cur >= 2 and got != WS_PENDING_APPROVAL:
		frappe.throw(
			_("Award stage {0!r} does not match route step 2 (expected {1!r}).").format(
				got, WS_PENDING_APPROVAL
			),
			frappe.ValidationError,
			title=_("Stage mismatch"),
		)


def submit_award_for_approval(
	award_decision_id: str,
	*,
	actor_user: str | None = None,
) -> dict[str, Any]:
	"""Draft or Returned → approval pipeline; resolves KenTender approval route (WF-012)."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	actor = _norm(actor_user) or _actor()
	doc = frappe.get_doc(AD, an)
	ws = _norm(doc.workflow_state)
	if ws not in (WS_DRAFT, WS_RETURNED):
		frappe.throw(
			_("Only draft or returned awards can be submitted for approval."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	ctx = _award_context(doc)
	res = run_controlled_action_gate(
		doctype=AD,
		docname=doc.name,
		action=ACTION_SUBMIT,
		user=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_SUBMIT)

	route_id = get_or_create_active_route(AD, doc.name)
	if not route_id:
		frappe.throw(
			_("No active KenTender Workflow Policy matches this award; cannot resolve an approval route."),
			frappe.ValidationError,
			title=_("No approval route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)
	n_steps = _max_step_order(inst)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		if n_steps == 1:
			doc.workflow_state = WS_PENDING_APPROVAL
		else:
			doc.workflow_state = WS_IN_PROGRESS
		if _norm(doc.status) in ("", WS_DRAFT, WS_RETURNED):
			doc.status = WS_IN_PROGRESS
		doc.approval_status = "Pending"
		doc.save()

	new = _state_snapshot(doc)
	pe = _procuring_entity_for_award(doc)
	log_global_approval_action(
		reference_doctype=AD,
		reference_docname=doc.name,
		action=ACTION_SUBMIT,
		actor_user=actor,
		actor_role=_primary_role_for_user(actor),
		previous_state=old,
		new_state=new,
		comments=_("Award submitted for approval."),
		route_instance=route_id,
		is_final_action=False,
	)
	emit_post_transition(
		doctype=AD,
		docname=doc.name,
		action=ACTION_SUBMIT,
		actor=actor,
		context={"procuring_entity": pe, "route_instance": route_id},
	)
	log_audit_event(
		event_type=EVT_STEP,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"workflow_state": doc.workflow_state, "action": "submit"}),
		reason=_("Award submitted for approval"),
		event_datetime=now_datetime(),
	)
	log_controlled_action_completed(
		action=ACTION_SUBMIT,
		doctype=AD,
		docname=doc.name,
		actor=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return {"name": an, "workflow_state": doc.workflow_state, "approval_status": doc.approval_status, "route_instance": route_id}


def approve_award_step(
	award_decision_id: str,
	*,
	workflow_step: str,
	decision_level: str,
	action_type: str = "Recommend",
	comments: str | None = None,
	actor_user: str | None = None,
) -> dict[str, Any]:
	"""Non-final step: append **Award Approval Record** and advance the route (two-step templates only)."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	actor = _norm(actor_user) or _actor()
	doc = frappe.get_doc(AD, an)
	_assert_not_active_evaluator(doc.evaluation_session, actor)

	route_id = get_active_route_instance(AD, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route for this award."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)
	if _is_final_approval_step(inst):
		frappe.throw(
			_("Use final approval for the last route step."),
			frappe.ValidationError,
			title=_("Invalid action"),
		)

	_assert_award_matches_route_for_action(doc, inst)

	ctx = _award_context(doc)
	res = run_controlled_action_gate(
		doctype=AD,
		docname=doc.name,
		action=ACTION_APPROVE,
		user=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_APPROVE)
	_assert_no_blocking_sod_award(doc=doc, proposed_user=actor, proposed_action=SOD_ACTION_APPROVE)

	step_row = get_current_step_row(inst)
	step_label = _norm(workflow_step) or (step_row.step_name if step_row else "")
	level_label = _norm(decision_level) or (
		f"L{int(inst.current_step_no or 0)}" if inst.current_step_no else "L1"
	)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_PENDING_APPROVAL
		doc.save()

	frappe.get_doc(
		{
			"doctype": AAR,
			"award_decision": an,
			"workflow_step": step_label or "—",
			"decision_level": level_label or "—",
			"approver_user": actor,
			"approver_role": _actor_role() if actor == _actor() else (frappe.get_roles(actor) or ["Guest"])[0],
			"action_type": _norm(action_type) or "Recommend",
			"action_datetime": now_datetime(),
			"comments": _norm(comments) or None,
		}
	).insert(ignore_permissions=True)

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Approve",
		user=actor,
		comments=comments,
		reference_doctype=AD,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_APPROVE,
		hook_action=ACTION_APPROVE,
	)

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
	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=AD,
		docname=doc.name,
		actor=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
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

	route_id = get_active_route_instance(AD, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route for this award."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)
	if not _is_final_approval_step(inst):
		frappe.throw(
			_("Complete earlier approval steps before final approval."),
			frappe.ValidationError,
			title=_("Not final step"),
		)
	_assert_award_matches_route_for_action(doc, inst)

	ctx = _award_context(doc)
	res = run_controlled_action_gate(
		doctype=AD,
		docname=doc.name,
		action=ACTION_APPROVE,
		user=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_APPROVE)
	_assert_no_blocking_sod_award(doc=doc, proposed_user=actor, proposed_action=SOD_ACTION_APPROVE)

	ts = now_datetime()
	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.status = WS_APPROVED
		doc.workflow_state = WS_APPROVED
		doc.approval_status = WS_APPROVED
		doc.final_approval_datetime = ts
		doc.approval_decision_date = get_datetime(ts).date()
		if not int(doc.standstill_required or 0):
			doc.ready_for_contract_creation = 1
		else:
			doc.ready_for_contract_creation = 0
		doc.save()

	frappe.get_doc(
		{
			"doctype": AAR,
			"award_decision": an,
			"workflow_step": "Final",
			"decision_level": "Final",
			"approver_user": actor,
			"approver_role": _actor_role() if actor == _actor() else (frappe.get_roles(actor) or ["Guest"])[0],
			"action_type": "Approve",
			"action_datetime": ts,
			"comments": _norm(comments) or None,
		}
	).insert(ignore_permissions=True)

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Approve",
		user=actor,
		comments=comments,
		reference_doctype=AD,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_APPROVE,
		hook_action=ACTION_APPROVE,
	)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_FINAL,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"status": WS_APPROVED}),
		reason=_("Award final approval"),
		event_datetime=ts,
	)
	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=AD,
		docname=doc.name,
		actor=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
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

	ws = _norm(doc.workflow_state)
	if ws not in PENDING_ROUTE_STATES:
		frappe.throw(
			_("Reject is only allowed while the award is in the approval pipeline."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	route_id = get_active_route_instance(AD, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route for this award."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)
	_assert_award_matches_route_for_action(doc, inst)

	ctx = _award_context(doc)
	res = run_controlled_action_gate(
		doctype=AD,
		docname=doc.name,
		action=ACTION_REJECT,
		user=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_REJECT)
	_assert_no_blocking_sod_award(doc=doc, proposed_user=actor, proposed_action=SOD_ACTION_REJECT)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.status = WS_REJECTED
		doc.workflow_state = WS_REJECTED
		doc.approval_status = WS_REJECTED
		doc.ready_for_contract_creation = 0
		doc.save()

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

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Reject",
		user=actor,
		comments=comments,
		reference_doctype=AD,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_REJECT,
		hook_action=ACTION_REJECT,
	)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_REJECT,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"status": WS_REJECTED}),
		reason=_("Award rejected"),
		event_datetime=now_datetime(),
	)
	log_controlled_action_completed(
		action=ACTION_REJECT,
		doctype=AD,
		docname=doc.name,
		actor=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
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

	ws = _norm(doc.workflow_state)
	if ws not in PENDING_ROUTE_STATES:
		frappe.throw(
			_("Return is only allowed while the award is in the approval pipeline."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	route_id = get_active_route_instance(AD, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route for this award."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)
	_assert_award_matches_route_for_action(doc, inst)

	ctx = _award_context(doc)
	res = run_controlled_action_gate(
		doctype=AD,
		docname=doc.name,
		action=ACTION_RETURN,
		user=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_RETURN)
	_assert_no_blocking_sod_award(doc=doc, proposed_user=actor, proposed_action=SOD_ACTION_RETURN)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_RETURNED
		doc.status = WS_IN_PROGRESS
		doc.approval_status = WS_DRAFT
		doc.ready_for_contract_creation = 0
		doc.save()

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

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Return",
		user=actor,
		comments=return_reason,
		reference_doctype=AD,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action="return_for_revision",
		hook_action="return_for_revision",
	)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_RETURN,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"workflow_state": WS_RETURNED}),
		reason=_("Award returned for revision"),
		event_datetime=now_datetime(),
	)
	log_controlled_action_completed(
		action=ACTION_RETURN,
		doctype=AD,
		docname=doc.name,
		actor=actor,
		procuring_entity=ctx.get("procuring_entity") or None,
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
