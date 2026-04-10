# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""GOV-STORY-022: apply / release procurement holds recorded on **Complaint** + optional `kentender` bridge."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_governance.services.complaint_service_utils import (
	append_complaint_event,
	ensure_complaint_not_locked,
	get_complaint_doc,
	norm,
	save_complaint,
)


def _emit_hold_bridge(complaint: str, action: str, context: dict[str, Any]) -> None:
	from kentender.api.complaint_integration import emit_complaint_hold_signal

	emit_complaint_hold_signal(complaint=complaint, action=action, context=context)


def _ensure_holdable(doc: Document) -> None:
	st = norm(doc.status)
	if st in ("Closed", "Withdrawn"):
		frappe.throw(_("Cannot change procurement hold in status {0}.").format(st), frappe.ValidationError)
	if st not in ("Under Review", "Decided"):
		frappe.throw(
			_("Procurement hold applies while the complaint is **Under Review** or **Decided** (current: {0}).").format(
				st
			),
			frappe.ValidationError,
		)


@frappe.whitelist()
def apply_procurement_hold(
	complaint: str,
	affects_award_process: int | None = None,
	affects_contract_execution: int | None = None,
	hold_scope: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Activate a complaint-driven hold (award and/or contract progression flags on **Complaint**).

	Calls `kentender.api.complaint_integration.emit_complaint_hold_signal` for downstream readiness hooks.
	Emits **Complaint Status Event** ``Other``.
	"""
	doc = get_complaint_doc(complaint)
	ensure_complaint_not_locked(doc)
	_ensure_holdable(doc)

	doc.hold_required = 1
	doc.hold_status = "Active"
	if affects_award_process is not None:
		doc.affects_award_process = int(affects_award_process)
	if affects_contract_execution is not None:
		doc.affects_contract_execution = int(affects_contract_execution)
	if hold_scope is not None:
		doc.hold_scope = norm(hold_scope) or None

	save_complaint(doc)
	ctx = {
		"affects_award_process": int(doc.affects_award_process or 0),
		"affects_contract_execution": int(doc.affects_contract_execution or 0),
		"hold_scope": doc.hold_scope,
	}
	_emit_hold_bridge(doc.name, "apply", ctx)
	summary = _("Procurement hold applied (award={0}, contract={1}).").format(
		int(doc.affects_award_process or 0),
		int(doc.affects_contract_execution or 0),
	)
	append_complaint_event(doc.name, "Other", summary, actor_user=actor_user)
	return doc


@frappe.whitelist()
def release_procurement_hold(complaint: str, actor_user: str | None = None) -> Document:
	"""Release an active hold (**hold_status** → **Released**). Emits **Other**."""
	doc = get_complaint_doc(complaint)
	ensure_complaint_not_locked(doc)
	_ensure_holdable(doc)
	if norm(doc.hold_status) != "Active":
		frappe.throw(_("No active procurement hold to release."), frappe.ValidationError)

	doc.hold_status = "Released"
	save_complaint(doc)
	_emit_hold_bridge(
		doc.name,
		"release",
		{
			"affects_award_process": int(doc.affects_award_process or 0),
			"affects_contract_execution": int(doc.affects_contract_execution or 0),
		},
	)
	append_complaint_event(
		doc.name,
		"Other",
		_("Procurement hold released."),
		actor_user=actor_user,
	)
	return doc
