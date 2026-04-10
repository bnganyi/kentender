# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Contract variation request / approve / apply (PROC-STORY-097)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

from kentender.services.audit_event_service import log_audit_event
from kentender_budget.services.budget_downstream import validate_funds_or_raise

PC = "Procurement Contract"
PCV = "Procurement Contract Variation"
PCSE = "Procurement Contract Status Event"

SOURCE_MODULE = "kentender_procurement.contract_variation_services"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _append_event(contract_name: str, event_type: str, summary: str, variation: str | None = None) -> None:
	frappe.get_doc(
		{
			"doctype": PCSE,
			"procurement_contract": contract_name,
			"event_type": event_type,
			"event_datetime": now_datetime(),
			"actor_user": _norm(frappe.session.user) or "Administrator",
			"summary": summary,
			"related_variation": variation,
		}
	).insert(ignore_permissions=True)


def request_contract_variation(
	contract_id: str,
	*,
	reason: str,
	variation_type: str = "Combined",
	value_change_amount: float | None = None,
	new_contract_value: float | None = None,
	new_end_date: str | None = None,
) -> dict[str, Any]:
	cn = _norm(contract_id)
	doc = frappe.get_doc(PC, cn)
	if _norm(doc.status) not in ("Active", "Suspended"):
		frappe.throw(_("Variations require an active or suspended contract."), frappe.ValidationError)

	existing = frappe.db.count(PCV, filters={"procurement_contract": cn}) or 0
	var_no = existing + 1
	biz = f"{_norm(doc.business_id)}-V{var_no}"

	pcv = frappe.new_doc(PCV)
	pcv.business_id = biz
	pcv.procurement_contract = cn
	pcv.variation_no = var_no
	pcv.variation_type = _norm(variation_type) or "Combined"
	pcv.status = "Draft"
	pcv.reason = _norm(reason)
	pcv.value_change_amount = value_change_amount
	pcv.old_contract_value = flt(doc.contract_value)
	pcv.new_contract_value = flt(new_contract_value) if new_contract_value is not None else None
	pcv.old_end_date = doc.contract_end_date
	pcv.new_end_date = new_end_date
	pcv.requested_by_user = _norm(frappe.session.user) or "Administrator"
	pcv.requested_on = now_datetime()
	pcv.budget_validation_status = "Pending" if (new_contract_value and flt(new_contract_value) > flt(doc.contract_value)) else "Not Required"
	pcv.insert(ignore_permissions=True)

	_append_event(cn, "Variation Requested", "Variation requested.", pcv.name)
	log_audit_event(
		event_type="procurement_contract.variation_requested",
		source_module=SOURCE_MODULE,
		target_doctype=PCV,
		target_docname=pcv.name,
	)
	return {"name": pcv.name, "business_id": pcv.business_id}


def approve_contract_variation(variation_id: str, *, comments: str | None = None) -> dict[str, Any]:
	vn = _norm(variation_id)
	pcv = frappe.get_doc(PCV, vn)
	if _norm(pcv.status) not in ("Draft", "Submitted"):
		frappe.throw(_("Variation cannot be approved in this state."), frappe.ValidationError)
	pcv.status = "Approved"
	pcv.approved_by_user = _norm(frappe.session.user) or "Administrator"
	pcv.approved_on = now_datetime()
	if comments:
		pcv.impact_notes = _norm(comments)
	pcv.save(ignore_permissions=True)

	_append_event(
		_norm(pcv.procurement_contract),
		"Other",
		_("Variation approved."),
		vn,
	)
	return {"name": vn, "status": pcv.status}


def apply_contract_variation(variation_id: str) -> dict[str, Any]:
	"""Apply approved variation to the contract (no silent desk edits to active terms)."""
	vn = _norm(variation_id)
	pcv = frappe.get_doc(PCV, vn)
	if _norm(pcv.status) != "Approved":
		frappe.throw(_("Only approved variations can be applied."), frappe.ValidationError)

	cdoc = frappe.get_doc(PC, pcv.procurement_contract)
	if _norm(cdoc.status) not in ("Active", "Suspended"):
		frappe.throw(_("Contract must be active or suspended to apply a variation."), frappe.ValidationError)

	old_val = flt(cdoc.contract_value)
	new_val = pcv.new_contract_value
	if new_val is not None:
		nv = flt(new_val)
		delta = nv - old_val
		bl = _norm(cdoc.budget_line)
		ent = _norm(cdoc.procuring_entity)
		if delta > 0 and bl and ent:
			validate_funds_or_raise(bl, delta, "commit_from_available", ent)
			pcv.budget_validation_status = "Passed"
		elif delta > 0:
			frappe.throw(_("Budget line required for value increase."), frappe.ValidationError)
		cdoc.contract_value = nv

	if pcv.new_end_date:
		cdoc.contract_end_date = getdate(pcv.new_end_date)

	cdoc.variation_count = (cdoc.variation_count or 0) + 1
	cdoc.latest_variation_ref = vn
	cdoc.save(ignore_permissions=True)

	pcv.status = "Applied"
	pcv.save(ignore_permissions=True)

	_append_event(
		cdoc.name,
		"Variation Applied",
		_("Variation applied to contract."),
		vn,
	)
	log_audit_event(
		event_type="procurement_contract.variation_applied",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cdoc.name,
		new_state=json.dumps({"variation": vn}),
	)
	return {"contract": cdoc.name, "variation": vn}
