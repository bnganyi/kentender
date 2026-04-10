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
	approve_requisition_finance,
	approve_requisition_hod,
	return_requisition_for_revision,
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


def _upsert_pr(
	ds: dict[str, Any],
	*,
	procuring_entity: str,
	requesting_department: str | None,
	strategy: dict[str, Any],
	budget: dict[str, Any],
	funding_source: str,
	spec: dict[str, Any],
	budget_line_id: str,
) -> frappe.model.document.Document:
	bid = spec["name"]
	item = spec.get("item") or {}
	_delete_pr_cascade(bid)
	row = {
		"doctype": PR,
		"name": bid,
		"title": spec.get("title") or "MVP Requisition",
		"requisition_type": "Goods",
		"status": "Draft",
		"workflow_state": "Draft",
		"approval_status": "Draft",
		"procuring_entity": procuring_entity,
		"requesting_department": requesting_department,
		"fiscal_year": ds.get("fiscal_year") or "2026-2027",
		"currency": (ds.get("currency_code") or "USD").strip(),
		"request_date": "2026-04-01",
		"priority_level": "Medium",
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
	return doc


def load_sp1(
	ds: dict[str, Any],
	*,
	procuring_entity: str,
	requesting_department: str | None,
	strategy: dict[str, Any],
	budget: dict[str, Any],
	funding_source: str,
) -> dict[str, Any]:
	"""SP1: draft, returned (submit→return), approved (submit→final approve with budget line OK)."""
	ensure_minimal_golden_pr_workflow_policy()
	em = _emails_by_key(ds)
	req_u = em.get("requisitioner")
	hod_u = em.get("hod")
	fin_u = em.get("finance")
	pr_spec = ds.get("purchase_requisitions") or {}
	healthy_line = budget.get("budget_line_healthy")

	# Draft
	draft_spec = pr_spec.get("draft") or {}
	_draft_doc = _upsert_pr(
		ds,
		procuring_entity=procuring_entity,
		requesting_department=requesting_department,
		strategy=strategy,
		budget=budget,
		funding_source=funding_source,
		spec=draft_spec,
		budget_line_id=healthy_line,
	)

	# Returned path
	ret_spec = pr_spec.get("returned") or {}
	ret_doc = _upsert_pr(
		ds,
		procuring_entity=procuring_entity,
		requesting_department=requesting_department,
		strategy=strategy,
		budget=budget,
		funding_source=funding_source,
		spec=ret_spec,
		budget_line_id=healthy_line,
	)
	ret_doc.requested_by_user = req_u
	ret_doc.hod_user = hod_u
	ret_doc.save(ignore_permissions=True)
	submit_requisition(ret_doc.name, user=req_u)
	return_requisition_for_revision(
		ret_doc.name,
		workflow_step="HOD",
		decision_level="L1",
		comments="UAT MVP seed — return for revision",
		user=hod_u,
	)

	# Approved path
	app_spec = pr_spec.get("approved") or {}
	app_doc = _upsert_pr(
		ds,
		procuring_entity=procuring_entity,
		requesting_department=requesting_department,
		strategy=strategy,
		budget=budget,
		funding_source=funding_source,
		spec=app_spec,
		budget_line_id=healthy_line,
	)
	app_doc.requested_by_user = req_u
	app_doc.finance_reviewer_user = fin_u
	app_doc.hod_user = hod_u
	app_doc.save(ignore_permissions=True)
	submit_requisition(app_doc.name, user=req_u)
	approve_requisition_hod(
		app_doc.name,
		comments="UAT MVP seed — HOD approved",
		user=hod_u,
	)
	approve_requisition_finance(
		app_doc.name,
		comments="UAT MVP seed — Finance approved",
		user=fin_u,
	)
	app_doc.reload()

	frappe.db.commit()
	return {
		"draft_business_id": draft_spec.get("name"),
		"returned_business_id": ret_spec.get("name"),
		"approved_business_id": app_spec.get("name"),
		"approved_name": app_doc.name,
		"approved_workflow_state": app_doc.workflow_state,
		"approved_budget_reservation_status": app_doc.budget_reservation_status,
	}
