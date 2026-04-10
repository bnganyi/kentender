# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Apply approved **Procurement Plan Revision** documents to plan items (PROC-STORY-020).

Idempotent: revisions in **Applied** status cannot be applied again.

Line semantics (v1):

- **Update:** ``estimated_amount += flt(change_amount)``; missing ``change_amount`` treated as 0.
- **Add:** set ``estimated_amount`` to ``change_amount`` (absolute); ``change_amount`` must be set (not None).
- **Cancel:** set item ``status`` to **Cancelled**; ``change_notes`` copied to ``cancellation_reason`` when present.
- **Supersede:** set item ``status`` to **Superseded**.

**Add** assumes a stub **Procurement Plan Item** already exists on the plan (PROC-STORY-019 validation).

PCS totals may diverge from ``estimated_amount`` after amount-only changes; operators may need to adjust
**Plan Consolidation Source** rows separately—this service does not reconcile them automatically.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

from kentender.services.audit_event_service import log_audit_event

REVISION_DOCTYPE = "Procurement Plan Revision"
PPI_DOCTYPE = "Procurement Plan Item"
PP_DOCTYPE = "Procurement Plan"

SOURCE_MODULE = "kentender_procurement"
AUDIT_REVISION_APPLIED = "procurement.plan_revision.applied"

STATUS_APPROVED = "Approved"
STATUS_APPLIED = "Applied"

ACTION_UPDATE = "Update"
ACTION_ADD = "Add"
ACTION_CANCEL = "Cancel"
ACTION_SUPERSEDE = "Supersede"

AMOUNT_TOLERANCE = 1e-9


def _norm(s: str | None) -> str:
	return (s or "").strip()


def apply_procurement_plan_revision(revision_id: str) -> dict[str, Any]:
	"""Apply an **Approved** procurement plan revision; set revision to **Applied** and log audit.

	:param revision_id: ``name`` of **Procurement Plan Revision**.
	:returns: Summary dict with ``revision``, ``procurement_plan``, ``lines_applied``, ``items_touched``.
	"""
	rid = _norm(revision_id)
	if not rid:
		frappe.throw(_("Revision id is required."), frappe.ValidationError)
	if not frappe.db.exists(REVISION_DOCTYPE, rid):
		frappe.throw(
			_("Procurement Plan Revision {0} does not exist.").format(frappe.bold(rid)),
			frappe.ValidationError,
			title=_("Not found"),
		)

	rev = frappe.get_doc(REVISION_DOCTYPE, rid)
	st = _norm(rev.status)
	if st == STATUS_APPLIED:
		frappe.throw(
			_("This revision has already been applied."),
			frappe.ValidationError,
			title=_("Already applied"),
		)
	if st != STATUS_APPROVED:
		frappe.throw(
			_("Only approved revisions can be applied (status is {0}).").format(frappe.bold(st or "?")),
			frappe.ValidationError,
			title=_("Invalid status"),
		)

	lines = list(rev.get("revision_lines") or [])
	if not lines:
		frappe.throw(
			_("Revision has no lines to apply."),
			frappe.ValidationError,
			title=_("Empty revision"),
		)

	plan = _norm(rev.source_procurement_plan)
	if not plan:
		frappe.throw(
			_("Source Procurement Plan is required."),
			frappe.ValidationError,
			title=_("Invalid revision"),
		)

	procuring_entity = _norm(frappe.db.get_value(PP_DOCTYPE, plan, "procuring_entity")) or None

	save_point = f"ppr_apply_{frappe.generate_hash(length=10)}"
	frappe.db.savepoint(save_point)
	touched_items: list[str] = []
	line_summaries: list[dict[str, Any]] = []

	try:
		for row in lines:
			item_name = _norm(row.get("affected_plan_item"))
			if not item_name:
				frappe.throw(
					_("Each revision line must set Affected Plan Item."),
					frappe.ValidationError,
					title=_("Invalid line"),
				)
			action = _norm(row.get("action_type"))
			if not action:
				frappe.throw(
					_("Each revision line must set Action Type."),
					frappe.ValidationError,
					title=_("Invalid line"),
				)

			if not frappe.db.exists(PPI_DOCTYPE, item_name):
				frappe.throw(
					_("Procurement Plan Item {0} does not exist.").format(frappe.bold(item_name)),
					frappe.ValidationError,
					title=_("Invalid item"),
				)

			ppi = frappe.get_doc(PPI_DOCTYPE, item_name)
			if _norm(ppi.procurement_plan) != plan:
				frappe.throw(
					_("Line item {0} does not belong to procurement plan {1}.").format(
						frappe.bold(item_name), frappe.bold(plan)
					),
					frappe.ValidationError,
					title=_("Plan mismatch"),
				)

			if action == ACTION_UPDATE:
				delta = flt(row.get("change_amount"))
				new_est = flt(ppi.estimated_amount) + delta
				if new_est < -AMOUNT_TOLERANCE:
					frappe.throw(
						_("Estimated amount cannot be negative after update for item {0}.").format(
							frappe.bold(item_name)
						),
						frappe.ValidationError,
						title=_("Invalid amount"),
					)
				ppi.estimated_amount = new_est
			elif action == ACTION_ADD:
				if row.get("change_amount") is None:
					frappe.throw(
						_("Add action requires change_amount on line for item {0}.").format(
							frappe.bold(item_name)
						),
						frappe.ValidationError,
						title=_("Missing amount"),
					)
				amt = flt(row.get("change_amount"))
				if amt < -AMOUNT_TOLERANCE:
					frappe.throw(
						_("change_amount cannot be negative for Add on item {0}.").format(
							frappe.bold(item_name)
						),
						frappe.ValidationError,
						title=_("Invalid amount"),
					)
				ppi.estimated_amount = amt
			elif action == ACTION_CANCEL:
				ppi.status = "Cancelled"
				cn = _norm(row.get("change_notes"))
				if cn:
					ppi.cancellation_reason = cn
			elif action == ACTION_SUPERSEDE:
				ppi.status = "Superseded"
			else:
				frappe.throw(
					_("Unknown action type {0}.").format(frappe.bold(action)),
					frappe.ValidationError,
					title=_("Invalid action"),
				)

			ppi.save(ignore_permissions=True)
			touched_items.append(item_name)
			line_summaries.append({"affected_plan_item": item_name, "action_type": action})

		rev.reload()
		rev.status = STATUS_APPLIED
		rev.save(ignore_permissions=True)

		frappe.db.release_savepoint(save_point)
	except Exception:
		frappe.db.rollback(save_point=save_point)
		raise

	summary_payload = {
		"revision": rev.name,
		"revision_business_id": _norm(rev.revision_business_id),
		"procurement_plan": plan,
		"lines": line_summaries,
	}
	log_audit_event(
		event_type=AUDIT_REVISION_APPLIED,
		source_module=SOURCE_MODULE,
		target_doctype=REVISION_DOCTYPE,
		target_docname=rev.name,
		procuring_entity=procuring_entity,
		reason=_("Procurement plan revision {0} applied.").format(_norm(rev.revision_business_id) or rev.name),
		new_state=json.dumps(summary_payload, sort_keys=True),
	)

	return {
		"revision": rev.name,
		"revision_business_id": _norm(rev.revision_business_id),
		"procurement_plan": plan,
		"lines_applied": len(lines),
		"items_touched": touched_items,
	}


__all__ = ["apply_procurement_plan_revision", "AUDIT_REVISION_APPLIED", "SOURCE_MODULE"]
