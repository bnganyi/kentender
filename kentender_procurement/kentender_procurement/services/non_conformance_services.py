# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""PROC-STORY-114: non-conformance lifecycle and reinspection orchestration."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime

IR = "Inspection Record"
NC = "Non Conformance Record"
RR = "Reinspection Record"
ISE = "Inspection Status Event"

_ISSUE_TYPES = frozenset({"Defect", "Non Compliance", "Documentation", "Safety", "Quality", "Other"})
_SEVERITIES = frozenset({"Minor", "Major", "Critical"})
_APPROVE_OUTCOMES = frozenset({"Resolved", "Waived"})
_RR_TRIGGERS = frozenset({"Non Conformance", "Failed Inspection", "Client Request", "Regulatory", "Other"})


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _append_inspection_event(
	inspection_record: str,
	event_type: str,
	summary: str,
	*,
	related_non_conformance_record: str | None = None,
	actor_user: str | None = None,
) -> None:
	row: dict[str, Any] = {
		"doctype": ISE,
		"inspection_record": inspection_record,
		"event_type": event_type,
		"event_datetime": now_datetime(),
		"actor_user": actor_user or frappe.session.user,
		"summary": summary,
	}
	if related_non_conformance_record:
		row["related_non_conformance_record"] = related_non_conformance_record
	frappe.get_doc(row).insert(ignore_permissions=True)


def _sync_non_conformance_count(inspection_record: str) -> None:
	cnt = len(
		frappe.get_all(
			NC,
			filters={"inspection_record": inspection_record, "status": ["!=", "Cancelled"]},
			pluck="name",
		)
	)
	frappe.db.set_value(IR, inspection_record, "non_conformance_count", cnt, update_modified=False)


def raise_non_conformance(inspection_record_id: str, issue_data: dict[str, Any]) -> dict[str, Any]:
	"""Register a **Non Conformance Record** and emit **NonConformanceRaised**."""
	irn = _norm(inspection_record_id)
	if not irn or not frappe.db.exists(IR, irn):
		frappe.throw(_("Inspection Record not found."), frappe.ValidationError)

	data = issue_data or {}
	bid = _norm(data.get("business_id"))
	if not bid:
		frappe.throw(_("business_id is required."), frappe.ValidationError)
	if frappe.db.exists(NC, {"business_id": bid}):
		frappe.throw(_("Non Conformance business_id already exists."), frappe.ValidationError)

	it = _norm(data.get("issue_type"))
	if it not in _ISSUE_TYPES:
		frappe.throw(_("Invalid issue_type."), frappe.ValidationError)
	title = _norm(data.get("issue_title"))
	if not title:
		frappe.throw(_("issue_title is required."), frappe.ValidationError)
	sev = _norm(data.get("severity"))
	if sev not in _SEVERITIES:
		frappe.throw(_("Invalid severity."), frappe.ValidationError)

	ir = frappe.get_doc(IR, irn)
	if int(ir.is_locked or 0):
		frappe.throw(_("Inspection is locked."), frappe.ValidationError)

	nc = frappe.new_doc(NC)
	nc.business_id = bid
	nc.inspection_record = irn
	nc.contract = ir.contract
	nc.issue_type = it
	nc.issue_title = title
	nc.severity = sev
	nc.status = _norm(data.get("status")) or "Open"

	for fn in (
		"contract_milestone",
		"contract_deliverable",
		"checklist_line_ref",
		"issue_description",
		"required_corrective_action",
		"remarks",
	):
		if data.get(fn) is not None:
			setattr(nc, fn, data.get(fn))

	if data.get("corrective_action_due_date") is not None:
		nc.corrective_action_due_date = data.get("corrective_action_due_date")

	nc.insert(ignore_permissions=True)
	_sync_non_conformance_count(irn)

	summary = _("Non-conformance raised: {0} ({1})").format(title, it)
	_append_inspection_event(irn, "NonConformanceRaised", summary, related_non_conformance_record=nc.name)

	return {"name": nc.name, "business_id": nc.business_id, "inspection_record": irn}


def submit_corrective_action_resolution(non_conformance_id: str, data: dict[str, Any]) -> dict[str, Any]:
	"""Record supplier / contractor corrective action details; moves **Open** → **In Progress**."""
	ncn = _norm(non_conformance_id)
	if not ncn or not frappe.db.exists(NC, ncn):
		frappe.throw(_("Non Conformance Record not found."), frappe.ValidationError)

	payload = data or {}
	summary = _norm(payload.get("resolution_summary"))
	if not summary:
		frappe.throw(_("resolution_summary is required."), frappe.ValidationError)

	nc = frappe.get_doc(NC, ncn)
	st = _norm(nc.status)
	if st in ("Resolved", "Waived", "Cancelled"):
		frappe.throw(_("This non-conformance is already closed."), frappe.ValidationError)
	if st not in ("Open", "In Progress"):
		frappe.throw(_("Invalid non-conformance status for corrective submission."), frappe.ValidationError)

	nc.resolution_summary = summary
	if payload.get("resolved_by_user"):
		nc.resolved_by_user = _norm(payload.get("resolved_by_user"))
	else:
		nc.resolved_by_user = frappe.session.user
	nc.status = "In Progress"
	if payload.get("remarks") is not None:
		nc.remarks = payload.get("remarks")
	nc.save(ignore_permissions=True)

	irn = _norm(nc.inspection_record)
	_append_inspection_event(
		irn,
		"Other",
		_("Corrective action resolution submitted for non-conformance {0}.").format(nc.business_id),
		related_non_conformance_record=nc.name,
		actor_user=_norm(payload.get("resolved_by_user")) or None,
	)

	return {"name": nc.name, "status": nc.status}


def approve_non_conformance_resolution(non_conformance_id: str, data: dict[str, Any]) -> dict[str, Any]:
	"""Formal approval closing the NC as **Resolved** or **Waived**."""
	ncn = _norm(non_conformance_id)
	if not ncn or not frappe.db.exists(NC, ncn):
		frappe.throw(_("Non Conformance Record not found."), frappe.ValidationError)

	payload = data or {}
	outcome = _norm(payload.get("outcome"))
	if outcome not in _APPROVE_OUTCOMES:
		frappe.throw(_("outcome must be Resolved or Waived."), frappe.ValidationError)

	nc = frappe.get_doc(NC, ncn)
	if _norm(nc.status) != "In Progress":
		frappe.throw(
			_("Non-conformance must be In Progress (corrective action submitted) before approval."),
			frappe.ValidationError,
		)

	if outcome == "Waived":
		waiver_user = _norm(payload.get("waiver_approved_by_user"))
		if not waiver_user or not frappe.db.exists("User", waiver_user):
			frappe.throw(_("waiver_approved_by_user is required for a waiver."), frappe.ValidationError)
		nc.waiver_approved_by_user = waiver_user
		nc.status = "Waived"
	else:
		nc.status = "Resolved"
		if payload.get("resolved_by_user"):
			nc.resolved_by_user = _norm(payload.get("resolved_by_user"))

	nc.resolved_on = payload.get("resolved_on") or now_datetime()
	if payload.get("resolution_summary"):
		nc.resolution_summary = _norm(payload.get("resolution_summary"))
	if payload.get("remarks") is not None:
		nc.remarks = payload.get("remarks")

	nc.save(ignore_permissions=True)

	irn = _norm(nc.inspection_record)
	_append_inspection_event(
		irn,
		"Other",
		_("Non-conformance resolution approved ({0}) for {1}.").format(outcome, nc.business_id),
		related_non_conformance_record=nc.name,
		actor_user=frappe.session.user,
	)

	return {"name": nc.name, "status": nc.status, "resolved_on": str(nc.resolved_on)}


def create_reinspection(inspection_record_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Create a **Reinspection Record** and flag the inspection; emits **ReinspectionScheduled**."""
	irn = _norm(inspection_record_id)
	if not irn or not frappe.db.exists(IR, irn):
		frappe.throw(_("Inspection Record not found."), frappe.ValidationError)

	payload = data or {}
	ir = frappe.get_doc(IR, irn)
	if int(ir.is_locked or 0):
		frappe.throw(_("Inspection is locked."), frappe.ValidationError)

	tr = _norm(payload.get("trigger_reason")) or "Non Conformance"
	if tr not in _RR_TRIGGERS:
		frappe.throw(_("Invalid trigger_reason."), frappe.ValidationError)

	rr = frappe.new_doc(RR)
	rr.inspection_record = irn
	rr.contract = ir.contract
	rr.trigger_reason = tr
	rr.status = _norm(payload.get("status")) or "Planned"
	if payload.get("scheduled_datetime") is not None:
		rr.scheduled_datetime = payload.get("scheduled_datetime")
	if payload.get("actual_datetime") is not None:
		rr.actual_datetime = payload.get("actual_datetime")
	if payload.get("outcome_summary") is not None:
		rr.outcome_summary = payload.get("outcome_summary")
	if payload.get("remarks") is not None:
		rr.remarks = payload.get("remarks")
	if payload.get("linked_followup_inspection"):
		rr.linked_followup_inspection = _norm(payload.get("linked_followup_inspection"))
	rr.created_by_user = _norm(payload.get("created_by_user")) or frappe.session.user

	rr.insert(ignore_permissions=True)

	ir.reload()
	ir.is_reinspection_required = 1
	if payload.get("reinspection_due_date") is not None:
		ir.reinspection_due_date = payload.get("reinspection_due_date")
	elif rr.scheduled_datetime:
		ir.reinspection_due_date = getdate(rr.scheduled_datetime)
	ir.save(ignore_permissions=True)

	summary = _("Reinspection scheduled ({0}).").format(tr)
	_append_inspection_event(irn, "ReinspectionScheduled", summary, actor_user=rr.created_by_user)

	return {"name": rr.name, "inspection_record": irn, "linked_followup_inspection": rr.linked_followup_inspection}
