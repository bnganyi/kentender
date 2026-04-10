# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-012: read-side queues and script report rows for Kentender Stores."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

SI = "Store Issue"
SM = "Stock Movement"
GRN = "Goods Receipt Note"


def get_pending_store_issues(*, limit: int = 500) -> list[dict[str, Any]]:
	"""**Store Issue** documents not yet issued (Draft / Submitted)."""
	return frappe.get_all(
		SI,
		filters={"status": ["in", ["Draft", "Submitted"]]},
		fields=[
			"name",
			"business_id",
			"store",
			"issue_datetime",
			"issued_to_user",
			"status",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_open_stock_movements(*, limit: int = 500) -> list[dict[str, Any]]:
	"""**Stock Movement** documents not completed (Draft / In Progress)."""
	return frappe.get_all(
		SM,
		filters={"status": ["in", ["Draft", "In Progress"]]},
		fields=[
			"name",
			"business_id",
			"from_store",
			"to_store",
			"movement_datetime",
			"status",
			"initiated_by_user",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_draft_goods_receipt_notes(*, limit: int = 500) -> list[dict[str, Any]]:
	"""**Goods Receipt Note** in Draft (intake queue)."""
	return frappe.get_all(
		GRN,
		filters={"status": "Draft"},
		fields=[
			"name",
			"business_id",
			"contract",
			"store",
			"receipt_datetime",
			"supplier",
			"status",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


# --- Script report columns (Frappe list-of-strings format) ---


def pending_store_issues_columns() -> list[str]:
	return [
		_("Store Issue") + ":Link/Store Issue:160",
		_("Business ID") + ":Data:140",
		_("Store") + ":Link/Store:140",
		_("Issue Datetime") + ":Datetime:150",
		_("Issued To") + ":Link/User:140",
		_("Status") + ":Data:100",
		_("Modified") + ":Datetime:150",
	]


def pending_store_issues_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("store"),
		r.get("issue_datetime"),
		r.get("issued_to_user"),
		r.get("status"),
		r.get("modified"),
	]


def open_stock_movements_columns() -> list[str]:
	return [
		_("Stock Movement") + ":Link/Stock Movement:160",
		_("Business ID") + ":Data:140",
		_("From Store") + ":Link/Store:140",
		_("To Store") + ":Link/Store:140",
		_("Movement Datetime") + ":Datetime:150",
		_("Status") + ":Data:120",
		_("Initiated By") + ":Link/User:140",
		_("Modified") + ":Datetime:150",
	]


def open_stock_movements_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("from_store"),
		r.get("to_store"),
		r.get("movement_datetime"),
		r.get("status"),
		r.get("initiated_by_user"),
		r.get("modified"),
	]


def draft_grn_columns() -> list[str]:
	return [
		_("Goods Receipt Note") + ":Link/Goods Receipt Note:180",
		_("Business ID") + ":Data:140",
		_("Contract") + ":Link/Procurement Contract:160",
		_("Store") + ":Link/Store:140",
		_("Receipt Datetime") + ":Datetime:150",
		_("Supplier") + ":Data:140",
		_("Modified") + ":Datetime:150",
	]


def draft_grn_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("contract"),
		r.get("store"),
		r.get("receipt_datetime"),
		r.get("supplier"),
		r.get("modified"),
	]
