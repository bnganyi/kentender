# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

from kentender.uat.mvp.dataset import load_mvp_dataset

from kentender_procurement.services.requisition_workflow_actions import RAR_DOCTYPE

PR = "Purchase Requisition"
BLE = "Budget Ledger Entry"
LINK = "Requisition Planning Link"


def _pr_business_ids(ds: dict[str, Any]) -> list[str]:
	"""Canonical SP1 IDs from dataset plus any stray UAT-MVP-PR-* rows (e.g. tests)."""
	out = []
	for _k, spec in (ds.get("purchase_requisitions") or {}).items():
		bid = (spec or {}).get("name")
		if bid:
			out.append(bid)
	extra = (
		frappe.get_all(PR, filters={"name": ("like", "UAT-MVP-PR-%")}, pluck="name") or []
	)
	for e in extra:
		if e not in out:
			out.append(e)
	return out


def reset_mvp_seed_data(ds: dict[str, Any] | None = None) -> None:
	"""Remove MVP rows (UAT-MVP* business IDs) in safe dependency order."""
	if ds is None:
		ds = load_mvp_dataset()

	ent = (ds.get("entity") or {}).get("entity_code")
	pr_ids = _pr_business_ids(ds)

	for bid in pr_ids:
		if not frappe.db.exists(PR, bid):
			continue
		pr_name = frappe.db.get_value(PR, bid, "name")
		if pr_name:
			for inst in frappe.get_all(
				"KenTender Approval Route Instance",
				filters={"reference_doctype": PR, "reference_docname": pr_name},
				pluck="name",
			):
				try:
					frappe.delete_doc(
						"KenTender Approval Route Instance",
						inst,
						force=True,
						ignore_permissions=True,
					)
				except Exception:
					pass
		frappe.db.delete(LINK, {"purchase_requisition": bid})
		frappe.db.delete(BLE, {"related_requisition": bid})
		frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": bid})
		frappe.delete_doc(PR, bid, force=True, ignore_permissions=True)

	bud = ds.get("budget") or {}
	line_ids = [
		((bud.get("lines") or {}).get("healthy") or {}).get("name"),
		((bud.get("lines") or {}).get("constrained") or {}).get("name"),
	]
	for lid in line_ids:
		if lid and frappe.db.exists("Budget Line", lid):
			frappe.db.delete(BLE, {"budget_line": lid})

	for lid in line_ids:
		if lid and frappe.db.exists("Budget Line", lid):
			frappe.delete_doc("Budget Line", lid, force=True, ignore_permissions=True)

	bud_id = (bud.get("budget") or {}).get("name")
	if bud_id and frappe.db.exists("Budget", bud_id):
		frappe.delete_doc("Budget", bud_id, force=True, ignore_permissions=True)

	bcp_id = (bud.get("budget_control_period") or {}).get("name")
	if bcp_id and frappe.db.exists("Budget Control Period", bcp_id):
		frappe.delete_doc("Budget Control Period", bcp_id, force=True, ignore_permissions=True)

	st = ds.get("strategy") or {}
	# Dependents first (target → indicator → sub → program → plan → objective → pillar → framework)
	strat_delete_order = (
		("performance_target", "Performance Target"),
		("output_indicator", "Output Indicator"),
		("sub_program", "Strategic Sub Program"),
		("program", "Strategic Program"),
		("entity_strategic_plan", "Entity Strategic Plan"),
		("national_objective", "National Objective"),
		("national_pillar", "National Pillar"),
		("national_framework", "National Framework"),
	)
	for key, dt in strat_delete_order:
		spec = st.get(key) or {}
		bid = spec.get("name")
		if bid and frappe.db.exists(dt, bid):
			frappe.delete_doc(dt, bid, force=True, ignore_permissions=True)

	for dep in ds.get("departments") or []:
		dcode = dep.get("department_code")
		if dcode and ent:
			dept_name = f"{dcode}-{ent}"
			if frappe.db.exists("Procuring Department", dept_name):
				frappe.delete_doc("Procuring Department", dept_name, force=True, ignore_permissions=True)

	dtr = (ds.get("document_type_registry") or {}).get("document_type_code")
	if dtr and frappe.db.exists("Document Type Registry", dtr):
		frappe.delete_doc("Document Type Registry", dtr, force=True, ignore_permissions=True)

	pc = (ds.get("procurement_category") or {}).get("category_code")
	if pc and frappe.db.exists("Procurement Category", pc):
		frappe.delete_doc("Procurement Category", pc, force=True, ignore_permissions=True)

	pm = (ds.get("procurement_method") or {}).get("method_code")
	if pm and frappe.db.exists("Procurement Method", pm):
		frappe.delete_doc("Procurement Method", pm, force=True, ignore_permissions=True)

	fs = (ds.get("funding_source") or {}).get("funding_source_code")
	if fs and frappe.db.exists("Funding Source", fs):
		frappe.delete_doc("Funding Source", fs, force=True, ignore_permissions=True)

	if ent and frappe.db.exists("Procuring Entity", ent):
		frappe.delete_doc("Procuring Entity", ent, force=True, ignore_permissions=True)

	frappe.db.commit()
