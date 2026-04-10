# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Purchase Requisition workflow actions: submit, approve, reject, return (PROC-STORY-005, WF-011).

Authorization uses **PERM-005** via :func:`kentender.services.controlled_action_service.run_controlled_action_gate`
(re-exported from :mod:`kentender.permissions.actions` for documentation parity).

State mutations use :func:`kentender.workflow_engine.safeguards.workflow_mutation_context` (WF-002).
Route resolution uses :mod:`kentender.workflow_engine.routes`; step execution uses
:mod:`kentender.workflow_engine.execution` (WF-007/WF-008). Spec: **KenTender Approval Workflow Specification v2** §7.1.
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
from kentender.services.separation_of_duty_service import (
	ParticipationRecord,
	has_blocking_sod_violation,
)
from kentender.workflow_engine.actions import emit_post_transition, log_global_approval_action
from kentender.workflow_engine.execution import apply_step_decision, get_current_step_row
from kentender.workflow_engine.routes import get_active_route_instance, get_or_create_active_route
from kentender.workflow_engine.safeguards import workflow_mutation_context
from kentender_procurement.services.requisition_budget_reservation import (
	apply_budget_reservation_on_final_approve,
)

PR_DOCTYPE = "Purchase Requisition"
RAR_DOCTYPE = "Requisition Approval Record"

SOURCE_MODULE = "kentender_procurement"

AUDIT_SUBMITTED = "kt.procurement.requisition.submitted"
AUDIT_APPROVED = "kt.procurement.requisition.approved"
AUDIT_REJECTED = "kt.procurement.requisition.rejected"
AUDIT_RETURNED = "kt.procurement.requisition.returned_for_revision"

ACTION_REJECT = "reject"
ACTION_RETURN = "return_for_revision"

SOD_ACTION_SUBMIT = "submit"
SOD_ACTION_APPROVE = "approve"
SOD_ACTION_REJECT = "reject"
SOD_ACTION_RETURN = "return_for_revision"
SOD_ACTION_RECOMMEND = "recommend"
SOD_ACTION_CLARIFY = "request_clarification"

WS_DRAFT = "Draft"
WS_PENDING_HOD = "Pending HOD Approval"
WS_PENDING_FINANCE = "Pending Finance Approval"
WS_APPROVED = "Approved"
WS_REJECTED = "Rejected"
WS_RETURNED = "Returned for Amendment"
WS_CANCELLED = "Cancelled"

PENDING_APPROVAL_STATES = frozenset({WS_PENDING_HOD, WS_PENDING_FINANCE})


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


def _rar_action_to_sod(action_type: str) -> str:
	m = {
		"Approve": SOD_ACTION_APPROVE,
		"Reject": SOD_ACTION_REJECT,
		"Return for Revision": SOD_ACTION_RETURN,
		"Recommend": SOD_ACTION_RECOMMEND,
		"Request Clarification": SOD_ACTION_CLARIFY,
	}
	return m.get(_norm(action_type), _norm(action_type).lower().replace(" ", "_"))


def _assert_gate_ok(result: Any, action: str) -> None:
	if result.ok:
		return
	frappe.throw(
		_(result.failure_reason or "Action not allowed."),
		frappe.ValidationError,
		title=_("{0} blocked").format(_(action)),
	)


def _procurement_context(doc: Document) -> dict[str, Any]:
	return {
		"procuring_entity": _norm(doc.get("procuring_entity")),
	}


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


def _emit_procurement_audit(
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
		target_doctype=PR_DOCTYPE,
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
			_("Purchase Requisition approval routes must have 1 or 2 steps (WF-011)."),
			frappe.ValidationError,
			title=_("Unsupported route"),
		)


def _expected_pr_state_for_route(inst: Document) -> str:
	_assert_route_template_supported(inst)
	steps = _ordered_route_steps(inst)
	n = len(steps)
	cur = int(inst.current_step_no or 0)
	if n == 1:
		return WS_PENDING_HOD if cur == 1 else ""
	if cur == 1:
		return WS_PENDING_HOD
	if cur == 2:
		return WS_PENDING_FINANCE
	return ""


def _assert_pr_matches_active_route(doc: Document, inst: Document) -> None:
	expected = _expected_pr_state_for_route(inst)
	got = _norm(doc.workflow_state)
	if got != expected:
		frappe.throw(
			_(
				"Requisition stage {0!r} does not match the active approval route (expected {1!r})."
			).format(got, expected),
			frappe.ValidationError,
			title=_("Stage mismatch"),
		)


def _is_final_approval_step(inst: Document) -> bool:
	return int(inst.current_step_no or 0) >= _max_step_order(inst)


def requisition_participation_history(doc: Document) -> list[ParticipationRecord]:
	"""Build SoD participation from submitter (synthetic) and prior approval rows."""
	hist: list[ParticipationRecord] = []
	rb = _norm(doc.get("requested_by_user"))
	ws = _norm(doc.get("workflow_state"))
	has_rar = bool(
		frappe.db.exists(RAR_DOCTYPE, {"purchase_requisition": doc.name})
	)
	if rb and (ws not in ("", "Draft") or has_rar):
		hist.append(
			ParticipationRecord(
				user=rb,
				doctype=PR_DOCTYPE,
				docname=doc.name,
				action=SOD_ACTION_SUBMIT,
				role=_primary_role_for_user(rb),
			)
		)
	rows = frappe.get_all(
		RAR_DOCTYPE,
		filters={"purchase_requisition": doc.name},
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
				doctype=PR_DOCTYPE,
				docname=doc.name,
				action=_rar_action_to_sod(at),
				role=role,
			)
		)
	return hist


def _assert_no_blocking_sod(
	*,
	doc: Document,
	proposed_user: str,
	proposed_action: str,
) -> None:
	if has_blocking_sod_violation(
		target_doctype=PR_DOCTYPE,
		target_docname=doc.name,
		proposed_user=proposed_user,
		proposed_action=proposed_action,
		proposed_role=_primary_role_for_user(proposed_user),
		participation_history=requisition_participation_history(doc),
	):
		frappe.throw(
			_("Separation of duty policy blocks this action."),
			frappe.ValidationError,
			title=_("Conflict of duty"),
		)


def _insert_approval_record(
	*,
	pr_name: str,
	workflow_step: str,
	decision_level: str,
	approver_user: str,
	action_type: str,
	comments: str | None = None,
	exception_record: str | None = None,
) -> Document:
	role = _primary_role_for_user(approver_user)
	rar = frappe.get_doc(
		{
			"doctype": RAR_DOCTYPE,
			"purchase_requisition": pr_name,
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
	rar.insert(ignore_permissions=True)
	return rar


def submit_requisition(pr_name: str, *, user: str | None = None) -> Document:
	"""Draft or Returned for Amendment → **Pending HOD Approval**; resolves workflow route (WF-011)."""
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(PR_DOCTYPE, pr_name)
	ws = _norm(doc.workflow_state)
	if ws not in (WS_DRAFT, WS_RETURNED):
		frappe.throw(
			_("Only draft or returned-for-amendment requisitions can be submitted."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)
	ctx = _procurement_context(doc)
	res = run_controlled_action_gate(
		doctype=PR_DOCTYPE,
		docname=doc.name,
		action=ACTION_SUBMIT,
		user=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_SUBMIT)

	route_id = get_or_create_active_route(PR_DOCTYPE, doc.name)
	if not route_id:
		frappe.throw(
			_(
				"No active KenTender Workflow Policy matches this requisition; "
				"cannot resolve an approval route."
			),
			frappe.ValidationError,
			title=_("No approval route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)

	old = _state_snapshot(doc)
	if not _norm(doc.requested_by_user):
		doc.requested_by_user = u
	with workflow_mutation_context():
		doc.workflow_state = WS_PENDING_HOD
		doc.save()
	new = _state_snapshot(doc)

	log_global_approval_action(
		reference_doctype=PR_DOCTYPE,
		reference_docname=doc.name,
		action=ACTION_SUBMIT,
		actor_user=u,
		actor_role=_primary_role_for_user(u),
		previous_state=old,
		new_state=new,
		comments=_("Requisition submitted."),
		route_instance=route_id,
		is_final_action=False,
	)
	emit_post_transition(
		doctype=PR_DOCTYPE,
		docname=doc.name,
		action=ACTION_SUBMIT,
		actor=u,
		context={"procuring_entity": ctx.get("procuring_entity"), "route_instance": route_id},
	)

	_emit_procurement_audit(
		event_type=AUDIT_SUBMITTED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_("Requisition submitted."),
	)
	log_controlled_action_completed(
		action=ACTION_SUBMIT,
		doctype=PR_DOCTYPE,
		docname=doc.name,
		actor=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return doc


def approve_requisition_step(
	pr_name: str,
	*,
	workflow_step: str,
	decision_level: str,
	comments: str | None = None,
	exception_record: str | None = None,
	user: str | None = None,
) -> Document:
	"""Advance one approval step; final step sets **Approved** and runs budget reservation."""
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(PR_DOCTYPE, pr_name)
	ws = _norm(doc.workflow_state)
	if ws not in PENDING_APPROVAL_STATES:
		frappe.throw(
			_("Approve is only allowed while the requisition is pending approval."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	route_id = get_active_route_instance(PR_DOCTYPE, doc.name)
	if not route_id:
		frappe.throw(
			_("No active approval route for this requisition."),
			frappe.ValidationError,
			title=_("Missing route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_pr_matches_active_route(doc, inst)

	rb = _norm(doc.requested_by_user)
	if rb and rb == u:
		frappe.throw(
			_("The requester cannot approve their own requisition."),
			frappe.ValidationError,
			title=_("Self-approval"),
		)

	ctx = _procurement_context(doc)
	res = run_controlled_action_gate(
		doctype=PR_DOCTYPE,
		docname=doc.name,
		action=ACTION_APPROVE,
		user=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_APPROVE)
	_assert_no_blocking_sod(doc=doc, proposed_user=u, proposed_action=SOD_ACTION_APPROVE)

	step_row = get_current_step_row(inst)
	step_label = _norm(workflow_step) or (step_row.step_name if step_row else "")
	level_label = _norm(decision_level) or (
		f"L{int(inst.current_step_no or 0)}" if inst.current_step_no else "L1"
	)

	final = _is_final_approval_step(inst)
	if final:
		apply_budget_reservation_on_final_approve(doc)

	old = _state_snapshot(doc)
	new_ws = WS_APPROVED if final else WS_PENDING_FINANCE
	with workflow_mutation_context():
		doc.workflow_state = new_ws
		doc.save()

	_insert_approval_record(
		pr_name=doc.name,
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
		reference_doctype=PR_DOCTYPE,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_APPROVE,
		hook_action=ACTION_APPROVE,
	)

	_emit_procurement_audit(
		event_type=AUDIT_APPROVED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_("Requisition approved."),
	)
	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=PR_DOCTYPE,
		docname=doc.name,
		actor=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return doc


def reject_requisition(
	pr_name: str,
	*,
	workflow_step: str,
	decision_level: str,
	comments: str | None = None,
	user: str | None = None,
) -> Document:
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(PR_DOCTYPE, pr_name)
	ws = _norm(doc.workflow_state)
	if ws not in PENDING_APPROVAL_STATES:
		frappe.throw(
			_("Reject is only allowed while the requisition is pending approval."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	route_id = get_active_route_instance(PR_DOCTYPE, doc.name)
	if not route_id:
		frappe.throw(
			_("No active approval route for this requisition."),
			frappe.ValidationError,
			title=_("Missing route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_pr_matches_active_route(doc, inst)

	ctx = _procurement_context(doc)
	res = run_controlled_action_gate(
		doctype=PR_DOCTYPE,
		docname=doc.name,
		action=ACTION_REJECT,
		user=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_REJECT)
	_assert_no_blocking_sod(doc=doc, proposed_user=u, proposed_action=SOD_ACTION_REJECT)

	step_row = get_current_step_row(inst)
	step_label = _norm(workflow_step) or (step_row.step_name if step_row else "")
	level_label = _norm(decision_level) or (
		f"L{int(inst.current_step_no or 0)}" if inst.current_step_no else "L1"
	)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_REJECTED
		doc.save()

	_insert_approval_record(
		pr_name=doc.name,
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
		reference_doctype=PR_DOCTYPE,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_REJECT,
		hook_action=ACTION_REJECT,
	)

	_emit_procurement_audit(
		event_type=AUDIT_REJECTED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_("Requisition rejected."),
	)
	log_controlled_action_completed(
		action=ACTION_REJECT,
		doctype=PR_DOCTYPE,
		docname=doc.name,
		actor=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return doc


def return_requisition_for_revision(
	pr_name: str,
	*,
	workflow_step: str,
	decision_level: str,
	comments: str | None = None,
	user: str | None = None,
) -> Document:
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(PR_DOCTYPE, pr_name)
	ws = _norm(doc.workflow_state)
	if ws not in PENDING_APPROVAL_STATES:
		frappe.throw(
			_("Return for revision is only allowed while the requisition is pending approval."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	route_id = get_active_route_instance(PR_DOCTYPE, doc.name)
	if not route_id:
		frappe.throw(
			_("No active approval route for this requisition."),
			frappe.ValidationError,
			title=_("Missing route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_pr_matches_active_route(doc, inst)

	ctx = _procurement_context(doc)
	res = run_controlled_action_gate(
		doctype=PR_DOCTYPE,
		docname=doc.name,
		action=ACTION_RETURN,
		user=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	_assert_gate_ok(res, ACTION_RETURN)
	_assert_no_blocking_sod(doc=doc, proposed_user=u, proposed_action=SOD_ACTION_RETURN)

	step_row = get_current_step_row(inst)
	step_label = _norm(workflow_step) or (step_row.step_name if step_row else "")
	level_label = _norm(decision_level) or (
		f"L{int(inst.current_step_no or 0)}" if inst.current_step_no else "L1"
	)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_RETURNED
		doc.save()

	_insert_approval_record(
		pr_name=doc.name,
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
		reference_doctype=PR_DOCTYPE,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_RETURN,
		hook_action=ACTION_RETURN,
	)

	_emit_procurement_audit(
		event_type=AUDIT_RETURNED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_("Requisition returned for revision."),
	)
	log_controlled_action_completed(
		action=ACTION_RETURN,
		doctype=PR_DOCTYPE,
		docname=doc.name,
		actor=u,
		procuring_entity=ctx.get("procuring_entity") or None,
	)
	return doc


def approve_requisition_hod(
	pr_name: str,
	*,
	comments: str | None = None,
	exception_record: str | None = None,
	user: str | None = None,
) -> Document:
	"""Convenience wrapper: approve current step (expected first / HOD stage)."""
	return approve_requisition_step(
		pr_name,
		workflow_step="HOD",
		decision_level="L1",
		comments=comments,
		exception_record=exception_record,
		user=user,
	)


def approve_requisition_finance(
	pr_name: str,
	*,
	comments: str | None = None,
	exception_record: str | None = None,
	user: str | None = None,
) -> Document:
	"""Convenience wrapper: approve current step (expected finance stage)."""
	return approve_requisition_step(
		pr_name,
		workflow_step="Finance",
		decision_level="L2",
		comments=comments,
		exception_record=exception_record,
		user=user,
	)
