# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Contract approval and signing workflow (PROC-STORY-095)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender.services.audit_event_service import log_audit_event

PC = "Procurement Contract"
PCAR = "Procurement Contract Approval Record"
PCSR = "Procurement Contract Signing Record"
PCSE = "Procurement Contract Status Event"

SOURCE_MODULE = "kentender_procurement.contract_approval_signature_services"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _actor_role() -> str:
	return (frappe.get_roles(_norm(frappe.session.user)) or ["Guest"])[0]


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
	doc.workflow_state = "In Review"
	doc.save(ignore_permissions=True)

	frappe.get_doc(
		{
			"doctype": PCAR,
			"procurement_contract": cn,
			"workflow_step": "Submit",
			"approver_user": _norm(frappe.session.user) or "Administrator",
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
	doc.approval_status = "Approved"
	doc.workflow_state = "Pending Signature"
	doc.save(ignore_permissions=True)

	frappe.get_doc(
		{
			"doctype": PCAR,
			"procurement_contract": cn,
			"workflow_step": "Approve",
			"approver_user": _norm(frappe.session.user) or "Administrator",
			"approver_role": _actor_role(),
			"action_type": "Approve",
			"action_datetime": now_datetime(),
			"comments": _norm(comments),
			"decision_level": "Final",
		}
	).insert(ignore_permissions=True)

	_append_status_event(cn, "Approved", _("Contract approved; awaiting signature."))
	log_audit_event(
		event_type="procurement_contract.approved",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"approval_status": "Approved"}),
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
