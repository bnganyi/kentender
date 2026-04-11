# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""PROC-STORY-113: submit acceptance decisions against completed inspections."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender.workflow_engine.safeguards import workflow_mutation_context

AR = "Acceptance Record"
IR = "Inspection Record"
IPL = "Inspection Parameter Line"
ISE = "Inspection Status Event"

_VALID_DECISIONS = frozenset({"Accepted", "Rejected", "Conditional", "Deferred"})


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _mandatory_acceptance_blockers(inspection_record: str) -> list[str]:
	"""Return human-readable reasons for mandatory items that block **full** acceptance."""
	reasons: list[str] = []
	for row in frappe.get_all(
		IPL,
		filters={"inspection_record": inspection_record},
		fields=["name", "parameter_code", "mandatory_for_acceptance", "status"],
	):
		if not int(row.mandatory_for_acceptance or 0):
			continue
		st = _norm(row.status)
		if st not in ("Passed", "Waived"):
			code = _norm(row.parameter_code) or row.name
			reasons.append(_("Mandatory parameter {0} is not satisfied (status {1}).").format(code, st or "—"))
	return reasons


def _map_ir_acceptance_status(acceptance_decision: str) -> str:
	ad = _norm(acceptance_decision)
	if ad == "Accepted":
		return "Accepted"
	if ad == "Rejected":
		return "Rejected"
	if ad == "Conditional":
		return "Conditional"
	if ad == "Deferred":
		return "Pending"
	return "Pending"


def _default_payment_eligibility_signal(acceptance_decision: str) -> str:
	ad = _norm(acceptance_decision)
	if ad == "Accepted":
		return "Eligible"
	if ad == "Rejected":
		return "Not Eligible"
	if ad == "Conditional":
		return "Conditional"
	return "Unknown"


def _default_next_action_type(acceptance_decision: str) -> str:
	ad = _norm(acceptance_decision)
	if ad == "Accepted":
		return "Close Out"
	if ad == "Rejected":
		return "Reinspect"
	if ad == "Conditional":
		return "Variation"
	if ad == "Deferred":
		return "None"
	return "None"


def _append_acceptance_event(
	inspection_record: str,
	acceptance_record: str,
	acceptance_decision: str,
	*,
	summary_notes: str | None = None,
	actor_user: str | None = None,
) -> None:
	parts = [
		_("Acceptance decision: {0}").format(_norm(acceptance_decision)),
	]
	if summary_notes:
		parts.append(_norm(summary_notes))
	summary = " ".join(parts)
	frappe.get_doc(
		{
			"doctype": ISE,
			"inspection_record": inspection_record,
			"event_type": "AcceptanceRecorded",
			"event_datetime": now_datetime(),
			"actor_user": actor_user or frappe.session.user,
			"summary": summary,
			"related_acceptance_record": acceptance_record,
		}
	).insert(ignore_permissions=True)


def submit_acceptance_decision(inspection_record_id: str, decision_data: dict[str, Any]) -> dict[str, Any]:
	"""Create an **Acceptance Record**, link it on the inspection, and emit an audit event.

	Does **not** update payment ledgers (PROC-STORY-113).

	:param decision_data: At minimum ``business_id`` and ``acceptance_decision`` (``Accepted`` /
		``Rejected`` / ``Conditional`` / ``Deferred``). Optional: ``decision_reason``,
		``approved_by_user``, ``decision_datetime``, ``accepted_value_amount``,
		``accepted_quantity_summary``, ``accepted_scope_notes``, ``technical_acceptance_basis``,
		``standards_compliance_status``, ``payment_eligibility_signal_status``,
		``contract_progress_update_required``, ``next_action_type``, ``remarks``,
		``status``, ``workflow_state``, ``event_summary`` (extra text for the status event).

		Unless overridden, ``contract_progress_update_required`` defaults on for **Accepted**,
		**Conditional**, and **Rejected** (PROC-STORY-115); **Deferred** defaults off unless set.
	"""
	irn = _norm(inspection_record_id)
	if not irn or not frappe.db.exists(IR, irn):
		frappe.throw(_("Inspection Record not found."), frappe.ValidationError)

	data = decision_data or {}
	ad = _norm(data.get("acceptance_decision"))
	if ad not in _VALID_DECISIONS:
		frappe.throw(
			_("acceptance_decision must be one of: {0}.").format(", ".join(sorted(_VALID_DECISIONS))),
			frappe.ValidationError,
		)

	bid = _norm(data.get("business_id"))
	if not bid:
		frappe.throw(_("business_id is required."), frappe.ValidationError)
	if frappe.db.exists(AR, {"business_id": bid}):
		frappe.throw(_("Acceptance Record business_id already exists."), frappe.ValidationError)

	ir = frappe.get_doc(IR, irn)
	if int(ir.is_locked or 0):
		frappe.throw(_("Inspection is locked."), frappe.ValidationError)
	if _norm(ir.status) != "Completed":
		frappe.throw(_("Inspection must be completed before acceptance."), frappe.ValidationError)

	use_engine_workflow = bool(data.get("use_engine_workflow", False))

	existing_ar = _norm(ir.acceptance_record)
	if existing_ar and frappe.db.exists(AR, existing_ar):
		st = _norm(frappe.db.get_value(AR, existing_ar, "status"))
		if st not in ("Cancelled", "Superseded"):
			frappe.throw(_("This inspection already has an active acceptance record."), frappe.ValidationError)

	if ad == "Accepted":
		if _norm(ir.inspection_result) != "Pass":
			frappe.throw(
				_("Full acceptance requires inspection result Pass."),
				frappe.ValidationError,
			)
		blockers = _mandatory_acceptance_blockers(irn)
		if blockers:
			frappe.throw(
				_("Cannot accept while mandatory items remain unresolved:\n{0}").format("\n".join(blockers)),
				frappe.ValidationError,
			)

	ar = frappe.new_doc(AR)
	ar.business_id = bid
	ar.inspection_record = irn
	ar.contract = ir.contract
	ar.acceptance_decision = ad
	if use_engine_workflow:
		ar.status = _norm(data.get("status")) or "Draft"
		ar.workflow_state = _norm(data.get("workflow_state")) or "Draft"
	else:
		ar.status = _norm(data.get("status")) or "Submitted"
		ar.workflow_state = _norm(data.get("workflow_state")) or "Pending Approval"
	ar.standards_compliance_status = _norm(data.get("standards_compliance_status")) or "Not Assessed"
	ar.payment_eligibility_signal_status = (
		_norm(data.get("payment_eligibility_signal_status")) or _default_payment_eligibility_signal(ad)
	)
	ar.next_action_type = _norm(data.get("next_action_type")) or _default_next_action_type(ad)
	if "contract_progress_update_required" in data:
		ar.contract_progress_update_required = 1 if data.get("contract_progress_update_required") else 0
	elif ad in ("Accepted", "Conditional", "Rejected"):
		ar.contract_progress_update_required = 1

	if data.get("decision_reason") is not None:
		ar.decision_reason = data.get("decision_reason")
	if data.get("approved_by_user"):
		ar.approved_by_user = _norm(data.get("approved_by_user"))
	if data.get("decision_datetime"):
		ar.decision_datetime = data.get("decision_datetime")
	else:
		ar.decision_datetime = now_datetime()

	for fn in (
		"accepted_value_amount",
		"accepted_quantity_summary",
		"accepted_scope_notes",
		"technical_acceptance_basis",
		"remarks",
	):
		if data.get(fn) is not None:
			setattr(ar, fn, data.get(fn))

	with workflow_mutation_context():
		ar.insert(ignore_permissions=True)

	ir.reload()
	ir.acceptance_record = ar.name
	if use_engine_workflow:
		ir.acceptance_status = "Pending"
	else:
		ir.acceptance_status = _map_ir_acceptance_status(ad)
	ir.save(ignore_permissions=True)

	if not use_engine_workflow:
		_append_acceptance_event(
			irn,
			ar.name,
			ad,
			summary_notes=_norm(data.get("event_summary")),
			actor_user=_norm(data.get("approved_by_user")) or None,
		)

	return {
		"name": ar.name,
		"business_id": ar.business_id,
		"acceptance_decision": ar.acceptance_decision,
		"inspection_acceptance_status": ir.acceptance_status,
	}


def sync_inspection_acceptance_status_from_record(acceptance_record_id: str) -> None:
	"""After workflow final approval, align **Inspection Record** ``acceptance_status`` with the decision."""
	an = _norm(acceptance_record_id)
	if not an or not frappe.db.exists(AR, an):
		frappe.throw(_("Acceptance Record not found."), frappe.ValidationError)
	ar = frappe.get_doc(AR, an)
	irn = _norm(ar.inspection_record)
	if not irn:
		return
	ir = frappe.get_doc(IR, irn)
	ir.acceptance_status = _map_ir_acceptance_status(ar.acceptance_decision)
	ir.save(ignore_permissions=True)

