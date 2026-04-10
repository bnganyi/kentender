# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def _upsert_business_doc(doctype: str, business_id: str, fields: dict[str, Any]) -> str:
	if frappe.db.exists(doctype, business_id):
		doc = frappe.get_doc(doctype, business_id)
		for k, v in fields.items():
			doc.set(k, v)
		doc.save(ignore_permissions=True)
		return doc.name
	row = dict(fields)
	row["doctype"] = doctype
	row["name"] = business_id
	frappe.get_doc(row).insert(ignore_permissions=True)
	return business_id


def strategy_handles_for_budget_line(ds: dict[str, Any]) -> dict[str, Any]:
	"""Map canonical ``strategy`` JSON to the ``strategy`` dict expected by :func:`load_budget`."""
	st = ds.get("strategy") or {}

	def _bid(json_key: str) -> str:
		b = (st.get(json_key) or {}).get("name")
		if not b:
			frappe.throw(
				_("Minimal Golden dataset is missing strategy.{0}.name").format(json_key),
				frappe.ValidationError,
			)
		return b

	return {
		"entity_strategic_plan": _bid("entity_strategic_plan"),
		"strategic_program": _bid("program"),
		"strategic_sub_program": _bid("sub_program"),
		"output_indicator": _bid("output_indicator"),
		"performance_target": _bid("performance_target"),
	}


def assert_strategy_chain_seeded(ds: dict[str, Any]) -> dict[str, Any]:
	"""Return strategy handles after verifying GOLD strategy docs exist (step 2)."""
	handles = strategy_handles_for_budget_line(ds)
	checks = (
		("Entity Strategic Plan", handles["entity_strategic_plan"]),
		("Strategic Program", handles["strategic_program"]),
		("Strategic Sub Program", handles["strategic_sub_program"]),
		("Output Indicator", handles["output_indicator"]),
		("Performance Target", handles["performance_target"]),
	)
	for doctype, name in checks:
		if not frappe.db.exists(doctype, name):
			frappe.throw(
				_("{0} {1} not found. Run step 2: kentender.uat.minimal_golden.commands.seed_minimal_golden_strategy_console.").format(
					doctype,
					frappe.bold(name),
				),
				frappe.ValidationError,
			)
	return handles


def load_budget(
	ds: dict[str, Any],
	*,
	procuring_entity: str,
	strategy: dict[str, Any],
	departments: list[str],
	funding_source_code: str,
) -> dict[str, Any]:
	"""Budget control period, budget, and single main budget line (GOLD-SEED-004)."""
	bd = ds.get("budget") or {}
	fy = ds.get("fiscal_year") or "2026-2027"
	cur = (ds.get("currency_code") or "KES").strip()

	bcp_spec = bd.get("budget_control_period") or {}
	bcp_id = bcp_spec.get("name")
	_upsert_business_doc(
		"Budget Control Period",
		bcp_id,
		{
			"procuring_entity": procuring_entity,
			"fiscal_year": fy,
			"period_label": bcp_spec.get("period_label") or bcp_spec.get("fiscal_year_label") or "FY",
			"start_date": "2026-07-01",
			"end_date": "2027-06-30",
			"status": bcp_spec.get("status") or "Open",
			"budget_source_type": "Internal",
		},
	)

	bud_spec = bd.get("budget") or {}
	bud_id = bud_spec.get("name")
	lines_spec = bd.get("lines") or {}
	main_spec = lines_spec.get("main") or {}
	main_allocated = float(main_spec.get("allocated_amount") or 0)
	_upsert_business_doc(
		"Budget",
		bud_id,
		{
			"budget_title": bud_spec.get("budget_title") or "Budget",
			"procuring_entity": procuring_entity,
			"budget_control_period": bcp_id,
			"version_no": 1,
			"currency": cur,
			"status": "Active",
			"is_current_active_version": 1,
			"workflow_state": "Approved",
			"approval_status": "Approved",
			"total_allocated_amount": main_allocated,
		},
	)
	dept_primary = departments[0] if departments else None
	bid = main_spec.get("name")
	fs_name = funding_source_code
	_upsert_business_doc(
		"Budget Line",
		bid,
		{
			"budget": bud_id,
			"procuring_entity": procuring_entity,
			"budget_control_period": bcp_id,
			"fiscal_year": fy,
			"currency": cur,
			"status": "Active",
			"department": dept_primary,
			"funding_source": fs_name,
			"entity_strategic_plan": strategy.get("entity_strategic_plan"),
			"program": strategy.get("strategic_program"),
			"sub_program": strategy.get("strategic_sub_program"),
			"output_indicator": strategy.get("output_indicator"),
			"performance_target": strategy.get("performance_target"),
			"procurement_category": (ds.get("procurement_category") or {}).get("category_name", ""),
			"budget_line_type": main_spec.get("budget_line_type") or "Operating",
			"allocated_amount": main_allocated,
		},
	)

	return {
		"budget_control_period": bcp_id,
		"budget": bud_id,
		"budget_line_main": bid,
	}


def assert_budget_seeded_for_pr(ds: dict[str, Any]) -> dict[str, Any]:
	"""Return budget handles after verifying BCP, Budget, and main Budget Line exist (step 3)."""
	bd = ds.get("budget") or {}
	bcp_id = (bd.get("budget_control_period") or {}).get("name")
	bud_id = (bd.get("budget") or {}).get("name")
	main_spec = (bd.get("lines") or {}).get("main") or {}
	bl_id = main_spec.get("name")
	if not bcp_id or not bud_id or not bl_id:
		frappe.throw(
			_("Minimal Golden dataset is missing budget name(s) for control period, budget, or main line."),
			frappe.ValidationError,
		)
	for doctype, name in (
		("Budget Control Period", bcp_id),
		("Budget", bud_id),
		("Budget Line", bl_id),
	):
		if not frappe.db.exists(doctype, name):
			frappe.throw(
				_("{0} {1} not found. Run step 3: kentender.uat.minimal_golden.commands.seed_minimal_golden_budget_console.").format(
					doctype,
					frappe.bold(name),
				),
				frappe.ValidationError,
			)
	return {
		"budget_control_period": bcp_id,
		"budget": bud_id,
		"budget_line_main": bl_id,
	}
