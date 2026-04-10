# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Orchestrate Approved purchase requisitions into a procurement plan (PROC-STORY-018).

Creates **Procurement Plan Item**, **Plan Consolidation Source**, and **Requisition Planning Link**
rows so traceability and plan totals stay aligned. Over-planning is enforced by existing RPL
validation (``requisition_planning_allocation``).

Assumptions:

- **Approved** means ``workflow_state == "Approved"`` (not ``approval_status`` alone).
- Which requisitions are merged is **caller-defined** via ``mode`` and the ``lines`` batch; there is
  no automatic matching heuristic in v1.
- ``target_procurement_plan_item`` appends PCS/RPL rows to an existing item on the plan and raises
  ``estimated_amount`` by the sum of new link amounts so PCS totals can match.

Out of scope: tender creation; supplier/threshold policy.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Literal

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from kentender_procurement.services.requisition_planning_allocation import (
	PLANNING_AMOUNT_TOLERANCE,
	PRI_DOCTYPE,
)
from kentender_procurement.services.requisition_planning_derivation import (
	compute_requisition_planning_derivation,
)
from kentender_procurement.services.requisition_workflow_actions import WS_APPROVED

PP_DOCTYPE = "Procurement Plan"
PPI_DOCTYPE = "Procurement Plan Item"
PR_DOCTYPE = "Purchase Requisition"
PCS_DOCTYPE = "Plan Consolidation Source"
RPL_DOCTYPE = "Requisition Planning Link"

ConsolidationMode = Literal["separate", "consolidated"]


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _plan_header(plan_name: str) -> frappe._dict | None:
	pn = _norm(plan_name)
	if not pn or not frappe.db.exists(PP_DOCTYPE, pn):
		return None
	return frappe.db.get_value(
		PP_DOCTYPE,
		pn,
		["name", "procuring_entity", "currency", "budget_control_period"],
		as_dict=True,
	)


def _ensure_pr_eligible(pr_name: str, *, plan_entity: str, plan_currency: str) -> None:
	row = frappe.db.get_value(
		PR_DOCTYPE,
		pr_name,
		["workflow_state", "procuring_entity", "currency", "name"],
		as_dict=True,
	)
	if not row:
		frappe.throw(
			_("Purchase Requisition {0} does not exist.").format(frappe.bold(pr_name)),
			frappe.ValidationError,
			title=_("Missing requisition"),
		)
	if _norm(row.get("workflow_state")) != WS_APPROVED:
		frappe.throw(
			_("Only requisitions in **Approved** workflow state can be consolidated into a plan."),
			frappe.ValidationError,
			title=_("Not approved"),
		)
	if _norm(row.get("procuring_entity")) != _norm(plan_entity):
		frappe.throw(
			_("Requisition {0} must belong to the same procuring entity as the procurement plan.").format(
				frappe.bold(pr_name)
			),
			frappe.ValidationError,
			title=_("Entity mismatch"),
		)
	if _norm(row.get("currency")) != _norm(plan_currency):
		frappe.throw(
			_("Requisition {0} currency must match the procurement plan currency.").format(
				frappe.bold(pr_name)
			),
			frappe.ValidationError,
			title=_("Currency mismatch"),
		)


def _resolve_effective_linked_amount(line: dict[str, Any], pr_name: str) -> float:
	pri = _norm(line.get("purchase_requisition_item"))
	qty = flt(line.get("linked_quantity") or 0)
	if pri and qty > PLANNING_AMOUNT_TOLERANCE:
		if not frappe.db.exists(PRI_DOCTYPE, pri):
			frappe.throw(
				_("Invalid Purchase Requisition Item."),
				frappe.ValidationError,
				title=_("Invalid line"),
			)
		parent = _norm(frappe.db.get_value(PRI_DOCTYPE, pri, "parent"))
		if parent != _norm(pr_name):
			frappe.throw(
				_("Purchase Requisition Item does not belong to {0}.").format(
					frappe.bold(pr_name)
				),
				frappe.ValidationError,
				title=_("Line mismatch"),
			)
		unit = flt(frappe.db.get_value(PRI_DOCTYPE, pri, "estimated_unit_cost"))
		return qty * unit
	if line.get("linked_amount") is not None:
		return flt(line.get("linked_amount"))
	deriv = compute_requisition_planning_derivation(pr_name)
	return flt(deriv.get("unplanned_amount"))


def _normalize_input_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
	if not lines:
		frappe.throw(
			_("At least one requisition line is required."),
			frappe.ValidationError,
			title=_("Missing lines"),
		)
	out: list[dict[str, Any]] = []
	for raw in lines:
		pr = _norm(raw.get("purchase_requisition"))
		if not pr:
			frappe.throw(
				_("Each line must set purchase_requisition."),
				frappe.ValidationError,
				title=_("Invalid line"),
			)
		amt = _resolve_effective_linked_amount(raw, pr)
		if amt <= PLANNING_AMOUNT_TOLERANCE:
			frappe.throw(
				_("Linked amount for {0} must be greater than zero (check unplanned balance).").format(
					frappe.bold(pr)
				),
				frappe.ValidationError,
				title=_("Invalid amount"),
			)
		out.append(
			{
				"purchase_requisition": pr,
				"linked_amount": amt,
				"purchase_requisition_item": _norm(raw.get("purchase_requisition_item")) or None,
				"linked_quantity": flt(raw.get("linked_quantity"))
				if raw.get("linked_quantity") is not None
				else None,
			}
		)
	return out


def _validate_batch_within_unplanned(normalized: list[dict[str, Any]]) -> None:
	totals: dict[str, float] = defaultdict(float)
	for row in normalized:
		totals[row["purchase_requisition"]] += flt(row["linked_amount"])
	for pr_name, add_sum in totals.items():
		deriv = compute_requisition_planning_derivation(pr_name)
		unplanned = flt(deriv.get("unplanned_amount"))
		if add_sum > unplanned + PLANNING_AMOUNT_TOLERANCE:
			frappe.throw(
				_("Total planned amount ({0}) for requisition {1} exceeds remaining unplanned ({2}).").format(
					add_sum, frappe.bold(pr_name), unplanned
				),
				frappe.ValidationError,
				title=_("Over-planning not allowed"),
			)


def _new_ppi_name() -> str:
	return f"PPI-CNS-{frappe.generate_hash(length=14)}"


def _insert_pcs_rpl(
	*,
	procurement_plan: str,
	procurement_plan_item: str,
	pr_name: str,
	linked_amount: float,
	purchase_requisition_item: str | None,
	linked_quantity: float | None,
	linked_on,
) -> tuple[str, str]:
	pcs = frappe.get_doc(
		{
			"doctype": PCS_DOCTYPE,
			"procurement_plan_item": procurement_plan_item,
			"purchase_requisition": pr_name,
			"source_type": "Requisition",
			"linked_amount": linked_amount,
			"linked_on": linked_on,
			"status": "Active",
		}
	)
	pcs.insert(ignore_permissions=True)

	rpl_payload: dict[str, Any] = {
		"doctype": RPL_DOCTYPE,
		"purchase_requisition": pr_name,
		"linked_amount": linked_amount,
		"linked_on": linked_on,
		"status": "Active",
		"procurement_plan": procurement_plan,
		"procurement_plan_item": procurement_plan_item,
	}
	if purchase_requisition_item:
		rpl_payload["purchase_requisition_item"] = purchase_requisition_item
	if linked_quantity is not None and flt(linked_quantity) > PLANNING_AMOUNT_TOLERANCE:
		rpl_payload["linked_quantity"] = linked_quantity
	rpl = frappe.get_doc(rpl_payload)
	rpl.insert(ignore_permissions=True)
	return pcs.name, rpl.name


def consolidate_requisitions_into_plan(
	procurement_plan: str,
	lines: list[dict[str, Any]],
	*,
	mode: ConsolidationMode = "separate",
	target_procurement_plan_item: str | None = None,
	dry_run: bool = False,
) -> dict[str, Any]:
	"""Consolidate **Approved** requisitions into *procurement_plan*.

	:param procurement_plan: Target **Procurement Plan** name.
	:param lines: Dicts with ``purchase_requisition``; optional ``linked_amount``,
	  ``purchase_requisition_item``, ``linked_quantity`` (RPL semantics).
	:param mode: ``separate`` (one new PPI per line) or ``consolidated`` (one shared new PPI).
	:param target_procurement_plan_item: Existing PPI on this plan; all lines attach here;
	  ``estimated_amount`` is increased by the sum of linked amounts. ``mode`` only affects
	  behaviour when this is **not** set (whether to create one or many new PPI rows).
	:param dry_run: If True, validate only and return a preview; no inserts.

	Returns keys such as ``plan_items_created``, ``consolidation_source_names``,
	``planning_link_names``, ``dry_run_preview`` (when applicable).
	"""
	plan = _plan_header(procurement_plan)
	if not plan:
		frappe.throw(
			_("Procurement Plan {0} does not exist.").format(frappe.bold(procurement_plan)),
			frappe.ValidationError,
			title=_("Invalid plan"),
		)

	plan_entity = _norm(plan.get("procuring_entity"))
	plan_currency = _norm(plan.get("currency"))
	pn = _norm(plan.get("name"))

	normalized = _normalize_input_lines(lines)
	for row in normalized:
		_ensure_pr_eligible(row["purchase_requisition"], plan_entity=plan_entity, plan_currency=plan_currency)
	_validate_batch_within_unplanned(normalized)

	target_ppi = _norm(target_procurement_plan_item)
	if target_ppi:
		if not frappe.db.exists(PPI_DOCTYPE, target_ppi):
			frappe.throw(
				_("Procurement Plan Item {0} does not exist.").format(frappe.bold(target_ppi)),
				frappe.ValidationError,
				title=_("Invalid plan item"),
			)
		item_plan = _norm(frappe.db.get_value(PPI_DOCTYPE, target_ppi, "procurement_plan"))
		if item_plan != pn:
			frappe.throw(
				_("Target plan item must belong to procurement plan {0}.").format(
					frappe.bold(procurement_plan)
				),
				frappe.ValidationError,
				title=_("Plan mismatch"),
			)

	t_delta = sum(flt(r["linked_amount"]) for r in normalized)
	linked_on = now_datetime()

	if dry_run:
		preview: list[dict[str, Any]] = []
		if target_ppi:
			preview.append(
				{
					"action": "increment_estimated_amount",
					"procurement_plan_item": target_ppi,
					"delta": t_delta,
				}
			)
		elif mode == "consolidated":
			preview.append(
				{
					"action": "create_procurement_plan_item",
					"origin_type": "Consolidated",
					"estimated_amount": t_delta,
					"lines": [r["purchase_requisition"] for r in normalized],
				}
			)
		else:
			for row in normalized:
				preview.append(
					{
						"action": "create_procurement_plan_item",
						"origin_type": "Requisition Derived",
						"estimated_amount": row["linked_amount"],
						"purchase_requisition": row["purchase_requisition"],
					}
				)
		for row in normalized:
			preview.append(
				{
					"action": "create_pcs_and_rpl",
					"purchase_requisition": row["purchase_requisition"],
					"linked_amount": row["linked_amount"],
				}
			)
		return {
			"dry_run": True,
			"dry_run_preview": preview,
			"procurement_plan": pn,
			"target_procurement_plan_item": target_ppi or None,
		}

	result: dict[str, Any] = {
		"dry_run": False,
		"procurement_plan": pn,
		"plan_items_created": [],
		"consolidation_source_names": [],
		"planning_link_names": [],
		"target_procurement_plan_item": target_ppi or None,
	}

	save_point = f"cns_{frappe.generate_hash(length=10)}"
	frappe.db.savepoint(save_point)
	try:
		if target_ppi:
			cur_est = flt(frappe.db.get_value(PPI_DOCTYPE, target_ppi, "estimated_amount"))
			frappe.db.set_value(
				PPI_DOCTYPE,
				target_ppi,
				{"estimated_amount": cur_est + t_delta},
				update_modified=True,
			)
			ppi_name = target_ppi
		elif mode == "consolidated":
			titles = [
				_norm(frappe.db.get_value(PR_DOCTYPE, row["purchase_requisition"], "title"))
				or row["purchase_requisition"]
				for row in normalized
			]
			title = f"Consolidated: {', '.join(titles)}"
			if len(title) > 140:
				title = title[:137] + "..."
			ppi = frappe.get_doc(
				{
					"doctype": PPI_DOCTYPE,
					"name": _new_ppi_name(),
					"procurement_plan": pn,
					"title": title,
					"procuring_entity": plan_entity,
					"currency": plan_currency,
					"status": "Draft",
					"origin_type": "Consolidated",
					"estimated_amount": t_delta,
					"priority_level": "Medium",
					"source_summary": ", ".join(r["purchase_requisition"] for r in normalized),
				}
			)
			ppi.insert(ignore_permissions=True)
			ppi_name = ppi.name
			result["plan_items_created"].append(ppi_name)
		else:
			ppi_name = None

		for row in normalized:
			if mode == "separate" and not target_ppi:
				pr_title = _norm(
					frappe.db.get_value(PR_DOCTYPE, row["purchase_requisition"], "title")
				) or row["purchase_requisition"]
				one_amt = flt(row["linked_amount"])
				ppi = frappe.get_doc(
					{
						"doctype": PPI_DOCTYPE,
						"name": _new_ppi_name(),
						"procurement_plan": pn,
						"title": pr_title,
						"procuring_entity": plan_entity,
						"currency": plan_currency,
						"status": "Draft",
						"origin_type": "Requisition Derived",
						"estimated_amount": one_amt,
						"priority_level": "Medium",
						"source_summary": row["purchase_requisition"],
					}
				)
				ppi.insert(ignore_permissions=True)
				this_ppi = ppi.name
				result["plan_items_created"].append(this_ppi)
			else:
				this_ppi = ppi_name
				assert this_ppi

			pcs_name, rpl_name = _insert_pcs_rpl(
				procurement_plan=pn,
				procurement_plan_item=this_ppi,
				pr_name=row["purchase_requisition"],
				linked_amount=flt(row["linked_amount"]),
				purchase_requisition_item=row.get("purchase_requisition_item"),
				linked_quantity=row.get("linked_quantity"),
				linked_on=linked_on,
			)
			result["consolidation_source_names"].append(pcs_name)
			result["planning_link_names"].append(rpl_name)

		frappe.db.release_savepoint(save_point)
	except Exception:
		frappe.db.rollback(save_point=save_point)
		raise

	return result
