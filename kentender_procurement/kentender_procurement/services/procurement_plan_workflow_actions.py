# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Procurement Plan workflow: submit, approve, reject, return, activate (WF-PLAN-001 / spec v2 §7.2).

Uses :mod:`kentender.workflow_engine` route resolution and step execution (WF-007/WF-008).
State changes run inside :func:`kentender.workflow_engine.safeguards.workflow_mutation_context` (WF-002).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.services.audit_event_service import log_audit_event
from kentender.services.controlled_action_service import (
	ACTION_APPROVE,
	ACTION_SUBMIT,
	log_controlled_action_completed,
	run_controlled_action_gate,
)
from kentender.services.separation_of_duty_service import ParticipationRecord
from kentender.workflow_engine.actions import emit_post_transition, log_global_approval_action
from kentender.workflow_engine.execution import apply_step_decision, get_current_step_row
from kentender.workflow_engine.routes import get_active_route_instance, get_or_create_active_route
from kentender.workflow_engine.policies import assert_no_blocking_sod
from kentender.workflow_engine.safeguards import workflow_mutation_context

PP_DOCTYPE = "Procurement Plan"
PPAR_DOCTYPE = "Procurement Plan Approval Record"

SOURCE_MODULE = "kentender_procurement"

ACTION_REJECT = "reject"
ACTION_RETURN = "return_for_revision"
ACTION_ACTIVATE = "activate"

SOD_ACTION_SUBMIT = "submit"
SOD_ACTION_APPROVE = "approve"
SOD_ACTION_REJECT = "reject"
SOD_ACTION_RETURN = "return_for_revision"

WS_DRAFT = "Draft"
WS_SUBMITTED = "Submitted"
WS_APPROVED = "Approved"
WS_ACTIVE = "Active"
WS_REJECTED = "Rejected"
WS_RETURNED = "Returned"

PENDING_APPROVAL_STATES = frozenset({WS_SUBMITTED})

AUDIT_SUBMITTED = "kt.procurement.plan.submitted"
AUDIT_APPROVED = "kt.procurement.plan.approved"
AUDIT_REJECTED = "kt.procurement.plan.rejected"
AUDIT_RETURNED = "kt.procurement.plan.returned"
AUDIT_ACTIVATED = "kt.procurement.plan.activated"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _primary_role_for_user(user: str) -> str | None:
	roles = frappe.get_roles(user)
	skip = frozenset({"Guest", "All"})
	if "System Manager" in roles:
		return "System Manager"
	for r in roles:
		if r not in skip:
			return r
	return None


def _plan_context(doc: Document) -> dict[str, Any]:
	return {"procuring_entity": _norm(doc.get("procuring_entity"))}


def _audit_payload(doc: Document, **extra: Any) -> str:
	return json.dumps(
		{
			"name": doc.name,
			"workflow_state": _norm(doc.get("workflow_state")),
			"status": _norm(doc.get("status")),
			"approval_status": _norm(doc.get("approval_status")),
			**extra,
		},
		sort_keys=True,
		ensure_ascii=False,
	)


def _emit_plan_audit(
	*,
	event_type: str,
	doc: Document,
	actor: str,
	old_snapshot: dict[str, str],
	new_snapshot: dict[str, str],
	reason: str | None = None,
) -> None:
	log_audit_event(
		event_type=event_type,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=PP_DOCTYPE,
		target_docname=doc.name,
		procuring_entity=_norm(doc.get("procuring_entity")) or None,
		old_state=_audit_payload(doc, **old_snapshot),
		new_state=_audit_payload(doc, **new_snapshot),
		reason=reason,
	)


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


def _assert_route_template_supported(inst: Document) -> None:
	n = len(_ordered_route_steps(inst))
	if n < 1 or n > 2:
		frappe.throw(
			_("Procurement Plan approval routes must have 1 or 2 steps."),
			frappe.ValidationError,
			title=_("Unsupported route"),
		)


def _is_final_approval_step(inst: Document) -> bool:
	return int(inst.current_step_no or 0) >= _max_step_order(inst)


def _assert_plan_matches_active_route(doc: Document, inst: Document) -> None:
	_assert_route_template_supported(inst)
	got = _norm(doc.workflow_state)
	expected = WS_SUBMITTED
	if got != expected:
		frappe.throw(
			_("Plan stage {0!r} does not match the active approval route (expected {1!r}).").format(
				got, expected
			),
			frappe.ValidationError,
			title=_("Stage mismatch"),
		)


def _ppar_action_to_sod(action_type: str) -> str:
	m = {
		"Approve": SOD_ACTION_APPROVE,
		"Reject": SOD_ACTION_REJECT,
		"Return for Revision": SOD_ACTION_RETURN,
		"Recommend": "recommend",
		"Request Clarification": "request_clarification",
	}
	return m.get(_norm(action_type), _norm(action_type).lower().replace(" ", "_"))


def plan_participation_history(doc: Document) -> list[ParticipationRecord]:
	hist: list[ParticipationRecord] = []
	rb = _norm(doc.get("planning_owner_user")) or _norm(doc.get("procurement_owner_user"))
	ws = _norm(doc.get("workflow_state"))
	has_par = bool(frappe.db.exists(PPAR_DOCTYPE, {"procurement_plan": doc.name}))
	if rb and (ws not in ("", WS_DRAFT, WS_RETURNED) or has_par):
		hist.append(
			ParticipationRecord(
				user=rb,
				doctype=PP_DOCTYPE,
				docname=doc.name,
				action=SOD_ACTION_SUBMIT,
				role=_primary_role_for_user(rb),
			)
		)
	rows = frappe.get_all(
		PPAR_DOCTYPE,
		filters={"procurement_plan": doc.name},
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
				doctype=PP_DOCTYPE,
				docname=doc.name,
				action=_ppar_action_to_sod(at),
				role=role,
			)
		)
	return hist


def _assert_no_blocking_sod_plan(*, doc: Document, proposed_user: str, proposed_action: str) -> None:
	assert_no_blocking_sod(
		target_doctype=PP_DOCTYPE,
		target_docname=doc.name,
		proposed_user=proposed_user,
		proposed_action=proposed_action,
		participation_history=plan_participation_history(doc),
		proposed_role=_primary_role_for_user(proposed_user),
	)


def _insert_plan_approval_record(
	*,
	plan_name: str,
	workflow_step: str,
	decision_level: str,
	approver_user: str,
	action_type: str,
	comments: str | None = None,
	exception_record: str | None = None,
) -> Document:
	role = _primary_role_for_user(approver_user)
	rec = frappe.get_doc(
		{
			"doctype": PPAR_DOCTYPE,
			"procurement_plan": plan_name,
			"workflow_step": _norm(workflow_step),
			"decision_level": _norm(decision_level),
			"approver_user": approver_user,
			"approver_role": role,
			"action_type": action_type,
			"action_datetime": now_datetime(),
			"comments": _norm(comments) or None,
			"exception_record": _norm(exception_record) or None,
		}
	)
	rec.insert(ignore_permissions=True)
	return rec


def _assert_gate_ok(result: Any, action: str) -> None:
	if result.ok:
		return
	frappe.throw(
		_(result.failure_reason or "Action not allowed."),
		frappe.ValidationError,
		title=_("{0} blocked").format(_(action)),
	)


def submit_procurement_plan_for_approval(plan_name: str, *, user: str | None = None) -> Document:
	"""Draft or Returned → **Submitted**; resolves KenTender approval route (spec v2 §7.2)."""
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(PP_DOCTYPE, plan_name)
	ws = _norm(doc.workflow_state)
	if ws not in (WS_DRAFT, WS_RETURNED):
		frappe.throw(
			_("Only draft or returned plans can be submitted for approval."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)
	ctx = _plan_context(doc)
	res = run_controlled_action_gate(
		doctype=PP_DOCTYPE,
		docname=doc.name,
		action=ACTION_SUBMIT,
		user=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_SUBMIT)

	route_id = get_or_create_active_route(PP_DOCTYPE, doc.name)
	if not route_id:
		frappe.throw(
			_(
				"No active KenTender Workflow Policy matches this plan; cannot resolve an approval route."
			),
			frappe.ValidationError,
			title=_("No approval route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)

	if not _norm(doc.get("planning_owner_user")):
		doc.planning_owner_user = u

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_SUBMITTED
		doc.save()
	new = _state_snapshot(doc)

	log_global_approval_action(
		reference_doctype=PP_DOCTYPE,
		reference_docname=doc.name,
		action=ACTION_SUBMIT,
		actor_user=u,
		actor_role=_primary_role_for_user(u),
		previous_state=old,
		new_state=new,
		comments=_("Procurement plan submitted for approval."),
		route_instance=route_id,
		is_final_action=False,
	)
	emit_post_transition(
		doctype=PP_DOCTYPE,
		docname=doc.name,
		action=ACTION_SUBMIT,
		actor=u,
		context={"procuring_entity": ctx.get("procuring_entity"), "route_instance": route_id},
	)
	_emit_plan_audit(
		event_type=AUDIT_SUBMITTED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_("Procurement plan submitted."),
	)
	log_controlled_action_completed(
		action=ACTION_SUBMIT,
		doctype=PP_DOCTYPE,
		docname=doc.name,
		actor=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return doc


def approve_procurement_plan_step(
	plan_name: str,
	*,
	workflow_step: str,
	decision_level: str,
	comments: str | None = None,
	exception_record: str | None = None,
	user: str | None = None,
) -> Document:
	"""Advance one approval step; final step sets **Approved**."""
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(PP_DOCTYPE, plan_name)
	ws = _norm(doc.workflow_state)
	if ws not in PENDING_APPROVAL_STATES:
		frappe.throw(
			_("Approve is only allowed while the plan is pending approval."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	route_id = get_active_route_instance(PP_DOCTYPE, doc.name)
	if not route_id:
		frappe.throw(
			_("No active approval route for this plan."),
			frappe.ValidationError,
			title=_("Missing route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_plan_matches_active_route(doc, inst)

	owner = _norm(doc.get("planning_owner_user")) or _norm(doc.get("procurement_owner_user"))
	if owner and owner == u:
		frappe.throw(
			_("The planning owner cannot approve their own plan."),
			frappe.ValidationError,
			title=_("Self-approval"),
		)

	ctx = _plan_context(doc)
	res = run_controlled_action_gate(
		doctype=PP_DOCTYPE,
		docname=doc.name,
		action=ACTION_APPROVE,
		user=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_APPROVE)
	_assert_no_blocking_sod_plan(doc=doc, proposed_user=u, proposed_action=SOD_ACTION_APPROVE)

	step_row = get_current_step_row(inst)
	step_label = _norm(workflow_step) or (step_row.step_name if step_row else "")
	level_label = _norm(decision_level) or (
		f"L{int(inst.current_step_no or 0)}" if inst.current_step_no else "L1"
	)

	final = _is_final_approval_step(inst)
	new_ws = WS_APPROVED if final else WS_SUBMITTED

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = new_ws
		doc.save()

	_insert_plan_approval_record(
		plan_name=doc.name,
		workflow_step=step_label,
		decision_level=level_label,
		approver_user=u,
		action_type="Approve",
		comments=comments,
		exception_record=exception_record,
	)
	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Approve",
		user=u,
		comments=comments,
		reference_doctype=PP_DOCTYPE,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_APPROVE,
		hook_action=ACTION_APPROVE,
	)

	_emit_plan_audit(
		event_type=AUDIT_APPROVED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_("Procurement plan approved."),
	)
	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=PP_DOCTYPE,
		docname=doc.name,
		actor=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return doc


def reject_procurement_plan(
	plan_name: str,
	*,
	workflow_step: str,
	decision_level: str,
	comments: str | None = None,
	user: str | None = None,
) -> Document:
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(PP_DOCTYPE, plan_name)
	ws = _norm(doc.workflow_state)
	if ws not in PENDING_APPROVAL_STATES:
		frappe.throw(
			_("Reject is only allowed while the plan is pending approval."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	route_id = get_active_route_instance(PP_DOCTYPE, doc.name)
	if not route_id:
		frappe.throw(
			_("No active approval route for this plan."),
			frappe.ValidationError,
			title=_("Missing route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_plan_matches_active_route(doc, inst)

	ctx = _plan_context(doc)
	res = run_controlled_action_gate(
		doctype=PP_DOCTYPE,
		docname=doc.name,
		action=ACTION_REJECT,
		user=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_REJECT)
	_assert_no_blocking_sod_plan(doc=doc, proposed_user=u, proposed_action=SOD_ACTION_REJECT)

	step_row = get_current_step_row(inst)
	step_label = _norm(workflow_step) or (step_row.step_name if step_row else "")
	level_label = _norm(decision_level) or (
		f"L{int(inst.current_step_no or 0)}" if inst.current_step_no else "L1"
	)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_REJECTED
		doc.save()

	_insert_plan_approval_record(
		plan_name=doc.name,
		workflow_step=step_label,
		decision_level=level_label,
		approver_user=u,
		action_type="Reject",
		comments=comments,
	)
	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Reject",
		user=u,
		comments=comments,
		reference_doctype=PP_DOCTYPE,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_REJECT,
		hook_action=ACTION_REJECT,
	)

	_emit_plan_audit(
		event_type=AUDIT_REJECTED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_("Procurement plan rejected."),
	)
	log_controlled_action_completed(
		action=ACTION_REJECT,
		doctype=PP_DOCTYPE,
		docname=doc.name,
		actor=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return doc


def return_procurement_plan_for_revision(
	plan_name: str,
	*,
	workflow_step: str,
	decision_level: str,
	comments: str | None = None,
	user: str | None = None,
) -> Document:
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(PP_DOCTYPE, plan_name)
	ws = _norm(doc.workflow_state)
	if ws not in PENDING_APPROVAL_STATES:
		frappe.throw(
			_("Return for revision is only allowed while the plan is pending approval."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	route_id = get_active_route_instance(PP_DOCTYPE, doc.name)
	if not route_id:
		frappe.throw(
			_("No active approval route for this plan."),
			frappe.ValidationError,
			title=_("Missing route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_plan_matches_active_route(doc, inst)

	ctx = _plan_context(doc)
	res = run_controlled_action_gate(
		doctype=PP_DOCTYPE,
		docname=doc.name,
		action=ACTION_RETURN,
		user=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_RETURN)
	_assert_no_blocking_sod_plan(doc=doc, proposed_user=u, proposed_action=SOD_ACTION_RETURN)

	step_row = get_current_step_row(inst)
	step_label = _norm(workflow_step) or (step_row.step_name if step_row else "")
	level_label = _norm(decision_level) or (
		f"L{int(inst.current_step_no or 0)}" if inst.current_step_no else "L1"
	)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_RETURNED
		doc.save()

	_insert_plan_approval_record(
		plan_name=doc.name,
		workflow_step=step_label,
		decision_level=level_label,
		approver_user=u,
		action_type="Return for Revision",
		comments=comments,
	)
	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Return",
		user=u,
		comments=comments,
		reference_doctype=PP_DOCTYPE,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_RETURN,
		hook_action=ACTION_RETURN,
	)

	_emit_plan_audit(
		event_type=AUDIT_RETURNED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_("Procurement plan returned for revision."),
	)
	log_controlled_action_completed(
		action=ACTION_RETURN,
		doctype=PP_DOCTYPE,
		docname=doc.name,
		actor=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return doc


def activate_procurement_plan(plan_name: str, *, user: str | None = None) -> Document:
	"""Approved → **Active** (plan items become tender-eligible per spec §7.2)."""
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(PP_DOCTYPE, plan_name)
	if _norm(doc.workflow_state) != WS_APPROVED:
		frappe.throw(
			_("Only approved plans can be activated."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)
	ctx = _plan_context(doc)
	res = run_controlled_action_gate(
		doctype=PP_DOCTYPE,
		docname=doc.name,
		action=ACTION_ACTIVATE,
		user=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_ACTIVATE)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_ACTIVE
		doc.save()
	new = _state_snapshot(doc)

	_emit_plan_audit(
		event_type=AUDIT_ACTIVATED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_("Procurement plan activated."),
	)
	log_controlled_action_completed(
		action=ACTION_ACTIVATE,
		doctype=PP_DOCTYPE,
		docname=doc.name,
		actor=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return doc


@frappe.whitelist()
def submit_procurement_plan_for_approval_api(plan_name: str) -> str:
	doc = submit_procurement_plan_for_approval(plan_name)
	return doc.name


@frappe.whitelist()
def approve_procurement_plan_step_api(
	plan_name: str,
	workflow_step: str | None = None,
	decision_level: str | None = None,
	comments: str | None = None,
	exception_record: str | None = None,
) -> str:
	doc = approve_procurement_plan_step(
		plan_name,
		workflow_step=workflow_step or "",
		decision_level=decision_level or "",
		comments=comments,
		exception_record=exception_record,
	)
	return doc.name


@frappe.whitelist()
def activate_procurement_plan_api(plan_name: str) -> str:
	doc = activate_procurement_plan(plan_name)
	return doc.name
