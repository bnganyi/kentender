# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Activate procurement contract (PROC-STORY-096)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender.services.audit_event_service import log_audit_event
from kentender.workflow_engine.safeguards import workflow_mutation_context

PC = "Procurement Contract"
PCSR = "Procurement Contract Signing Record"
PCSE = "Procurement Contract Status Event"

SOURCE_MODULE = "kentender_procurement.contract_activation_service"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def activate_contract(contract_id: str) -> dict[str, Any]:
	"""Set contract to **Active** after approval and completed signing evidence."""
	cn = _norm(contract_id)
	if not cn or not frappe.db.exists(PC, cn):
		frappe.throw(_("Procurement Contract not found."), frappe.ValidationError)

	doc = frappe.get_doc(PC, cn)
	if _norm(doc.approval_status) != "Approved":
		frappe.throw(_("Contract must be approved before activation."), frappe.ValidationError)

	signatures = (
		frappe.get_all(
			PCSR,
			filters={"procurement_contract": cn, "status": "Completed"},
			fields=["name", "hash_value", "signed_document"],
			order_by="signed_on desc",
			limit=1,
		)
		or []
	)
	if not signatures:
		frappe.throw(_("Completed signing record required before activation."), frappe.ValidationError)
	sig = signatures[0]
	if not _norm(sig.get("hash_value")) and not _norm(sig.get("signed_document")):
		frappe.throw(_("Signing record must include hash or signed document."), frappe.ValidationError)

	ts = now_datetime()
	with workflow_mutation_context():
		doc.status = "Active"
		doc.workflow_state = "Active"
		doc.actual_activation_date = ts
		doc.save(ignore_permissions=True)

	frappe.get_doc(
		{
			"doctype": PCSE,
			"procurement_contract": cn,
			"event_type": "Activated",
			"event_datetime": ts,
			"actor_user": _norm(frappe.session.user) or "Administrator",
			"summary": _("Contract activated."),
			"status_result": "Active",
		}
	).insert(ignore_permissions=True)

	log_audit_event(
		event_type="procurement_contract.activated",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=cn,
		new_state=json.dumps({"status": "Active"}),
		event_datetime=ts,
	)

	return {"name": cn, "status": doc.status, "actual_activation_date": str(ts)}
