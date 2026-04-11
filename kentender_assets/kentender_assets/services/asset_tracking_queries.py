# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-021: read-side lists and script report helpers for KenTender Assets."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

AST = "KenTender Asset"
AMR = "KenTender Asset Maintenance Record"
ADR = "KenTender Asset Disposal Record"


def get_assets_for_contract(contract_name: str, *, limit: int = 500) -> list[dict[str, Any]]:
	"""**KenTender Asset** rows with **Source Contract** = ``contract_name``."""
	return frappe.get_all(
		AST,
		filters={"source_contract": contract_name},
		fields=[
			"name",
			"asset_code",
			"asset_name",
			"status",
			"source_grn",
			"supplier",
			"acquisition_date",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_assets_for_grn(grn_name: str, *, limit: int = 500) -> list[dict[str, Any]]:
	"""Assets created from a **Goods Receipt Note** (``source_grn``)."""
	return frappe.get_all(
		AST,
		filters={"source_grn": grn_name},
		fields=[
			"name",
			"asset_code",
			"asset_name",
			"status",
			"source_grn_line_idx",
			"acquisition_cost",
			"currency",
			"modified",
		],
		order_by="source_grn_line_idx asc, asset_code asc",
		limit=limit,
	)


def get_open_maintenance_records(*, limit: int = 500) -> list[dict[str, Any]]:
	"""Maintenance rows not yet **Completed** or **Cancelled**."""
	return frappe.get_all(
		AMR,
		filters={"status": ["not in", ["Completed", "Cancelled"]]},
		fields=[
			"name",
			"business_id",
			"asset",
			"maintenance_type",
			"scheduled_date",
			"status",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_draft_disposal_records(*, limit: int = 500) -> list[dict[str, Any]]:
	"""**KenTender Asset Disposal Record** in **Draft**."""
	return frappe.get_all(
		ADR,
		filters={"status": "Draft"},
		fields=[
			"name",
			"business_id",
			"asset",
			"disposal_method",
			"disposal_datetime",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


# --- Script report column helpers ---


def open_maintenance_columns() -> list[str]:
	return [
		_("KenTender Asset Maintenance Record") + ":Link/KenTender Asset Maintenance Record:200",
		_("Business ID") + ":Data:140",
		_("Asset") + ":Link/KenTender Asset:160",
		_("Type") + ":Data:120",
		_("Scheduled Date") + ":Date:120",
		_("Status") + ":Data:100",
		_("Modified") + ":Datetime:150",
	]


def open_maintenance_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("asset"),
		r.get("maintenance_type"),
		r.get("scheduled_date"),
		r.get("status"),
		r.get("modified"),
	]


def draft_disposals_columns() -> list[str]:
	return [
		_("KenTender Asset Disposal Record") + ":Link/KenTender Asset Disposal Record:200",
		_("Business ID") + ":Data:140",
		_("Asset") + ":Link/KenTender Asset:160",
		_("Method") + ":Data:120",
		_("Disposal Datetime") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def draft_disposals_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("asset"),
		r.get("disposal_method"),
		r.get("disposal_datetime"),
		r.get("modified"),
	]
