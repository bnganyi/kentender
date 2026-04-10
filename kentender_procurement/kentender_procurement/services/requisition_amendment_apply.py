# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Apply approved Requisition Amendment Records to Purchase Requisitions (PROC-STORY-008).

``after_summary`` JSON contract (when machine apply is used):

- **Cancellation:** ``{}`` or ``{"confirm": true}``
- **Quantity Change** / **Cost Estimate Change:**
  ``{"items":[{"idx":1,"quantity":2.0,"estimated_unit_cost":500.0}]}`` — ``idx`` matches child row
  ``idx``; omit keys to leave fields unchanged.
- **Budget Line Change:**
  ``{"budget_line":"...", "budget":"...", "budget_control_period":"..."}`` — include keys to update.

**Strategic Linkage Correction** and **Need Specification Change** are not implemented in V1
(raise ``ValidationError``).

All budget movements use ``kentender_budget.services.budget_ledger_posting`` only.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

from kentender.services.audit_event_service import log_audit_event
from kentender_budget.services.budget_availability import availability_headroom
from kentender_budget.services.budget_ledger_posting import release_reservation, reserve_budget
from kentender_procurement.services.purchase_requisition_validation import (
	recompute_requested_amount_from_items,
)

AMENDMENT_DOCTYPE = "Requisition Amendment Record"
PR_DOCTYPE = "Purchase Requisition"
SOURCE_MODULE = "kentender_procurement"
SOURCE_ACTION = "apply_amendment"

AUDIT_APPLIED = "kt.procurement.requisition.amendment_applied"

TYPE_QUANTITY = "Quantity Change"
TYPE_COST = "Cost Estimate Change"
TYPE_STRATEGIC = "Strategic Linkage Correction"
TYPE_BUDGET_LINE = "Budget Line Change"
TYPE_SPEC = "Need Specification Change"
TYPE_CANCEL = "Cancellation"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _parse_after_summary(raw: str | None) -> dict[str, Any]:
	text = (raw or "").strip()
	if not text:
		return {}
	try:
		out = json.loads(text)
	except json.JSONDecodeError as e:
		frappe.throw(
			_("After Summary must be valid JSON for this amendment type. {0}").format(str(e)),
			frappe.ValidationError,
			title=_("Invalid JSON"),
		)
	return out if isinstance(out, dict) else {}


@contextmanager
def _approved_pr_mutation_allowed():
	prev = frappe.flags.get("allow_approved_requisition_mutation")
	frappe.flags.allow_approved_requisition_mutation = True
	try:
		yield
	finally:
		if prev is None:
			try:
				del frappe.flags["allow_approved_requisition_mutation"]
			except KeyError:
				frappe.flags.allow_approved_requisition_mutation = False
		else:
			frappe.flags.allow_approved_requisition_mutation = prev


def _related_pr(pr: Document) -> dict[str, str | None]:
	return {"related_requisition": pr.name}


def _reservation_active(pr: Document) -> bool:
	return _norm(pr.get("budget_reservation_status")) == "Reserved" and bool(
		_norm(pr.get("budget_line"))
	)


def _sync_pr_reservation_fields(pr: Document, budget_line: str | None) -> None:
	if not budget_line:
		return
	pr.set("available_budget_at_check", availability_headroom(budget_line))
	pr.set("budget_check_datetime", now_datetime())


def _apply_item_patches(pr: Document, items_payload: list[Any]) -> None:
	if not isinstance(items_payload, list):
		frappe.throw(_("items must be a JSON array."), frappe.ValidationError)
	for patch in items_payload:
		if not isinstance(patch, dict) or "idx" not in patch:
			frappe.throw(_("Each items entry must be an object with idx."), frappe.ValidationError)
		target = int(patch["idx"])
		found = False
		for row in pr.get("items") or []:
			if int(row.idx) == target:
				found = True
				if "quantity" in patch:
					row.quantity = flt(patch["quantity"])
				if "estimated_unit_cost" in patch:
					row.estimated_unit_cost = flt(patch["estimated_unit_cost"])
				row.run_method("validate")
				break
		if not found:
			frappe.throw(
				_("No line item with idx {0}.").format(target),
				frappe.ValidationError,
				title=_("Invalid item idx"),
			)


def _budget_delta(
	pr: Document,
	amendment: Document,
	old_requested: float,
	new_requested: float,
) -> None:
	line = _norm(pr.get("budget_line"))
	if not line or not _reservation_active(pr):
		return

	delta = flt(new_requested) - flt(old_requested)
	if abs(delta) < 1e-9:
		pr.set("reserved_amount", flt(new_requested))
		_sync_pr_reservation_fields(pr, line)
		return

	if delta > 0:
		ble = reserve_budget(
			line,
			delta,
			source_doctype=AMENDMENT_DOCTYPE,
			source_docname=amendment.name,
			source_action=SOURCE_ACTION,
			source_business_id=_norm(pr.name) or None,
			related=_related_pr(pr),
			idempotency_key=f"RAM|{amendment.name}|delta_reserve|{round(delta, 6)}",
		)
		pr.set("last_budget_action_ref", ble)
	else:
		ble = release_reservation(
			line,
			-delta,
			source_doctype=AMENDMENT_DOCTYPE,
			source_docname=amendment.name,
			source_action=SOURCE_ACTION,
			source_business_id=_norm(pr.name) or None,
			related=_related_pr(pr),
			idempotency_key=f"RAM|{amendment.name}|delta_release|{round(-delta, 6)}",
		)
		pr.set("last_budget_action_ref", ble)

	pr.set("reserved_amount", flt(new_requested))
	_sync_pr_reservation_fields(pr, line)


def _apply_cancellation(pr: Document, amendment: Document, _payload: dict[str, Any]) -> None:
	line = _norm(pr.get("budget_line"))
	if _reservation_active(pr) and line:
		amt = flt(pr.get("reserved_amount"))
		if amt > 1e-9:
			ble = release_reservation(
				line,
				amt,
				source_doctype=AMENDMENT_DOCTYPE,
				source_docname=amendment.name,
				source_action=SOURCE_ACTION,
				source_business_id=_norm(pr.name) or None,
				related=_related_pr(pr),
				idempotency_key=f"RAM|{amendment.name}|cancel_release",
			)
			pr.set("last_budget_action_ref", ble)
	pr.set("budget_reservation_status", "Released")
	pr.set("reserved_amount", 0.0)
	pr.set("status", "Cancelled")
	pr.set("workflow_state", "Cancelled")
	pr.set("approval_status", "Cancelled")


def _apply_budget_line_change(pr: Document, amendment: Document, payload: dict[str, Any]) -> None:
	old_line = _norm(pr.get("budget_line"))
	old_reserved = flt(pr.get("reserved_amount"))
	if _reservation_active(pr) and old_line and old_reserved > 1e-9:
		release_reservation(
			old_line,
			old_reserved,
			source_doctype=AMENDMENT_DOCTYPE,
			source_docname=amendment.name,
			source_action=SOURCE_ACTION,
			source_business_id=_norm(pr.name) or None,
			related=_related_pr(pr),
			idempotency_key=f"RAM|{amendment.name}|bl_release|{old_line}",
		)
	if "budget_line" in payload:
		pr.set("budget_line", _norm(payload.get("budget_line")) or None)
	if "budget" in payload:
		pr.set("budget", _norm(payload.get("budget")) or None)
	if "budget_control_period" in payload:
		pr.set("budget_control_period", _norm(payload.get("budget_control_period")) or None)

	recompute_requested_amount_from_items(pr)
	new_line = _norm(pr.get("budget_line"))
	new_req = flt(pr.get("requested_amount"))
	if new_line and new_req > 1e-9:
		ble = reserve_budget(
			new_line,
			new_req,
			source_doctype=AMENDMENT_DOCTYPE,
			source_docname=amendment.name,
			source_action=SOURCE_ACTION,
			source_business_id=_norm(pr.name) or None,
			related=_related_pr(pr),
			idempotency_key=f"RAM|{amendment.name}|bl_reserve|{new_line}",
		)
		pr.set("budget_reservation_status", "Reserved")
		pr.set("reserved_amount", new_req)
		pr.set("last_budget_action_ref", ble)
		_sync_pr_reservation_fields(pr, new_line)
	else:
		pr.set("budget_reservation_status", "None")
		pr.set("reserved_amount", 0.0)


def apply_requisition_amendment(amendment_id: str) -> Document:
	"""Apply an **Approved** amendment to its purchase requisition. Sets amendment to **Applied**."""
	aid = _norm(amendment_id)
	if not aid:
		frappe.throw(_("Amendment id is required."), frappe.ValidationError)

	amendment = frappe.get_doc(AMENDMENT_DOCTYPE, aid)
	st = _norm(amendment.status)
	if st == "Applied":
		frappe.throw(
			_("This amendment has already been applied."),
			frappe.ValidationError,
			title=_("Already applied"),
		)
	if st != "Approved":
		frappe.throw(
			_("Only approved amendments can be applied (status is {0}).").format(frappe.bold(st or "?")),
			frappe.ValidationError,
			title=_("Invalid status"),
		)

	pr_name = _norm(amendment.purchase_requisition)
	if not pr_name:
		frappe.throw(_("Purchase Requisition is required on the amendment."), frappe.ValidationError)

	pr = frappe.get_doc(PR_DOCTYPE, pr_name)
	if _norm(pr.status) == "Cancelled":
		frappe.throw(
			_("Cancelled requisitions cannot be amended through this service."),
			frappe.ValidationError,
			title=_("Cancelled"),
		)
	if _norm(pr.workflow_state) != "Approved":
		frappe.throw(
			_("Purchase Requisition must be in Approved workflow state."),
			frappe.ValidationError,
			title=_("Invalid requisition state"),
		)

	payload = _parse_after_summary(amendment.after_summary)
	at = _norm(amendment.amendment_type)

	with _approved_pr_mutation_allowed():
		if at == TYPE_CANCEL:
			_apply_cancellation(pr, amendment, payload)
		elif at in (TYPE_QUANTITY, TYPE_COST):
			items = payload.get("items")
			if not items:
				frappe.throw(
					_("after_summary JSON must include an items array for this amendment type."),
					frappe.ValidationError,
				)
			old_requested = flt(pr.get("requested_amount"))
			_apply_item_patches(pr, items)
			recompute_requested_amount_from_items(pr)
			new_requested = flt(pr.get("requested_amount"))
			_budget_delta(pr, amendment, old_requested, new_requested)
		elif at == TYPE_BUDGET_LINE:
			_apply_budget_line_change(pr, amendment, payload)
		elif at in (TYPE_STRATEGIC, TYPE_SPEC):
			frappe.throw(
				_("Amendment type {0} is not implemented yet.").format(frappe.bold(at)),
				frappe.ValidationError,
				title=_("Not implemented"),
			)
		else:
			frappe.throw(
				_("Unknown amendment type {0}.").format(frappe.bold(at)),
				frappe.ValidationError,
			)

		pr.save()

	amendment.reload()
	amendment.status = "Applied"
	amendment.save()

	log_audit_event(
		event_type=AUDIT_APPLIED,
		source_module=SOURCE_MODULE,
		target_doctype=PR_DOCTYPE,
		target_docname=pr.name,
		procuring_entity=_norm(pr.get("procuring_entity")) or None,
		reason=_("Amendment {0} applied ({1}).").format(amendment.name, at),
		new_state=json.dumps(
			{"amendment": amendment.name, "amendment_type": at},
			sort_keys=True,
		),
	)

	return amendment
