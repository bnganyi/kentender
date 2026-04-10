# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""PROC-STORY-115: apply acceptance outcomes to milestone/deliverable progress and contract completion."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

AR = "Acceptance Record"
IR = "Inspection Record"
PC = "Procurement Contract"
PCM = "Procurement Contract Milestone"
PCD = "Procurement Contract Deliverable"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _weighted_contract_completion_percent(contract_id: str) -> float:
	"""Value-weighted average of milestone ``completion_percent`` (weights default to 1)."""
	rows = frappe.get_all(
		PCM,
		filters={"procurement_contract": contract_id, "status": ["!=", "Cancelled"]},
		fields=["completion_percent", "milestone_value"],
	)
	if not rows:
		return flt(frappe.db.get_value(PC, contract_id, "completion_percent"))
	tw = 0.0
	acc = 0.0
	for r in rows:
		mv = r.milestone_value
		w = flt(mv) if mv is not None and flt(mv) > 0 else 1.0
		p = flt(r.completion_percent)
		tw += w
		acc += p * w
	if tw <= 0:
		return min(100.0, sum(flt(x.completion_percent) for x in rows) / len(rows))
	return min(100.0, acc / tw)


def _persist_contract_completion(contract_id: str, percent: float) -> None:
	pc = frappe.get_doc(PC, contract_id)
	pc.completion_percent = min(100.0, max(0.0, flt(percent)))
	pc.save(ignore_permissions=True)


def _apply_decision_to_milestone(milestone_id: str, decision: str, *, partial_milestone_percent: float | None) -> None:
	ms = frappe.get_doc(PCM, milestone_id)
	dec = _norm(decision)
	if dec == "Accepted":
		ms.status = "Achieved"
		ms.completion_percent = 100.0
		ms.actual_completion_date = getdate(nowdate())
	elif dec == "Conditional":
		ms.status = "In Progress"
		target = flt(partial_milestone_percent) if partial_milestone_percent is not None else 50.0
		target = min(100.0, max(0.0, target))
		ms.completion_percent = min(100.0, max(flt(ms.completion_percent), target))
	elif dec == "Rejected":
		ms.status = "Missed"
	elif dec == "Deferred":
		return
	else:
		return
	ms.save(ignore_permissions=True)


def _apply_decision_to_deliverable(deliverable_id: str, decision: str) -> None:
	dd = frappe.get_doc(PCD, deliverable_id)
	dec = _norm(decision)
	if dec == "Accepted":
		dd.status = "Delivered"
	elif dec == "Conditional":
		dd.status = "In Progress"
	elif dec == "Rejected":
		dd.status = "Rejected"
	elif dec == "Deferred":
		return
	else:
		return
	dd.save(ignore_permissions=True)


def apply_acceptance_progress_from_inspection(
	inspection_record_id: str,
	*,
	partial_milestone_percent: float | None = None,
) -> dict[str, Any]:
	"""Push **Acceptance Record** outcomes to linked milestone/deliverable rows and refresh contract completion.

	Requires **Acceptance Record** ``contract_progress_update_required`` and a linked **Inspection Record**
	whose scope matches the rows being updated. **Contract Wide** inspections only recalculate the
	contract aggregate (no automatic milestone row changes).

	Does not modify unrelated contract fields (PROC-STORY-115).
	"""
	irn = _norm(inspection_record_id)
	if not irn or not frappe.db.exists(IR, irn):
		frappe.throw(_("Inspection Record not found."), frappe.ValidationError)

	ir = frappe.get_doc(IR, irn)
	arn = _norm(ir.acceptance_record)
	if not arn or not frappe.db.exists(AR, arn):
		frappe.throw(_("Inspection has no Acceptance Record."), frappe.ValidationError)

	ar = frappe.get_doc(AR, arn)
	if int(ar.contract_progress_update_required or 0) != 1:
		frappe.throw(
			_("Acceptance Record is not flagged for contract progress update."),
			frappe.ValidationError,
		)
	if _norm(ar.inspection_record) != irn:
		frappe.throw(_("Acceptance Record does not match this inspection."), frappe.ValidationError)
	if _norm(ar.contract) != _norm(ir.contract):
		frappe.throw(_("Acceptance Record contract does not match the inspection."), frappe.ValidationError)

	decision = _norm(ar.acceptance_decision)
	if decision == "Pending":
		frappe.throw(_("Cannot apply progress while acceptance decision is Pending."), frappe.ValidationError)

	updated_ms: list[str] = []
	updated_dd: list[str] = []
	st = _norm(ir.inspection_scope_type)

	if decision != "Deferred":
		if st == "Milestone" and ir.contract_milestone:
			_apply_decision_to_milestone(
				_norm(ir.contract_milestone),
				decision,
				partial_milestone_percent=partial_milestone_percent,
			)
			updated_ms.append(_norm(ir.contract_milestone))
		elif st == "Deliverable" and ir.contract_deliverable:
			_apply_decision_to_deliverable(_norm(ir.contract_deliverable), decision)
			updated_dd.append(_norm(ir.contract_deliverable))
		elif st == "Milestone and Deliverable":
			if ir.contract_milestone:
				_apply_decision_to_milestone(
					_norm(ir.contract_milestone),
					decision,
					partial_milestone_percent=partial_milestone_percent,
				)
				updated_ms.append(_norm(ir.contract_milestone))
			if ir.contract_deliverable:
				_apply_decision_to_deliverable(_norm(ir.contract_deliverable), decision)
				updated_dd.append(_norm(ir.contract_deliverable))

	cid = _norm(ir.contract)
	new_pct = _weighted_contract_completion_percent(cid)
	_persist_contract_completion(cid, new_pct)

	ar.contract_progress_update_required = 0
	ar.save(ignore_permissions=True)

	return {
		"contract": cid,
		"completion_percent": new_pct,
		"updated_milestones": updated_ms,
		"updated_deliverables": updated_dd,
		"acceptance_record": ar.name,
	}
