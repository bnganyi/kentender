# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-019: create **KenTender Asset** rows from qualifying GRN lines (capital asset flag)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

GRN = "Goods Receipt Note"
AST = "KenTender Asset"
CAT = "KenTender Asset Category"
STORE = "Store"


def _resolve_grn(ref: str) -> str | None:
	ref = (ref or "").strip()
	if not ref:
		return None
	if frappe.db.exists(GRN, ref):
		return ref
	return frappe.db.get_value(GRN, {"business_id": ref}, "name")


def _store_label(store_name: str) -> str:
	row = frappe.db.get_value(STORE, store_name, ("store_name", "location"), as_dict=True)
	if not row:
		return store_name
	loc = (row.location or "").strip()
	name = (row.store_name or "").strip()
	if loc and name:
		return f"{name} — {loc}"
	if name:
		return name
	return store_name


def _line_unit_cost(row) -> float:
	q = flt(row.quantity)
	if flt(row.get("amount")) and q:
		return flt(row.amount) / q
	return flt(row.get("unit_rate"))


def _line_units(row) -> int:
	return max(0, int(flt(row.quantity)))


def create_asset_from_grn(
	grn_id: str,
	*,
	default_asset_category: str | None = None,
	current_location: str | None = None,
	assigned_to_user: str | None = None,
	asset_code_prefix: str | None = None,
) -> dict[str, Any]:
	"""Create **KenTender Asset** records for GRN lines marked **Capital asset**.

	:param grn_id: **Goods Receipt Note** ``name`` or ``business_id``.
	:param default_asset_category: Used when a capital line does not set **Asset Category** on the line.
	:param current_location: Defaults to the receiving **Store** name / location.
	:param assigned_to_user: Optional **User** for new assets.
	:param asset_code_prefix: Prefix for generated ``asset_code`` values (defaults to GRN ``business_id``).

	Requires GRN **status** **Received**. Lines without **Capital asset** are skipped (not all goods are assets).
	Quantity ``N`` on a capital line creates ``N`` discrete assets (bulk).
	"""
	name = _resolve_grn(grn_id)
	if not name:
		frappe.throw(_("Goods Receipt Note not found."), frappe.ValidationError)
	grn = frappe.get_doc(GRN, name)
	if grn.status != "Received":
		frappe.throw(_("Goods Receipt Note must be Received before creating assets."), frappe.ValidationError)

	if assigned_to_user and not frappe.db.exists("User", assigned_to_user):
		frappe.throw(_("Assigned To user not found."), frappe.ValidationError)

	loc = (current_location or "").strip() or _store_label(grn.store)
	prefix = (asset_code_prefix or grn.business_id or grn.name).strip()
	created: list[str] = []

	for row in grn.get("items") or []:
		if not row.get("capital_asset"):
			continue
		category = (row.get("asset_category") or "").strip() or (default_asset_category or "").strip()
		if not category:
			frappe.throw(
				_("Capital line {0}: set Asset Category on the line or pass default_asset_category.").format(
					row.item_code or row.idx
				),
				frappe.ValidationError,
			)
		if not frappe.db.exists(CAT, category):
			frappe.throw(_("KenTender Asset Category not found."), frappe.ValidationError)

		units = _line_units(row)
		if units <= 0:
			continue

		cost = _line_unit_cost(row)
		item_name = (row.get("item_name") or "").strip() or (row.get("item_code") or "Item")
		line_idx = cint(row.idx)
		for u in range(1, units + 1):
			code = f"{prefix}-L{line_idx}-U{u}"
			if len(code) > 140:
				code = code[:140]
			if frappe.db.exists(AST, {"asset_code": code}):
				frappe.throw(_("Asset Code already exists: {0}").format(code), frappe.ValidationError)
			asset_name = f"{item_name} ({u}/{units})" if units > 1 else item_name
			doc = frappe.get_doc(
				{
					"doctype": AST,
					"asset_code": code,
					"asset_name": asset_name,
					"asset_category": category,
					"source_contract": grn.contract,
					"source_grn": grn.name,
					"source_grn_line_idx": line_idx,
					"supplier": grn.supplier,
					"acquisition_date": getdate(grn.receipt_datetime),
					"acquisition_cost": cost,
					"currency": grn.currency,
					"current_location": loc,
					"assigned_to_user": assigned_to_user,
					"condition_status": "Good",
					"status": "Active",
				}
			)
			doc.insert(ignore_permissions=True)
			created.append(doc.name)

	return {"grn": grn.name, "assets": created, "count": len(created)}


@frappe.whitelist()
def create_asset_from_grn_api(
	grn_id: str | None = None,
	default_asset_category: str | None = None,
	current_location: str | None = None,
	assigned_to_user: str | None = None,
	asset_code_prefix: str | None = None,
):
	"""Whitelisted entry point for ``frappe.call``."""
	if not grn_id:
		frappe.throw(_("grn_id is required."), frappe.ValidationError)
	return create_asset_from_grn(
		grn_id,
		default_asset_category=default_asset_category,
		current_location=current_location,
		assigned_to_user=assigned_to_user,
		asset_code_prefix=asset_code_prefix,
	)
