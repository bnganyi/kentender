# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-014: Acceptance Record workflow via :mod:`kentender.workflow_engine`.

Requires :func:`submit_acceptance_decision` with ``use_engine_workflow=True`` so the record starts in **Draft**.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.services.controlled_action_service import (
	ACTION_APPROVE,
	ACTION_SUBMIT,
	log_controlled_action_completed,
	run_controlled_action_gate,
)

ACTION_REJECT = "reject"
from kentender.workflow_engine.actions import emit_post_transition, log_global_approval_action
from kentender.workflow_engine.execution import apply_step_decision, get_current_step_row
from kentender.workflow_engine.routes import get_active_route_instance, get_or_create_active_route
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_procurement.services.acceptance_decision_services import (
	_append_acceptance_event,
	sync_inspection_acceptance_status_from_record,
)

AR = "Acceptance Record"
IR = "Inspection Record"

ACTION_RETURN = "return_for_revision"

WS_DRAFT = "Draft"
WS_IN_REVIEW = "In Review"
WS_PENDING_APPROVAL = "Pending Approval"
WS_APPROVED = "Approved"
WS_REJECTED = "Rejected"

ST_DRAFT = "Draft"
ST_SUBMITTED = "Submitted"
ST_APPROVED = "Approved"
ST_REJECTED = "Rejected"

PENDING_ROUTE_STATES = frozenset({WS_IN_REVIEW, WS_PENDING_APPROVAL})


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


def _procuring_entity(doc: Document) -> str | None:
	pe = _norm(doc.get("procuring_entity"))
	if pe:
		return pe
	cn = _norm(doc.get("contract"))
	if not cn:
		return None
	return frappe.db.get_value("Procurement Contract", cn, "procuring_entity")


def _state_snapshot(doc: Document) -> dict[str, str]:
	return {
		"workflow_state": _norm(doc.get("workflow_state")),
		"status": _norm(doc.get("status")),
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
			_("Acceptance Record approval routes must have 1 or 2 steps."),
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


def _assert_acceptance_matches_route(doc: Document, inst: Document) -> None:
	_assert_route_template_supported(inst)
	max_o = _max_step_order(inst)
	cur = int(inst.current_step_no or 0)
	got = _norm(doc.workflow_state)
	if max_o == 1:
		if got != WS_PENDING_APPROVAL:
			frappe.throw(
				_("Acceptance stage {0!r} does not match the active route (expected {1!r}).").format(
					got, WS_PENDING_APPROVAL
				),
				frappe.ValidationError,
				title=_("Stage mismatch"),
			)
		return
	if cur == 1 and got != WS_IN_REVIEW:
		frappe.throw(
			_("Acceptance stage {0!r} does not match route step 1 (expected {1!r}).").format(
				got, WS_IN_REVIEW
			),
			frappe.ValidationError,
			title=_("Stage mismatch"),
		)
	if cur >= 2 and got != WS_PENDING_APPROVAL:
		frappe.throw(
			_("Acceptance stage {0!r} does not match route step 2 (expected {1!r}).").format(
				got, WS_PENDING_APPROVAL
			),
			frappe.ValidationError,
			title=_("Stage mismatch"),
		)


def submit_acceptance_for_approval(acceptance_record_id: str, *, user: str | None = None) -> dict[str, Any]:
	"""Draft → approval pipeline; resolves KenTender approval route (WF-014)."""
	an = _norm(acceptance_record_id)
	if not an or not frappe.db.exists(AR, an):
		frappe.throw(_("Acceptance Record not found."), frappe.ValidationError)

	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(AR, an)
	if _norm(doc.workflow_state) != WS_DRAFT:
		frappe.throw(
			_("Only draft acceptance records can be submitted for approval."),
			frappe.ValidationError,
			title=_("Invalid state"),
		)

	pe = _procuring_entity(doc)
	res = run_controlled_action_gate(
		doctype=AR,
		docname=doc.name,
		action=ACTION_SUBMIT,
		user=u,
		procuring_entity=pe,
	)
	_assert_gate_ok(res, ACTION_SUBMIT)

	route_id = get_or_create_active_route(AR, doc.name)
	if not route_id:
		frappe.throw(
			_("No active KenTender Workflow Policy matches this acceptance record; cannot resolve an approval route."),
			frappe.ValidationError,
			title=_("No approval route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)
	n_steps = _max_step_order(inst)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.status = ST_SUBMITTED
		if n_steps == 1:
			doc.workflow_state = WS_PENDING_APPROVAL
		else:
			doc.workflow_state = WS_IN_REVIEW
		doc.save()

	new = _state_snapshot(doc)
	log_global_approval_action(
		reference_doctype=AR,
		reference_docname=doc.name,
		action=ACTION_SUBMIT,
		actor_user=u,
		actor_role=_primary_role_for_user(u),
		previous_state=old,
		new_state=new,
		comments=_("Acceptance submitted for approval."),
		route_instance=route_id,
		is_final_action=False,
	)
	emit_post_transition(
		doctype=AR,
		docname=doc.name,
		action=ACTION_SUBMIT,
		actor=u,
		context={"route_instance": route_id},
	)
	log_controlled_action_completed(
		action=ACTION_SUBMIT,
		doctype=AR,
		docname=doc.name,
		actor=u,
		procuring_entity=pe,
	)
	return {"name": an, "workflow_state": doc.workflow_state, "status": doc.status, "route_instance": route_id}


def approve_acceptance_step(
	acceptance_record_id: str,
	*,
	workflow_step: str | None = None,
	decision_level: str | None = None,
	comments: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Non-final route step (two-step templates)."""
	an = _norm(acceptance_record_id)
	doc = frappe.get_doc(AR, an)

	route_id = get_active_route_instance(AR, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	if _is_final_approval_step(inst):
		frappe.throw(_("Use approve_acceptance for the final step."), frappe.ValidationError, title=_("Invalid action"))
	_assert_acceptance_matches_route(doc, inst)

	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	pe = _procuring_entity(doc)
	res = run_controlled_action_gate(
		doctype=AR,
		docname=doc.name,
		action=ACTION_APPROVE,
		user=u,
		procuring_entity=pe,
	)
	_assert_gate_ok(res, ACTION_APPROVE)

	step_row = get_current_step_row(inst)
	step_label = _norm(workflow_step) or (step_row.step_name if step_row else "Review")
	level_label = _norm(decision_level) or (
		f"L{int(inst.current_step_no or 0)}" if inst.current_step_no else "L1"
	)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_PENDING_APPROVAL
		doc.save()

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Approve",
		user=u,
		comments=comments,
		reference_doctype=AR,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_APPROVE,
		hook_action=ACTION_APPROVE,
	)
	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=AR,
		docname=doc.name,
		actor=u,
		procuring_entity=pe,
	)
	return {"name": an, "workflow_state": doc.workflow_state, "workflow_step": step_label, "decision_level": level_label}


def approve_acceptance(
	acceptance_record_id: str,
	*,
	comments: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Final approval: workflow **Approved**, sync inspection status, emit inspection event."""
	an = _norm(acceptance_record_id)
	doc = frappe.get_doc(AR, an)

	route_id = get_active_route_instance(AR, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	if not _is_final_approval_step(inst):
		frappe.throw(_("Complete earlier steps first."), frappe.ValidationError, title=_("Not final step"))
	_assert_acceptance_matches_route(doc, inst)

	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	pe = _procuring_entity(doc)
	res = run_controlled_action_gate(
		doctype=AR,
		docname=doc.name,
		action=ACTION_APPROVE,
		user=u,
		procuring_entity=pe,
	)
	_assert_gate_ok(res, ACTION_APPROVE)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_APPROVED
		doc.status = ST_APPROVED
		doc.approved_by_user = u
		doc.decision_datetime = now_datetime()
		doc.save()

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Approve",
		user=u,
		comments=comments,
		reference_doctype=AR,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_APPROVE,
		hook_action=ACTION_APPROVE,
	)

	sync_inspection_acceptance_status_from_record(doc.name)
	irn = _norm(doc.inspection_record)
	ad = _norm(doc.acceptance_decision)
	if irn:
		_append_acceptance_event(
			irn,
			doc.name,
			ad,
			summary_notes=_norm(comments),
			actor_user=u,
		)

	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=AR,
		docname=doc.name,
		actor=u,
		procuring_entity=pe,
	)
	return {"name": an, "workflow_state": doc.workflow_state, "status": doc.status}


def reject_acceptance(
	acceptance_record_id: str,
	*,
	comments: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	an = _norm(acceptance_record_id)
	doc = frappe.get_doc(AR, an)
	if _norm(doc.workflow_state) not in PENDING_ROUTE_STATES:
		frappe.throw(_("Reject is only allowed during approval."), frappe.ValidationError, title=_("Invalid state"))

	route_id = get_active_route_instance(AR, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_acceptance_matches_route(doc, inst)

	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	pe = _procuring_entity(doc)
	res = run_controlled_action_gate(
		doctype=AR,
		docname=doc.name,
		action=ACTION_REJECT,
		user=u,
		procuring_entity=pe,
	)
	_assert_gate_ok(res, ACTION_REJECT)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_REJECTED
		doc.status = ST_REJECTED
		doc.save()

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Reject",
		user=u,
		comments=comments,
		reference_doctype=AR,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_REJECT,
		hook_action=ACTION_REJECT,
	)

	sync_inspection_acceptance_status_from_record(doc.name)
	log_controlled_action_completed(
		action=ACTION_REJECT,
		doctype=AR,
		docname=doc.name,
		actor=u,
		procuring_entity=pe,
	)
	return {"name": an, "workflow_state": doc.workflow_state}


def return_acceptance_for_revision(
	acceptance_record_id: str,
	*,
	comments: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	an = _norm(acceptance_record_id)
	doc = frappe.get_doc(AR, an)
	if _norm(doc.workflow_state) not in PENDING_ROUTE_STATES:
		frappe.throw(_("Return is only allowed during approval."), frappe.ValidationError, title=_("Invalid state"))

	route_id = get_active_route_instance(AR, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_acceptance_matches_route(doc, inst)

	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	pe = _procuring_entity(doc)
	res = run_controlled_action_gate(
		doctype=AR,
		docname=doc.name,
		action=ACTION_RETURN,
		user=u,
		procuring_entity=pe,
	)
	_assert_gate_ok(res, ACTION_RETURN)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_DRAFT
		doc.status = ST_DRAFT
		doc.save()

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Return",
		user=u,
		comments=comments,
		reference_doctype=AR,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_RETURN,
		hook_action=ACTION_RETURN,
	)

	irn = _norm(doc.inspection_record)
	if irn and frappe.db.exists(IR, irn):
		ir = frappe.get_doc(IR, irn)
		ir.acceptance_status = "Pending"
		ir.save(ignore_permissions=True)

	log_controlled_action_completed(
		action=ACTION_RETURN,
		doctype=AR,
		docname=doc.name,
		actor=u,
		procuring_entity=pe,
	)
	return {"name": an, "workflow_state": doc.workflow_state}
