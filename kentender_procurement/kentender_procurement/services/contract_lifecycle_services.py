# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Contract lifecycle: suspend, resume, terminate, close (PROC-STORY-098)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender.services.audit_event_service import log_audit_event
from kentender.workflow_engine.safeguards import workflow_mutation_context

PC = "Procurement Contract"
PCSE = "Procurement Contract Status Event"

SOURCE_MODULE = "kentender_procurement.contract_lifecycle_services"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _event(contract_name: str, event_type: str, summary: str, status_result: str | None = None) -> None:
	frappe.get_doc(
		{
			"doctype": PCSE,
			"procurement_contract": contract_name,
			"event_type": event_type,
			"event_datetime": now_datetime(),
			"actor_user": _norm(frappe.session.user) or "Administrator",
			"summary": summary,
			"status_result": status_result,
		}
	).insert(ignore_permissions=True)


def suspend_contract(contract_id: str, *, reason: str | None = None) -> dict[str, Any]:
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	if _norm(doc.status) != "Active":
		frappe.throw(_("Only active contracts can be suspended."), frappe.ValidationError)
	doc.status = "Suspended"
	doc.workflow_state = "Suspended"
	if reason:
		doc.remarks = (doc.remarks or "") + "\n" + _("Suspend: {0}").format(reason)
	with workflow_mutation_context():
		doc.save(ignore_permissions=True)
	_event(cn, "Suspended", _("Contract suspended."), "Suspended")
	log_audit_event(
		event_type="procurement_contract.suspended",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"status": "Suspended"}),
	)
	return {"name": cn, "status": doc.status}


def resume_contract(contract_id: str) -> dict[str, Any]:
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	if _norm(doc.status) != "Suspended":
		frappe.throw(_("Only suspended contracts can be resumed."), frappe.ValidationError)
	doc.status = "Active"
	doc.workflow_state = "Active"
	with workflow_mutation_context():
		doc.save(ignore_permissions=True)
	_event(cn, "Resumed", _("Contract resumed."), "Active")
	log_audit_event(
		event_type="procurement_contract.resumed",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"status": "Active"}),
	)
	return {"name": cn, "status": doc.status}


def terminate_contract(contract_id: str, *, reason: str | None = None) -> dict[str, Any]:
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	st = _norm(doc.status)
	if st not in ("Active", "Suspended"):
		frappe.throw(_("Only active or suspended contracts can be terminated."), frappe.ValidationError)
	doc.status = "Terminated"
	doc.workflow_state = "Terminated"
	if reason:
		doc.termination_reason = reason
	with workflow_mutation_context():
		doc.save(ignore_permissions=True)
	_event(cn, "Terminated", _("Contract terminated."), "Terminated")
	log_audit_event(
		event_type="procurement_contract.terminated",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"status": "Terminated"}),
	)
	return {"name": cn, "status": doc.status}


def close_contract(contract_id: str, *, notes: str | None = None) -> dict[str, Any]:
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	st = _norm(doc.status)
	if st not in ("Active", "Suspended", "Terminated"):
		frappe.throw(_("Contract cannot move to closed from this state."), frappe.ValidationError)
	doc.status = "Closed"
	doc.workflow_state = "Closed"
	if notes:
		doc.closure_notes = notes
	with workflow_mutation_context():
		doc.save(ignore_permissions=True)
	_event(cn, "Closed", _("Contract closed."), "Closed")
	log_audit_event(
		event_type="procurement_contract.closed",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"status": "Closed"}),
	)
	return {"name": cn, "status": doc.status}
