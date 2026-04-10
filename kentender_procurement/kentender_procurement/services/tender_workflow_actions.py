# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender lifecycle actions: submit, approve, publish, cancel, withdraw (PROC-STORY-033).

Linear workflow (v1): **Draft → Submitted → Approved → Published**. ``Under Review`` is not used by
these services; approvers move **Submitted → Approved** in one step.

All mutations run inside :func:`kentender.workflow_engine.safeguards.workflow_mutation_context`.
Publication must use :func:`publish_tender` so :class:`~frappe.model.document.Document` validation
can allow the **Published** stage (see ``frappe.flags.in_tender_publish_service``).
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
	ACTION_CLOSE,
	ACTION_PUBLISH,
	ACTION_SUBMIT,
	log_controlled_action_completed,
	run_controlled_action_gate,
)
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_procurement.services.tender_publication_readiness import (
	assess_tender_publication_readiness,
)

TENDER_DOCTYPE = "Tender"
TAR_DOCTYPE = "Tender Approval Record"

SOURCE_MODULE = "kentender_procurement"

AUDIT_SUBMITTED = "kt.procurement.tender.submitted"
AUDIT_APPROVED = "kt.procurement.tender.approved"
AUDIT_PUBLISHED = "kt.procurement.tender.published"
AUDIT_CANCELLED = "kt.procurement.tender.cancelled"
AUDIT_WITHDRAWN = "kt.procurement.tender.withdrawn"

WS_DRAFT = "Draft"
WS_SUBMITTED = "Submitted"
WS_UNDER_REVIEW = "Under Review"
WS_APPROVED = "Approved"
WS_PUBLISHED = "Published"
WS_CANCELLED = "Cancelled"
WS_RETURNED = "Returned"

ST_DRAFT = "Draft"
ST_PENDING = "Pending"
ST_ACTIVE = "Active"
ST_CANCELLED = "Cancelled"

AS_DRAFT = "Draft"
AS_SUBMITTED = "Submitted"
AS_APPROVED = "Approved"
AS_PUBLISHED = "Published"
# ``approval_status`` options have no Cancelled; use Rejected for terminal procurement cancellation.
AS_TERMINAL = "Rejected"

SUB_NOT_OPEN = "Not Open"
SUB_OPEN = "Open"
SUB_CLOSED = "Closed"
SUB_CANCELLED = "Cancelled"

PD_NOT = "Not Published"
PD_SYNOPSIS = "Synopsis Only"
PD_FULL = "Full Tender"


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


def _assert_gate_ok(result: Any, action: str) -> None:
	if result.ok:
		return
	frappe.throw(
		_(result.failure_reason or "Action not allowed."),
		frappe.ValidationError,
		title=_("{0} blocked").format(_(action)),
	)


def _audit_payload(doc: Document, **extra: Any) -> str:
	return json.dumps(
		{
			"name": doc.name,
			"workflow_state": _norm(doc.get("workflow_state")),
			"status": _norm(doc.get("status")),
			"approval_status": _norm(doc.get("approval_status")),
			"submission_status": _norm(doc.get("submission_status")),
			**extra,
		},
		sort_keys=True,
		ensure_ascii=False,
	)


def _emit_tender_audit(
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
		target_doctype=TENDER_DOCTYPE,
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
		"submission_status": _norm(doc.get("submission_status")),
	}


def _insert_tender_approval_record(
	*,
	tender_name: str,
	workflow_step: str,
	decision_level: str,
	approver_user: str,
	action_type: str,
	comments: str | None = None,
	exception_record: str | None = None,
) -> Document:
	role = _primary_role_for_user(approver_user)
	return frappe.get_doc(
		{
			"doctype": TAR_DOCTYPE,
			"tender": tender_name,
			"workflow_step": _norm(workflow_step),
			"decision_level": _norm(decision_level),
			"approver_user": approver_user,
			"approver_role": role,
			"action_type": action_type,
			"action_datetime": now_datetime(),
			"comments": _norm(comments) or None,
			"exception_record": _norm(exception_record) or None,
		}
	).insert(ignore_permissions=True)


def submit_tender_for_review(
	tender_name: str,
	*,
	user: str | None = None,
	comments: str | None = None,
) -> Document:
	"""Draft → Submitted."""
	tn = _norm(tender_name)
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(TENDER_DOCTYPE, tn)
	ws = _norm(doc.workflow_state)
	if ws != WS_DRAFT:
		frappe.throw(
			_("Only tenders in **Draft** can be submitted (current stage: {0}).").format(ws or "—"),
			frappe.ValidationError,
			title=_("Invalid stage"),
		)
	res = run_controlled_action_gate(
		doctype=TENDER_DOCTYPE,
		docname=tn,
		action=ACTION_SUBMIT,
		user=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
	)
	_assert_gate_ok(res, ACTION_SUBMIT)
	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_SUBMITTED
		doc.status = ST_PENDING
		doc.approval_status = AS_SUBMITTED
		doc.save(ignore_permissions=True)
	new = _state_snapshot(doc)
	_emit_tender_audit(
		event_type=AUDIT_SUBMITTED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
	)
	_insert_tender_approval_record(
		tender_name=tn,
		workflow_step="Submission",
		decision_level="Procuring Entity",
		approver_user=u,
		action_type="Recommend",
		comments=comments or _("Submitted for review."),
	)
	log_controlled_action_completed(
		action=ACTION_SUBMIT,
		doctype=TENDER_DOCTYPE,
		docname=tn,
		actor=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
	)
	doc.reload()
	return doc


def approve_tender(
	tender_name: str,
	*,
	user: str | None = None,
	comments: str | None = None,
	exception_record: str | None = None,
) -> Document:
	"""Submitted or Under Review → Approved."""
	tn = _norm(tender_name)
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(TENDER_DOCTYPE, tn)
	ws = _norm(doc.workflow_state)
	if ws not in (WS_SUBMITTED, WS_UNDER_REVIEW):
		frappe.throw(
			_("Only tenders **Submitted** or **Under Review** can be approved (current: {0}).").format(
				ws or "—",
			),
			frappe.ValidationError,
			title=_("Invalid stage"),
		)
	res = run_controlled_action_gate(
		doctype=TENDER_DOCTYPE,
		docname=tn,
		action=ACTION_APPROVE,
		user=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
	)
	_assert_gate_ok(res, ACTION_APPROVE)
	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_APPROVED
		doc.status = ST_PENDING
		doc.approval_status = AS_APPROVED
		doc.save(ignore_permissions=True)
	new = _state_snapshot(doc)
	_emit_tender_audit(
		event_type=AUDIT_APPROVED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
	)
	_insert_tender_approval_record(
		tender_name=tn,
		workflow_step="Approval",
		decision_level="Procuring Entity",
		approver_user=u,
		action_type="Approve",
		comments=comments,
		exception_record=exception_record,
	)
	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=TENDER_DOCTYPE,
		docname=tn,
		actor=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
	)
	doc.reload()
	return doc


def publish_tender(
	tender_name: str,
	*,
	user: str | None = None,
	comments: str | None = None,
) -> Document:
	"""Approved → Published (readiness checks, controlled publish flag)."""
	tn = _norm(tender_name)
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(TENDER_DOCTYPE, tn)
	ws = _norm(doc.workflow_state)
	if ws != WS_APPROVED:
		frappe.throw(
			_("Only **Approved** tenders can be published (current: {0}).").format(ws or "—"),
			frappe.ValidationError,
			title=_("Invalid stage"),
		)
	ready = assess_tender_publication_readiness(tn)
	if not ready.get("ok"):
		r = "; ".join(ready.get("reasons") or []) or _("Tender is not ready to publish.")
		frappe.throw(r, frappe.ValidationError, title=_("Not ready to publish"))

	res = run_controlled_action_gate(
		doctype=TENDER_DOCTYPE,
		docname=tn,
		action=ACTION_PUBLISH,
		user=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
	)
	_assert_gate_ok(res, ACTION_PUBLISH)
	old = _state_snapshot(doc)
	frappe.flags.in_tender_publish_service = True
	try:
		with workflow_mutation_context():
			if not doc.publication_datetime:
				doc.publication_datetime = now_datetime()
			doc.workflow_state = WS_PUBLISHED
			doc.status = ST_ACTIVE
			doc.approval_status = AS_PUBLISHED
			doc.submission_status = SUB_OPEN
			doc.public_disclosure_stage = PD_FULL
			doc.save(ignore_permissions=True)
	finally:
		frappe.flags.in_tender_publish_service = False

	new = _state_snapshot(doc)
	_emit_tender_audit(
		event_type=AUDIT_PUBLISHED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
	)
	_insert_tender_approval_record(
		tender_name=tn,
		workflow_step="Publication",
		decision_level="Procuring Entity",
		approver_user=u,
		action_type="Approve",
		comments=comments or _("Published."),
	)
	log_controlled_action_completed(
		action=ACTION_PUBLISH,
		doctype=TENDER_DOCTYPE,
		docname=tn,
		actor=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
	)
	doc.reload()
	return doc


def cancel_tender(
	tender_name: str,
	*,
	reason: str,
	user: str | None = None,
	comments: str | None = None,
) -> Document:
	"""Cancel a tender before or after publication (except already terminal)."""
	tn = _norm(tender_name)
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(TENDER_DOCTYPE, tn)
	ws = _norm(doc.workflow_state)
	if ws in (WS_CANCELLED,):
		frappe.throw(_("Tender is already cancelled."), frappe.ValidationError, title=_("Invalid stage"))
	res = run_controlled_action_gate(
		doctype=TENDER_DOCTYPE,
		docname=tn,
		action=ACTION_CLOSE,
		user=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
	)
	_assert_gate_ok(res, "cancel")
	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_CANCELLED
		doc.status = ST_CANCELLED
		doc.approval_status = AS_TERMINAL
		doc.submission_status = SUB_CANCELLED
		doc.cancellation_reason = _norm(reason)
		doc.save(ignore_permissions=True)
	new = _state_snapshot(doc)
	_emit_tender_audit(
		event_type=AUDIT_CANCELLED,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_norm(reason),
	)
	_insert_tender_approval_record(
		tender_name=tn,
		workflow_step="Cancellation",
		decision_level="Procuring Entity",
		approver_user=u,
		action_type="Reject",
		comments=comments or reason,
	)
	log_controlled_action_completed(
		action=ACTION_CLOSE,
		doctype=TENDER_DOCTYPE,
		docname=tn,
		actor=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
		extra={"variant": "cancel"},
	)
	doc.reload()
	return doc


def withdraw_tender(
	tender_name: str,
	*,
	reason: str,
	user: str | None = None,
	comments: str | None = None,
) -> Document:
	"""Withdraw a **Published** tender from the market (terminal cancel + withdrawal reason)."""
	tn = _norm(tender_name)
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(TENDER_DOCTYPE, tn)
	ws = _norm(doc.workflow_state)
	if ws != WS_PUBLISHED:
		frappe.throw(
			_("Withdraw applies only to **Published** tenders (current: {0}). Use cancel otherwise.").format(
				ws or "—",
			),
			frappe.ValidationError,
			title=_("Invalid stage"),
		)
	res = run_controlled_action_gate(
		doctype=TENDER_DOCTYPE,
		docname=tn,
		action=ACTION_CLOSE,
		user=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
		context={"withdraw": True},
	)
	_assert_gate_ok(res, "withdraw")
	old = _state_snapshot(doc)
	with workflow_mutation_context():
		doc.workflow_state = WS_CANCELLED
		doc.status = ST_CANCELLED
		doc.approval_status = AS_TERMINAL
		doc.submission_status = SUB_CLOSED
		doc.withdrawal_reason = _norm(reason)
		doc.save(ignore_permissions=True)
	new = _state_snapshot(doc)
	_emit_tender_audit(
		event_type=AUDIT_WITHDRAWN,
		doc=doc,
		actor=u,
		old_snapshot=old,
		new_snapshot=new,
		reason=_norm(reason),
	)
	_insert_tender_approval_record(
		tender_name=tn,
		workflow_step="Withdrawal",
		decision_level="Procuring Entity",
		approver_user=u,
		action_type="Return for Revision",
		comments=comments or reason,
	)
	log_controlled_action_completed(
		action=ACTION_CLOSE,
		doctype=TENDER_DOCTYPE,
		docname=tn,
		actor=u,
		procuring_entity=_norm(doc.procuring_entity) or None,
		extra={"variant": "withdraw"},
	)
	doc.reload()
	return doc
