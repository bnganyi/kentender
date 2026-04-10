# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe


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


def load_base_bud(
	ds: dict[str, Any],
	*,
	procuring_entity: str,
	strategy: dict[str, Any],
	departments: list[str],
	funding_source_code: str,
) -> dict[str, Any]:
	bd = ds.get("budget") or {}
	fy = ds.get("fiscal_year") or "2026-2027"
	cur = (ds.get("currency_code") or "USD").strip()

	bcp_spec = bd.get("budget_control_period") or {}
	bcp_id = bcp_spec.get("name")
	_upsert_business_doc(
		"Budget Control Period",
		bcp_id,
		{
			"procuring_entity": procuring_entity,
			"fiscal_year": fy,
			"period_label": bcp_spec.get("period_label") or "FY",
			"start_date": "2026-07-01",
			"end_date": "2027-06-30",
			"status": bcp_spec.get("status") or "Open",
			"budget_source_type": "Internal",
		},
	)

	bud_spec = bd.get("budget") or {}
	bud_id = bud_spec.get("name")
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
		},
	)

	lines_spec = (bd.get("lines") or {})
	dept_primary = departments[0] if departments else None

	def upsert_line(key: str, spec: dict[str, Any]) -> str:
		bid = spec.get("name")
		fs_name = funding_source_code
		return _upsert_business_doc(
			"Budget Line",
			bid,
			{
				"budget": bud_id,
				"procuring_entity": procuring_entity,
				"budget_control_period": bcp_id,
				"fiscal_year": fy,
				"status": "Active",
				"department": dept_primary,
				"funding_source": fs_name,
				"entity_strategic_plan": strategy.get("entity_strategic_plan"),
				"program": strategy.get("strategic_program"),
				"sub_program": strategy.get("strategic_sub_program"),
				"output_indicator": strategy.get("output_indicator"),
				"performance_target": strategy.get("performance_target"),
				"procurement_category": (ds.get("procurement_category") or {}).get("category_name", ""),
				"budget_line_type": spec.get("budget_line_type") or "Operating",
				"allocated_amount": float(spec.get("allocated_amount") or 0),
			},
		)

	h_id = upsert_line("healthy", lines_spec.get("healthy") or {})
	c_id = upsert_line("constrained", lines_spec.get("constrained") or {})

	frappe.db.commit()
	return {
		"budget_control_period": bcp_id,
		"budget": bud_id,
		"budget_line_healthy": h_id,
		"budget_line_constrained": c_id,
	}
