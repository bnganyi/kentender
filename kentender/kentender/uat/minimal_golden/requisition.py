# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

from kentender.uat.minimal_golden.workflow_policy import (
	ensure_minimal_golden_pr_workflow_policy,
)
from kentender_procurement.services.requisition_workflow_actions import (
	RAR_DOCTYPE,
	approve_requisition_hod,
	approve_requisition_finance,
	submit_requisition,
)

PR = "Purchase Requisition"
BLE = "Budget Ledger Entry"
LINK = "Requisition Planning Link"


def _emails_by_key(ds: dict[str, Any]) -> dict[str, str]:
	out = {}
	for row in (ds.get("users") or {}).get("internal") or []:
		if row.get("key") and row.get("email"):
			out[row["key"]] = row["email"]
	return out


def _delete_pr_cascade(business_id: str) -> None:
	if not frappe.db.exists(PR, business_id):
		return
	frappe.db.delete(LINK, {"purchase_requisition": business_id})
	frappe.db.delete(BLE, {"related_requisition": business_id})
	frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": business_id})
	frappe.delete_doc(PR, business_id, force=True, ignore_permissions=True)


def load_purchase_requisition(
	ds: dict[str, Any],
	*,
	procuring_entity: str,
	requesting_department: str | None,
	strategy: dict[str, Any],
	budget: dict[str, Any],
	funding_source: str,
) -> dict[str, Any]:
	"""SP1: single approved PR with budget reservation (GOLD-SEED-006)."""
	spec = ds.get("purchase_requisition") or {}
	bid = spec.get("name")
	item = spec.get("item") or {}
	em = _emails_by_key(ds)
	req_u = em.get("requisitioner")
	hod_u = em.get("hod")
	fin_u = em.get("finance")
	budget_line_id = budget.get("budget_line_main")

	_delete_pr_cascade(bid)
	row = {
		"doctype": PR,
		"name": bid,
		"title": spec.get("title") or "Golden requisition",
		"requisition_type": "Goods",
		"status": "Draft",
		"workflow_state": "Draft",
		"approval_status": "Draft",
		"procuring_entity": procuring_entity,
		"requesting_department": requesting_department,
		"fiscal_year": ds.get("fiscal_year") or "2026-2027",
		"currency": (ds.get("currency_code") or "KES").strip(),
		"request_date": "2026-04-01",
		"priority_level": spec.get("priority_level") or "High",
		"budget_reservation_status": "None",
		"planning_status": "Unplanned",
		"entity_strategic_plan": strategy.get("entity_strategic_plan"),
		"program": strategy.get("strategic_program"),
		"sub_program": strategy.get("strategic_sub_program"),
		"output_indicator": strategy.get("output_indicator"),
		"performance_target": strategy.get("performance_target"),
		"national_objective": strategy.get("national_objective"),
		"budget_control_period": budget.get("budget_control_period"),
		"budget": budget.get("budget"),
		"budget_line": budget_line_id,
		"funding_source": funding_source,
		"items": [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": item.get("description") or "Item",
				"quantity": float(item.get("quantity") or 1),
				"estimated_unit_cost": float(item.get("unit_cost") or 1),
			}
		],
	}
	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	doc.requested_by_user = req_u
	doc.finance_reviewer_user = fin_u
	doc.hod_user = hod_u
	doc.save(ignore_permissions=True)
	ensure_minimal_golden_pr_workflow_policy()
	submit_requisition(doc.name, user=req_u)
	approve_requisition_hod(
		doc.name,
		comments="Minimal Golden seed — HOD approved",
		user=hod_u,
	)
	approve_requisition_finance(
		doc.name,
		comments="Minimal Golden seed — Finance approved",
		user=fin_u,
	)
	doc.reload()

	frappe.db.commit()
	return {
		"name": doc.name,
		"planned_name": bid,
		"workflow_state": doc.workflow_state,
		"budget_reservation_status": doc.budget_reservation_status,
		"requested_amount": doc.requested_amount,
	}
