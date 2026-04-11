# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Contract approval and signing workflow (PROC-STORY-095).

WF-013: approval transitions use :mod:`kentender.workflow_engine` (routes, ``apply_step_decision``).
Signing and send-for-signature remain domain actions after approval is complete.
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
from kentender.workflow_engine.actions import emit_post_transition, log_global_approval_action
from kentender.workflow_engine.execution import apply_step_decision, get_current_step_row
from kentender.workflow_engine.routes import get_active_route_instance, get_or_create_active_route
from kentender.workflow_engine.safeguards import workflow_mutation_context

PC = "Procurement Contract"
PCAR = "Procurement Contract Approval Record"
PCSR = "Procurement Contract Signing Record"
PCSE = "Procurement Contract Status Event"

SOURCE_MODULE = "kentender_procurement.contract_approval_signature_services"

WS_DRAFT = "Draft"
WS_IN_REVIEW = "In Review"
WS_PENDING_APPROVAL = "Pending Approval"
WS_PENDING_SIGNATURE = "Pending Signature"

ACTION_REJECT = "reject"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _actor_role() -> str:
	return (frappe.get_roles(_norm(frappe.session.user)) or ["Guest"])[0]


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
	return _norm(doc.get("procuring_entity")) or None


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
			_("Procurement Contract approval routes must have 1 or 2 steps."),
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


def _assert_contract_matches_route(doc: Document, inst: Document) -> None:
	_assert_route_template_supported(inst)
	max_o = _max_step_order(inst)
	cur = int(inst.current_step_no or 0)
	got = _norm(doc.workflow_state)
	if max_o == 1:
		if got != WS_IN_REVIEW:
			frappe.throw(
				_("Contract stage {0!r} does not match the active route (expected {1!r}).").format(
					got, WS_IN_REVIEW
				),
				frappe.ValidationError,
				title=_("Stage mismatch"),
			)
		return
	if cur == 1 and got != WS_IN_REVIEW:
		frappe.throw(
			_("Contract stage {0!r} does not match route step 1 (expected {1!r}).").format(
				got, WS_IN_REVIEW
			),
			frappe.ValidationError,
			title=_("Stage mismatch"),
		)
	if cur >= 2 and got != WS_PENDING_APPROVAL:
		frappe.throw(
			_("Contract stage {0!r} does not match route step 2 (expected {1!r}).").format(
				got, WS_PENDING_APPROVAL
			),
			frappe.ValidationError,
			title=_("Stage mismatch"),
		)


def _append_status_event(
	contract_name: str,
	event_type: str,
	summary: str,
	*,
	related_variation: str | None = None,
) -> None:
	frappe.get_doc(
		{
			"doctype": PCSE,
			"procurement_contract": contract_name,
			"event_type": event_type,
			"event_datetime": now_datetime(),
			"actor_user": _norm(frappe.session.user) or "Administrator",
			"summary": summary,
			"related_variation": related_variation,
		}
	).insert(ignore_permissions=True)


def submit_contract_for_review(
	contract_id: str,
	*,
	comments: str | None = None,
) -> dict[str, Any]:
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	if _norm(doc.status) != "Draft":
		frappe.throw(_("Only draft contracts can be submitted."), frappe.ValidationError)

	u = _norm(frappe.session.user) or "Administrator"
	res = run_controlled_action_gate(
		doctype=PC,
		docname=doc.name,
		action=ACTION_SUBMIT,
		user=u,
		procuring_entity=_procuring_entity(doc),
	)
	_assert_gate_ok(res, ACTION_SUBMIT)

	route_id = get_or_create_active_route(PC, doc.name)
	if not route_id:
		frappe.throw(
			_("No active KenTender Workflow Policy matches this contract; cannot resolve an approval route."),
			frappe.ValidationError,
			title=_("No approval route"),
		)
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_IN_REVIEW
		doc.approval_status = "Pending"
		doc.save()

	new = _state_snapshot(doc)
	log_global_approval_action(
		reference_doctype=PC,
		reference_docname=doc.name,
		action=ACTION_SUBMIT,
		actor_user=u,
		actor_role=_primary_role_for_user(u),
		previous_state=old,
		new_state=new,
		comments=_norm(comments) or _("Contract submitted for review."),
		route_instance=route_id,
		is_final_action=False,
	)
	emit_post_transition(
		doctype=PC,
		docname=doc.name,
		action=ACTION_SUBMIT,
		actor=u,
		context={"route_instance": route_id},
	)

	frappe.get_doc(
		{
			"doctype": PCAR,
			"procurement_contract": cn,
			"workflow_step": "Submit",
			"approver_user": u,
			"approver_role": _actor_role(),
			"action_type": "Submit",
			"action_datetime": now_datetime(),
			"comments": _norm(comments),
			"decision_level": "Initiation",
		}
	).insert(ignore_permissions=True)

	_append_status_event(cn, "Submitted", _("Contract submitted for review."))
	log_audit_event(
		event_type="procurement_contract.submitted",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"workflow_state": doc.workflow_state}),
	)
	log_controlled_action_completed(
		action=ACTION_SUBMIT,
		doctype=PC,
		docname=doc.name,
		actor=u,
		procuring_entity=_procuring_entity(doc),
	)
	return {"name": cn, "workflow_state": doc.workflow_state}


def approve_contract_review_step(
	contract_id: str,
	*,
	workflow_step: str | None = None,
	decision_level: str | None = None,
	comments: str | None = None,
) -> dict[str, Any]:
	"""Advance a non-final approval step (two-step templates only)."""
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	if _norm(doc.approval_status) == "Approved":
		frappe.throw(_("Contract is already approved."), frappe.ValidationError)

	route_id = get_active_route_instance(PC, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route for this contract."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)
	if _is_final_approval_step(inst):
		frappe.throw(
			_("Use approve_contract for the final route step."),
			frappe.ValidationError,
			title=_("Invalid action"),
		)
	_assert_contract_matches_route(doc, inst)

	u = _norm(frappe.session.user) or "Administrator"
	res = run_controlled_action_gate(
		doctype=PC,
		docname=doc.name,
		action=ACTION_APPROVE,
		user=u,
		procuring_entity=_procuring_entity(doc),
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

	frappe.get_doc(
		{
			"doctype": PCAR,
			"procurement_contract": cn,
			"workflow_step": step_label,
			"approver_user": u,
			"approver_role": _actor_role(),
			# PCAR select options omit "Recommend" (unlike Award Approval Record); non-final step is still an approval.
			"action_type": "Approve",
			"action_datetime": now_datetime(),
			"comments": _norm(comments),
			"decision_level": level_label,
		}
	).insert(ignore_permissions=True)

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Approve",
		user=u,
		comments=comments,
		reference_doctype=PC,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_APPROVE,
		hook_action=ACTION_APPROVE,
	)

	_append_status_event(cn, "Other", _("Contract review step completed."))
	log_audit_event(
		event_type="procurement_contract.review_step",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"workflow_state": doc.workflow_state}),
	)
	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=PC,
		docname=doc.name,
		actor=u,
		procuring_entity=_procuring_entity(doc),
	)
	return {"name": cn, "workflow_state": doc.workflow_state}


def approve_contract(
	contract_id: str,
	*,
	comments: str | None = None,
) -> dict[str, Any]:
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	if _norm(doc.approval_status) == "Approved":
		frappe.throw(_("Contract is already approved."), frappe.ValidationError)

	route_id = get_active_route_instance(PC, doc.name)
	if not route_id:
		frappe.throw(_("No active approval route for this contract."), frappe.ValidationError, title=_("Missing route"))
	inst = frappe.get_doc("KenTender Approval Route Instance", route_id)
	_assert_route_template_supported(inst)
	if not _is_final_approval_step(inst):
		frappe.throw(
			_("Complete earlier approval steps before final approval."),
			frappe.ValidationError,
			title=_("Not final step"),
		)
	_assert_contract_matches_route(doc, inst)

	u = _norm(frappe.session.user) or "Administrator"
	res = run_controlled_action_gate(
		doctype=PC,
		docname=doc.name,
		action=ACTION_APPROVE,
		user=u,
		procuring_entity=_procuring_entity(doc),
	)
	_assert_gate_ok(res, ACTION_APPROVE)

	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.approval_status = "Approved"
		doc.workflow_state = WS_PENDING_SIGNATURE
		doc.save()

	frappe.get_doc(
		{
			"doctype": PCAR,
			"procurement_contract": cn,
			"workflow_step": "Approve",
			"approver_user": u,
			"approver_role": _actor_role(),
			"action_type": "Approve",
			"action_datetime": now_datetime(),
			"comments": _norm(comments),
			"decision_level": "Final",
		}
	).insert(ignore_permissions=True)

	doc.reload()
	new = _state_snapshot(doc)

	apply_step_decision(
		route_id,
		"Approve",
		user=u,
		comments=comments,
		reference_doctype=PC,
		reference_docname=doc.name,
		previous_state=old,
		new_state=new,
		log_action=ACTION_APPROVE,
		hook_action=ACTION_APPROVE,
	)

	_append_status_event(cn, "Approved", _("Contract approved; awaiting signature."))
	log_audit_event(
		event_type="procurement_contract.approved",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"approval_status": "Approved"}),
	)
	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=PC,
		docname=doc.name,
		actor=u,
		procuring_entity=_procuring_entity(doc),
	)
	return {"name": cn, "approval_status": doc.approval_status}


def send_contract_for_signature(contract_id: str) -> dict[str, Any]:
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	if _norm(doc.approval_status) != "Approved":
		frappe.throw(_("Contract must be approved before signature."), frappe.ValidationError)
	doc.status = "Pending Signature"
	doc.save(ignore_permissions=True)

	_append_status_event(cn, "Signature", _("Contract sent for signature."))
	log_audit_event(
		event_type="procurement_contract.pending_signature",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
	)
	return {"name": cn, "status": doc.status}


def record_contract_signature(
	contract_id: str,
	*,
	signing_method: str = "Digital",
	signature_reference: str | None = None,
	signed_document: str | None = None,
	hash_value: str | None = None,
	signed_by_supplier_name: str | None = None,
) -> dict[str, Any]:
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	if _norm(doc.approval_status) != "Approved":
		frappe.throw(_("Contract must be approved before recording signature."), frappe.ValidationError)

	hv = _norm(hash_value)
	if not hv and not _norm(signed_document):
		frappe.throw(_("Provide signed document attachment or hash value."), frappe.ValidationError)

	rec = frappe.get_doc(
		{
			"doctype": PCSR,
			"procurement_contract": cn,
			"signing_method": _norm(signing_method) or "Digital",
			"signed_by_entity_user": _norm(frappe.session.user) or "Administrator",
			"signed_by_supplier_name": _norm(signed_by_supplier_name),
			"signed_on": now_datetime(),
			"status": "Completed",
			"signature_reference": _norm(signature_reference),
			"signed_document": signed_document,
			"hash_value": hv or None,
		}
	)
	rec.insert(ignore_permissions=True)

	doc.signed_document_hash = hv or doc.signed_document_hash
	doc.actual_signed_date = now_datetime()
	doc.save(ignore_permissions=True)

	_append_status_event(cn, "Signature", _("Signature recorded."))
	log_audit_event(
		event_type="procurement_contract.signature_recorded",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"signing_record": rec.name}),
	)
	return {"name": cn, "signing_record": rec.name}
