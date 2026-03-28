# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Controlled business action gate (STORY-CORE-014).

Use :func:`run_controlled_action_gate` before critical operations (submit, approve,
publish, etc.) to enforce, in order:

1. **Frappe permission** on the target document (configurable perm type per action).
2. **Workflow Guard Rule** evaluation for the matching pre-* event (CORE-013).
3. **Audit trail** via **KenTender Audit Event** (and **access denied** audit on
   permission failure when enabled).

The gate **does not** mutate the document or call ``doc.submit()`` — callers run
their business logic after ``ok`` is true. Use :func:`log_controlled_action_completed`
to record successful completion if needed.

**Actions:** use the string constants below so perm-type and workflow event mapping
stays consistent. Custom action strings fall back to perm type ``write`` and
workflow event :data:`kentender.services.workflow_guard_service.EVENT_PRE_TRANSITION`.

Call only from **server-side** code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from kentender.services.access_audit_service import log_access_denied
from kentender.services.audit_event_service import log_audit_event
from kentender.services.workflow_guard_service import (
	EVENT_PRE_APPROVE,
	EVENT_PRE_CREATE,
	EVENT_PRE_SUBMIT,
	EVENT_PRE_TRANSITION,
	RuleEvaluator,
	WorkflowGuardResult,
	evaluate_workflow_guards,
	workflow_guard_result_summary,
)

ACTION_SUBMIT = "submit"
ACTION_APPROVE = "approve"
ACTION_PUBLISH = "publish"
ACTION_OPEN = "open"
ACTION_FINALIZE = "finalize"
ACTION_CLOSE = "close"

AUDIT_GATE_PASSED = "kt.controlled_action.gate_passed"
AUDIT_GUARD_BLOCKED = "kt.controlled_action.workflow_guard_blocked"
AUDIT_PERMISSION_DENIED = "kt.controlled_action.permission_denied"
AUDIT_COMPLETED = "kt.controlled_action.completed"

SOURCE_MODULE = "kentender.controlled_action"


@dataclass
class ControlledActionResult:
	"""Outcome of :func:`run_controlled_action_gate`."""

	ok: bool
	action: str
	doctype: str
	docname: str
	user: str
	permission_ok: bool
	permission_ptype: str
	guard_result: WorkflowGuardResult | None
	failure_reason: str | None = None


def default_permtype_for_action(action: str, doctype: str | None = None) -> str:
	"""Default Frappe permission type for a logical *action* name.

	For ``submit``, returns ``submit`` only when *doctype* is submittable; otherwise
	``write`` so gates work on non-submittable business documents.
	"""
	a = (action or "").strip().lower()
	if a == ACTION_SUBMIT:
		if (doctype or "").strip():
			meta = frappe.get_meta(doctype.strip())
			if cint(getattr(meta, "is_submittable", 0)):
				return "submit"
		return "write"
	return "write"


def workflow_event_for_action(action: str) -> str:
	"""Map *action* to **Workflow Guard Rule** ``event_name``."""
	a = (action or "").strip().lower()
	mapping = {
		"create": EVENT_PRE_CREATE,
		ACTION_SUBMIT: EVENT_PRE_SUBMIT,
		ACTION_APPROVE: EVENT_PRE_APPROVE,
		ACTION_PUBLISH: EVENT_PRE_SUBMIT,
		ACTION_OPEN: EVENT_PRE_APPROVE,
		ACTION_FINALIZE: EVENT_PRE_TRANSITION,
		ACTION_CLOSE: EVENT_PRE_TRANSITION,
	}
	return mapping.get(a, EVENT_PRE_TRANSITION)


def _audit_payload(
	action: str,
	doctype: str,
	docname: str,
	**extra: Any,
) -> str:
	return json.dumps(
		{"action": action, "doctype": doctype, "docname": docname, **extra},
		sort_keys=True,
		ensure_ascii=False,
	)


def run_controlled_action_gate(
	*,
	doctype: str,
	docname: str,
	action: str,
	user: str | None = None,
	permission_ptype: str | None = None,
	context: dict[str, Any] | None = None,
	guard_evaluator: RuleEvaluator | None = None,
	run_workflow_guards: bool = True,
	audit: bool = True,
	log_permission_denial_with_access_audit: bool = True,
	procuring_entity: str | None = None,
	business_id: str | None = None,
) -> ControlledActionResult:
	"""Validate permission + workflow guards; optionally write audit rows.

	Returns :class:`ControlledActionResult` with ``ok=True`` only when permission
	checks pass and no **blocking** guard issues exist. Warning-only guard issues
	do not set ``ok`` to false.
	"""
	dt = (doctype or "").strip()
	dn = (docname or "").strip()
	act = (action or "").strip()
	u = (user or frappe.session.user or "").strip()
	ptype = (permission_ptype or "").strip() or default_permtype_for_action(act, dt)
	ctx = dict(context) if context else {}

	empty = ControlledActionResult(
		ok=False,
		action=act,
		doctype=dt,
		docname=dn,
		user=u,
		permission_ok=False,
		permission_ptype=ptype,
		guard_result=None,
		failure_reason=_("DocType and document name are required."),
	)
	if not dt or not dn or not act:
		return empty

	if not frappe.db.exists(dt, dn):
		return ControlledActionResult(
			ok=False,
			action=act,
			doctype=dt,
			docname=dn,
			user=u,
			permission_ok=False,
			permission_ptype=ptype,
			guard_result=None,
			failure_reason=_("Document does not exist."),
		)

	if not frappe.has_permission(dt, "read", doc=dn, user=u):
		reason = _("No read access to this document.")
		if log_permission_denial_with_access_audit:
			log_access_denied(
				resource_doctype=dt,
				resource_name=dn,
				action=act,
				denial_reason=str(reason),
				actor=u,
				procuring_entity=procuring_entity,
				business_id=business_id,
			)
		if audit:
			log_audit_event(
				event_type=AUDIT_PERMISSION_DENIED,
				actor=u,
				source_module=SOURCE_MODULE,
				target_doctype=dt,
				target_docname=dn,
				procuring_entity=procuring_entity,
				business_id=business_id,
				reason=str(reason),
				new_state=_audit_payload(act, dt, dn, stage="read", ptype="read"),
			)
		return ControlledActionResult(
			ok=False,
			action=act,
			doctype=dt,
			docname=dn,
			user=u,
			permission_ok=False,
			permission_ptype=ptype,
			guard_result=None,
			failure_reason=str(reason),
		)

	if not frappe.has_permission(dt, ptype, doc=dn, user=u):
		reason = _("Permission {0} denied for action {1}.").format(
			frappe.bold(ptype),
			frappe.bold(act),
		)
		if log_permission_denial_with_access_audit:
			log_access_denied(
				resource_doctype=dt,
				resource_name=dn,
				action=act,
				denial_reason=str(reason),
				actor=u,
				procuring_entity=procuring_entity,
				business_id=business_id,
			)
		if audit:
			log_audit_event(
				event_type=AUDIT_PERMISSION_DENIED,
				actor=u,
				source_module=SOURCE_MODULE,
				target_doctype=dt,
				target_docname=dn,
				procuring_entity=procuring_entity,
				business_id=business_id,
				reason=str(reason),
				new_state=_audit_payload(act, dt, dn, stage="action_perm", ptype=ptype),
			)
		return ControlledActionResult(
			ok=False,
			action=act,
			doctype=dt,
			docname=dn,
			user=u,
			permission_ok=False,
			permission_ptype=ptype,
			guard_result=None,
			failure_reason=str(reason),
		)

	doc = frappe.get_doc(dt, dn)
	guard_res: WorkflowGuardResult | None = None

	if run_workflow_guards:
		ev_name = workflow_event_for_action(act)
		guard_res = evaluate_workflow_guards(
			applies_to_doctype=dt,
			target_docname=dn,
			event_name=ev_name,
			document=doc,
			context=ctx,
			evaluator=guard_evaluator,
		)
		if not guard_res.passed:
			summary = workflow_guard_result_summary(guard_res)
			reason = _("Workflow guard blocked this action.")
			if audit:
				log_audit_event(
					event_type=AUDIT_GUARD_BLOCKED,
					actor=u,
					source_module=SOURCE_MODULE,
					target_doctype=dt,
					target_docname=dn,
					procuring_entity=procuring_entity,
					business_id=business_id,
					reason=str(reason),
					new_state=_audit_payload(
						act,
						dt,
						dn,
						event_name=ev_name,
						guard_summary=summary,
						blocking=[
							{
								"rule_code": i.rule_code,
								"message": i.message,
							}
							for i in guard_res.blocking_issues
						],
					),
				)
			return ControlledActionResult(
				ok=False,
				action=act,
				doctype=dt,
				docname=dn,
				user=u,
				permission_ok=True,
				permission_ptype=ptype,
				guard_result=guard_res,
				failure_reason=str(reason),
			)

	if audit:
		gr_summary = workflow_guard_result_summary(guard_res) if guard_res else {}
		log_audit_event(
			event_type=AUDIT_GATE_PASSED,
			actor=u,
			source_module=SOURCE_MODULE,
			target_doctype=dt,
			target_docname=dn,
			procuring_entity=procuring_entity,
			business_id=business_id,
			reason=_("Controlled action gate passed for {0}.").format(frappe.bold(act)),
			new_state=_audit_payload(
				act,
				dt,
				dn,
				workflow_event=workflow_event_for_action(act) if run_workflow_guards else None,
				guard_summary=gr_summary,
			),
		)

	return ControlledActionResult(
		ok=True,
		action=act,
		doctype=dt,
		docname=dn,
		user=u,
		permission_ok=True,
		permission_ptype=ptype,
		guard_result=guard_res,
		failure_reason=None,
	)


def log_controlled_action_completed(
	*,
	action: str,
	doctype: str,
	docname: str,
	actor: str | None = None,
	procuring_entity: str | None = None,
	business_id: str | None = None,
	extra: dict[str, Any] | None = None,
) -> Document:
	"""Append audit row after the business operation succeeds (optional)."""
	payload = {"phase": "completed", **(extra or {})}
	return log_audit_event(
		event_type=AUDIT_COMPLETED,
		actor=actor,
		source_module=SOURCE_MODULE,
		target_doctype=doctype,
		target_docname=docname,
		procuring_entity=procuring_entity,
		business_id=business_id,
		reason=_("Controlled action {0} completed.").format(frappe.bold(action)),
		new_state=_audit_payload(action, doctype, docname, **payload),
	)
