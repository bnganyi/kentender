# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.services.requisition_workflow_actions import RAR_DOCTYPE

from kentender.uat.minimal_golden.bid_receipts import delete_minimal_golden_bid_receipt
from kentender.uat.minimal_golden.bid_submissions import delete_minimal_golden_bid_submissions
from kentender.uat.minimal_golden.dataset import load_minimal_golden_dataset
from kentender.uat.minimal_golden.post_tender_scenario import delete_post_tender_scenario

PR = "Purchase Requisition"
BLE = "Budget Ledger Entry"
LINK = "Requisition Planning Link"
PP = "Procurement Plan"
PPI = "Procurement Plan Item"
TENDER = "Tender"


def reset_minimal_golden_data(ds: dict[str, Any] | None = None) -> None:
	"""Remove Minimal Golden business rows (dependency-safe order). Does not call MVP reset."""
	if ds is None:
		ds = load_minimal_golden_dataset()

	t_spec = ds.get("tender") or {}
	t_name = (t_spec.get("name") or "").strip()
	delete_post_tender_scenario(ds)
	# Bid Receipt links to Bid Submission — remove before bids/tender.
	delete_minimal_golden_bid_receipt(ds)
	# Bids link to Tender — remove before deleting the tender.
	delete_minimal_golden_bid_submissions(ds)
	if t_name and frappe.db.exists(TENDER, t_name):
		frappe.delete_doc(TENDER, t_name, force=True, ignore_permissions=True)

	pr_bid = (ds.get("purchase_requisition") or {}).get("name")
	if pr_bid and frappe.db.exists(PR, pr_bid):
		pr_name = frappe.db.get_value(PR, pr_bid, "name")
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
		frappe.db.delete(LINK, {"purchase_requisition": pr_bid})
		frappe.db.delete(BLE, {"related_requisition": pr_bid})
		frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": pr_bid})
		frappe.delete_doc(PR, pr_bid, force=True, ignore_permissions=True)

	pp_sec = ds.get("procurement_planning") or {}
	ppi_bid = (pp_sec.get("plan_item") or {}).get("name")
	pp_bid = (pp_sec.get("plan") or {}).get("name")
	if ppi_bid and frappe.db.exists(PPI, ppi_bid):
		frappe.delete_doc(PPI, ppi_bid, force=True, ignore_permissions=True)
	if pp_bid and frappe.db.exists(PP, pp_bid):
		frappe.delete_doc(PP, pp_bid, force=True, ignore_permissions=True)

	bud = ds.get("budget") or {}
	line_id = ((bud.get("lines") or {}).get("main") or {}).get("name")
	if line_id and frappe.db.exists("Budget Line", line_id):
		frappe.db.delete(BLE, {"budget_line": line_id})
		frappe.delete_doc("Budget Line", line_id, force=True, ignore_permissions=True)

	bud_id = (bud.get("budget") or {}).get("name")
	if bud_id and frappe.db.exists("Budget", bud_id):
		frappe.delete_doc("Budget", bud_id, force=True, ignore_permissions=True)

	bcp_id = (bud.get("budget_control_period") or {}).get("name")
	if bcp_id and frappe.db.exists("Budget Control Period", bcp_id):
		frappe.delete_doc("Budget Control Period", bcp_id, force=True, ignore_permissions=True)

	st = ds.get("strategy") or {}
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

	ent = (ds.get("entity") or {}).get("entity_code")
	for dep in ds.get("departments") or []:
		dcode = dep.get("department_code")
		if dcode and ent:
			dept_name = f"{dcode}-{ent}"
			if frappe.db.exists("Procuring Department", dept_name):
				frappe.delete_doc("Procuring Department", dept_name, force=True, ignore_permissions=True)

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
