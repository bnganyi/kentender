# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

PP = "Procurement Plan"
PPI = "Procurement Plan Item"


def _delete_planning_cascade(plan_item_name: str | None, plan_name: str | None) -> None:
	if plan_item_name and frappe.db.exists(PPI, plan_item_name):
		frappe.delete_doc(PPI, plan_item_name, force=True, ignore_permissions=True)
	if plan_name and frappe.db.exists(PP, plan_name):
		frappe.delete_doc(PP, plan_name, force=True, ignore_permissions=True)


def load_procurement_planning(
	ds: dict[str, Any],
	*,
	procuring_entity: str,
	budget: dict[str, Any],
	strategy: dict[str, Any],
	funding_source: str,
	requesting_department: str | None = None,
) -> dict[str, Any]:
	"""Create canonical Procurement Plan + Plan Item (GOLD planning rows).

	Requires budget step (BCP) and strategy chain. Idempotent for fixed business IDs.
	"""
	spec = ds.get("procurement_planning") or {}
	if not spec:
		return {}
	pp_spec = spec.get("plan") or {}
	ppi_spec = spec.get("plan_item") or {}
	pp_name = pp_spec.get("name")
	ppi_name = ppi_spec.get("name")
	if not pp_name or not ppi_name:
		return {}

	fy = ds.get("fiscal_year") or "2026-2027"
	cur = (ds.get("currency_code") or "KES").strip()
	bcp = budget.get("budget_control_period")
	bud = budget.get("budget")
	bl = budget.get("budget_line_main")
	if not bcp or not bud or not bl:
		frappe.throw(
			"Minimal Golden procurement planning requires budget_control_period, budget, and budget_line_main.",
			frappe.ValidationError,
		)

	_delete_planning_cascade(ppi_name, pp_name)

	plan_doc = frappe.get_doc(
		{
			"doctype": PP,
			"name": pp_name,
			"plan_title": pp_spec.get("plan_title") or "Procurement plan",
			"workflow_state": pp_spec.get("workflow_state") or "Draft",
			"status": "Draft",
			"approval_status": "Draft",
			"procuring_entity": procuring_entity,
			"fiscal_year": fy,
			"budget_control_period": bcp,
			"plan_period_label": pp_spec.get("plan_period_label") or fy,
			"currency": cur,
			"version_no": int(pp_spec.get("version_no") or 1),
			"allow_manual_items": int(pp_spec.get("allow_manual_items") or 1),
		}
	)
	plan_doc.insert(ignore_permissions=True)

	item_doc = frappe.get_doc(
		{
			"doctype": PPI,
			"name": ppi_name,
			"procurement_plan": pp_name,
			"title": ppi_spec.get("title") or "Plan line",
			"status": ppi_spec.get("status") or "Draft",
			"origin_type": ppi_spec.get("origin_type") or "Manual",
			"manual_entry_justification": ppi_spec.get("manual_entry_justification")
			or "Minimal Golden seed — procurement plan line.",
			"procuring_entity": procuring_entity,
			"requesting_department": requesting_department,
			"currency": cur,
			"estimated_amount": float(ppi_spec.get("estimated_amount") or 0),
			"priority_level": ppi_spec.get("priority_level") or "High",
			"entity_strategic_plan": strategy.get("entity_strategic_plan"),
			"program": strategy.get("strategic_program"),
			"sub_program": strategy.get("strategic_sub_program"),
			"output_indicator": strategy.get("output_indicator"),
			"performance_target": strategy.get("performance_target"),
			"national_objective": strategy.get("national_objective"),
			"budget": bud,
			"budget_line": bl,
			"funding_source": funding_source,
		}
	)
	item_doc.insert(ignore_permissions=True)

	frappe.db.commit()
	return {"procurement_plan": pp_name, "procurement_plan_item": ppi_name}
