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
		# Performance Target: Numeric measurement must not carry a percent value (even 0).
		if doctype == "Performance Target" and (fields.get("target_measurement_type") or "").strip() == "Numeric":
			doc.target_value_percent = None
		doc.save(ignore_permissions=True)
		return doc.name
	row = dict(fields)
	row["doctype"] = doctype
	row["name"] = business_id
	frappe.get_doc(row).insert(ignore_permissions=True)
	return business_id


def load_base_strat(ds: dict[str, Any], *, procuring_entity: str) -> dict[str, Any]:
	"""Minimum national + entity strategy chain for PR linkage."""
	st = ds.get("strategy") or {}
	ent = procuring_entity

	nf = st.get("national_framework") or {}
	b_nf = nf.get("name")
	_upsert_business_doc(
		"National Framework",
		b_nf,
		{
			"framework_code": nf.get("framework_code"),
			"framework_name": nf.get("framework_name"),
			"framework_type": nf.get("framework_type") or "National Development Plan",
			"version_label": nf.get("version_label") or "v1",
			"status": "Active",
			"is_locked_reference": 0,
			"start_date": "2026-01-01",
			"end_date": "2030-12-31",
		},
	)

	pl = st.get("national_pillar") or {}
	b_pl = pl.get("name")
	_upsert_business_doc(
		"National Pillar",
		b_pl,
		{
			"national_framework": b_nf,
			"pillar_code": pl.get("pillar_code") or "P1",
			"pillar_name": pl.get("pillar_name") or "Pillar",
			"status": "Active",
			"is_locked_reference": 0,
			"display_order": 0,
		},
	)

	ob = st.get("national_objective") or {}
	b_ob = ob.get("name")
	_upsert_business_doc(
		"National Objective",
		b_ob,
		{
			"national_pillar": b_pl,
			"objective_code": ob.get("objective_code") or "O1",
			"objective_name": ob.get("objective_name") or "Objective",
			"status": "Active",
			"is_locked_reference": 0,
			"display_order": 0,
		},
	)

	esp = st.get("entity_strategic_plan") or {}
	b_esp = esp.get("name")
	_upsert_business_doc(
		"Entity Strategic Plan",
		b_esp,
		{
			"plan_title": esp.get("plan_title"),
			"procuring_entity": ent,
			"plan_period_label": esp.get("plan_period_label") or "FY",
			"version_no": esp.get("version_no") or 1,
			"status": "Active",
			"is_current_active_version": 1,
			"start_date": "2026-01-01",
			"end_date": "2027-06-30",
			"primary_national_framework": b_nf,
			"approval_status": "Approved",
			"workflow_state": "Approved",
		},
	)

	pg = st.get("program") or {}
	b_pg = pg.get("name")
	_upsert_business_doc(
		"Strategic Program",
		b_pg,
		{
			"entity_strategic_plan": b_esp,
			"procuring_entity": ent,
			"program_code": pg.get("program_code") or "PG",
			"program_name": pg.get("program_name") or "Program",
			"national_objective": b_ob,
			"priority_level": "Medium",
			"status": "Active",
		},
	)

	sg = st.get("sub_program") or {}
	b_sg = sg.get("name")
	_upsert_business_doc(
		"Strategic Sub Program",
		b_sg,
		{
			"program": b_pg,
			"entity_strategic_plan": b_esp,
			"sub_program_code": sg.get("sub_program_code") or "SG",
			"sub_program_name": sg.get("sub_program_name") or "Sub",
			"status": "Active",
		},
	)

	ind = st.get("output_indicator") or {}
	b_ind = ind.get("name")
	_upsert_business_doc(
		"Output Indicator",
		b_ind,
		{
			"indicator_code": ind.get("indicator_code") or "IND",
			"indicator_name": ind.get("indicator_name") or "Indicator",
			"sub_program": b_sg,
			"unit_of_measure": "Nos",
			"indicator_type": "Quantitative",
			"baseline_date": "2026-01-15",
			"status": "Active",
		},
	)

	tg = st.get("performance_target") or {}
	b_tgt = tg.get("name")
	_upsert_business_doc(
		"Performance Target",
		b_tgt,
		{
			"target_title": tg.get("target_title"),
			"output_indicator": b_ind,
			"entity_strategic_plan": b_esp,
			"program": b_pg,
			"sub_program": b_sg,
			"target_period_type": tg.get("target_period_type") or "Annual",
			"period_label": tg.get("period_label") or "FY2026",
			"period_start_date": "2026-07-01",
			"period_end_date": "2027-06-30",
			"target_measurement_type": tg.get("target_measurement_type") or "Numeric",
			"target_value_numeric": tg.get("target_value_numeric") or 100,
			"target_value_percent": None,
			"target_value_text": None,
			"status": "Active",
		},
	)

	frappe.db.commit()
	return {
		"national_framework": b_nf,
		"entity_strategic_plan": b_esp,
		"strategic_program": b_pg,
		"strategic_sub_program": b_sg,
		"output_indicator": b_ind,
		"performance_target": b_tgt,
		"national_objective": b_ob,
	}
