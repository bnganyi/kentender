# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-020: guarded transitions for KenTender asset satellites and master status."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime, nowdate

AST = "KenTender Asset"
AMR = "KenTender Asset Maintenance Record"
ADR = "KenTender Asset Disposal Record"
ASG = "KenTender Asset Assignment"
ACL = "KenTender Asset Condition Log"


def complete_maintenance_record(
	maintenance_name: str,
	*,
	completed_date: str | None = None,
	performed_by_user: str | None = None,
	summary: str | None = None,
) -> dict[str, Any]:
	"""Set maintenance to **Completed** and return the asset to **Active** if it was **In Maintenance**."""
	doc = frappe.get_doc(AMR, maintenance_name)
	if doc.status in ("Completed", "Cancelled"):
		frappe.throw(_("Maintenance record is already closed."), frappe.ValidationError)
	doc.status = "Completed"
	doc.completed_date = completed_date or nowdate()
	if performed_by_user:
		if not frappe.db.exists("User", performed_by_user):
			frappe.throw(_("Performed By user not found."), frappe.ValidationError)
		doc.performed_by_user = performed_by_user
	if summary:
		doc.summary = summary
	doc.save(ignore_permissions=True)

	ast = frappe.get_doc(AST, doc.asset)
	if ast.status == "In Maintenance":
		ast.status = "Active"
		ast.save(ignore_permissions=True)

	return {"maintenance": doc.name, "asset": doc.asset, "asset_status": ast.status}


def complete_disposal_record(
	disposal_name: str,
	*,
	approved_by_user: str | None = None,
) -> dict[str, Any]:
	"""Move disposal from **Draft** to **Completed** and set the asset to **Disposed**."""
	doc = frappe.get_doc(ADR, disposal_name)
	if doc.status != "Draft":
		frappe.throw(_("Only Draft disposal records can be completed via this service."), frappe.ValidationError)
	doc.status = "Completed"
	if approved_by_user:
		if not frappe.db.exists("User", approved_by_user):
			frappe.throw(_("Approved By user not found."), frappe.ValidationError)
		doc.approved_by_user = approved_by_user
	doc.save(ignore_permissions=True)

	ast = frappe.get_doc(AST, doc.asset)
	ast.status = "Disposed"
	ast.save(ignore_permissions=True)

	return {"disposal": doc.name, "asset": doc.asset, "asset_status": ast.status}


def register_asset_assignment(
	asset_name: str,
	business_id: str,
	assigned_to_user: str,
	assignment_type: str = "Permanent",
	*,
	from_location: str | None = None,
	to_location: str | None = None,
) -> dict[str, Any]:
	"""Create an **Active** **KenTender Asset Assignment** and update the asset's **Assigned To**."""
	if not frappe.db.exists(AST, asset_name):
		frappe.throw(_("KenTender Asset not found."), frappe.ValidationError)
	if not frappe.db.exists("User", assigned_to_user):
		frappe.throw(_("Assigned user not found."), frappe.ValidationError)
	if frappe.db.exists(ASG, {"business_id": business_id}):
		frappe.throw(_("Assignment business_id already exists."), frappe.ValidationError)

	doc = frappe.get_doc(
		{
			"doctype": ASG,
			"business_id": business_id,
			"asset": asset_name,
			"assignment_datetime": now_datetime(),
			"assignment_type": assignment_type,
			"assigned_to_user": assigned_to_user,
			"from_location": from_location,
			"to_location": to_location,
			"status": "Active",
		}
	)
	doc.insert(ignore_permissions=True)

	ast = frappe.get_doc(AST, asset_name)
	ast.assigned_to_user = assigned_to_user
	ast.save(ignore_permissions=True)

	return {"assignment": doc.name, "asset": asset_name}


def log_asset_condition(
	asset_name: str,
	condition_status: str,
	assessed_by_user: str,
	*,
	remarks: str | None = None,
) -> dict[str, Any]:
	"""Append a **KenTender Asset Condition Log** entry."""
	if not frappe.db.exists(AST, asset_name):
		frappe.throw(_("KenTender Asset not found."), frappe.ValidationError)
	if not frappe.db.exists("User", assessed_by_user):
		frappe.throw(_("Assessed By user not found."), frappe.ValidationError)

	doc = frappe.get_doc(
		{
			"doctype": ACL,
			"asset": asset_name,
			"condition_datetime": now_datetime(),
			"condition_status": condition_status,
			"assessed_by_user": assessed_by_user,
			"remarks": remarks,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"condition_log": doc.name, "asset": asset_name}


@frappe.whitelist()
def complete_maintenance_record_api(
	maintenance_name: str | None = None,
	completed_date: str | None = None,
	performed_by_user: str | None = None,
	summary: str | None = None,
):
	if not maintenance_name:
		frappe.throw(_("maintenance_name is required."), frappe.ValidationError)
	return complete_maintenance_record(
		maintenance_name,
		completed_date=completed_date,
		performed_by_user=performed_by_user,
		summary=summary,
	)


@frappe.whitelist()
def complete_disposal_record_api(disposal_name: str | None = None, approved_by_user: str | None = None):
	if not disposal_name:
		frappe.throw(_("disposal_name is required."), frappe.ValidationError)
	return complete_disposal_record(disposal_name, approved_by_user=approved_by_user)


@frappe.whitelist()
def register_asset_assignment_api(
	asset_name: str | None = None,
	business_id: str | None = None,
	assigned_to_user: str | None = None,
	assignment_type: str | None = None,
	from_location: str | None = None,
	to_location: str | None = None,
):
	if not asset_name or not business_id or not assigned_to_user:
		frappe.throw(_("asset_name, business_id, and assigned_to_user are required."), frappe.ValidationError)
	return register_asset_assignment(
		asset_name,
		business_id,
		assigned_to_user,
		assignment_type or "Permanent",
		from_location=from_location,
		to_location=to_location,
	)


@frappe.whitelist()
def log_asset_condition_api(
	asset_name: str | None = None,
	condition_status: str | None = None,
	assessed_by_user: str | None = None,
	remarks: str | None = None,
):
	if not asset_name or not condition_status or not assessed_by_user:
		frappe.throw(_("asset_name, condition_status, and assessed_by_user are required."), frappe.ValidationError)
	return log_asset_condition(asset_name, condition_status, assessed_by_user, remarks=remarks)
