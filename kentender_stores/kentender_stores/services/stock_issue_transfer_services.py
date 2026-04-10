# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-010: post Store Ledger for inter-store transfer and store issue."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

SLE = "Store Ledger Entry"
STORE = "Store"
SM = "Stock Movement"
SI = "Store Issue"


def _normalize_items(items: Any) -> list[dict[str, Any]]:
	if items is None:
		return []
	if isinstance(items, str):
		items = json.loads(items)
	if not isinstance(items, list):
		frappe.throw(_("items must be a list of line dicts."), frappe.ValidationError)
	return items


def _validate_lines(items_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
	rows: list[dict[str, Any]] = []
	for row in items_list:
		if not isinstance(row, dict):
			frappe.throw(_("Each item row must be an object."), frappe.ValidationError)
		code = (row.get("item_code") or "").strip()
		if not code:
			frappe.throw(_("Each line must have item_code."), frappe.ValidationError)
		qty = flt(row.get("quantity"))
		if qty <= 0:
			frappe.throw(_("Each line must have a positive quantity."), frappe.ValidationError)
		uom = (row.get("unit_of_measure") or "").strip() or "Nos"
		rows.append(
			{
				"item_code": code,
				"item_name": (row.get("item_name") or "").strip(),
				"quantity": qty,
				"unit_of_measure": uom,
				"remarks": (row.get("remarks") or "").strip(),
			}
		)
	return rows


def _rollback_sles_for_source(source_doctype: str, source_docname: str) -> None:
	for name in (
		frappe.get_all(SLE, filters={"source_doctype": source_doctype, "source_docname": source_docname}, pluck="name")
		or []
	):
		frappe.flags.allow_store_ledger_delete = True
		try:
			frappe.delete_doc(SLE, name, force=True, ignore_permissions=True)
		finally:
			frappe.flags.allow_store_ledger_delete = False


def _post_sle(
	*,
	store: str,
	item_code: str,
	entry_type: str,
	entry_direction: str,
	quantity: float,
	unit_of_measure: str,
	posting_datetime,
	source_doctype: str,
	source_docname: str,
	remarks: str,
) -> str:
	doc = frappe.get_doc(
		{
			"doctype": SLE,
			"store": store,
			"item_reference": item_code,
			"entry_type": entry_type,
			"entry_direction": entry_direction,
			"quantity": quantity,
			"unit_of_measure": unit_of_measure,
			"posting_datetime": posting_datetime,
			"source_doctype": source_doctype,
			"source_docname": source_docname,
			"remarks": remarks,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def transfer_stock_between_stores(
	from_store: str,
	to_store: str,
	items: list[dict[str, Any]] | str | None = None,
	*,
	movement_business_id: str | None = None,
	initiated_by_user: str | None = None,
	movement_datetime=None,
	remarks: str | None = None,
) -> dict[str, Any]:
	"""Create a **Stock Movement** and post **Transfer** ledger rows (out from source, in to destination).

	:param from_store: **Store** name (origin).
	:param to_store: **Store** name (destination).
	:param items: Lines: ``item_code``, ``quantity``; optional ``item_name``, ``unit_of_measure``, ``remarks``.
	"""
	items_list = _validate_lines(_normalize_items(items))
	if not items_list:
		frappe.throw(_("items must contain at least one line."), frappe.ValidationError)
	if not frappe.db.exists(STORE, from_store) or not frappe.db.exists(STORE, to_store):
		frappe.throw(_("From Store and To Store must exist."), frappe.ValidationError)
	if from_store == to_store:
		frappe.throw(_("From Store and To Store must be different."), frappe.ValidationError)

	user = initiated_by_user or frappe.session.user
	if not frappe.db.exists("User", user):
		frappe.throw(_("Initiated By user not found."), frappe.ValidationError)

	dt = movement_datetime or now_datetime()
	biz = (movement_business_id or "").strip() or frappe.generate_hash(length=16)
	if frappe.db.exists(SM, {"business_id": biz}):
		frappe.throw(_("Stock Movement Business ID already exists."), frappe.ValidationError)

	sm_rows = [
		{
			"item_code": r["item_code"],
			"item_name": r["item_name"],
			"quantity": r["quantity"],
			"unit_of_measure": r["unit_of_measure"],
			"remarks": r["remarks"],
		}
		for r in items_list
	]

	sm = frappe.get_doc(
		{
			"doctype": SM,
			"business_id": biz,
			"from_store": from_store,
			"to_store": to_store,
			"movement_datetime": dt,
			"status": "Draft",
			"initiated_by_user": user,
			"remarks": remarks,
			"items": sm_rows,
		}
	)
	sm.insert(ignore_permissions=True)

	ledger_names: list[str] = []
	try:
		for line in sm.items:
			qty = flt(line.quantity)
			uom = (line.unit_of_measure or "").strip() or "Nos"
			code = (line.item_code or "").strip()
			base_remarks = f"Transfer {sm.business_id} · {code}"
			ledger_names.append(
				_post_sle(
					store=from_store,
					item_code=code,
					entry_type="Transfer",
					entry_direction="Out",
					quantity=qty,
					unit_of_measure=uom,
					posting_datetime=dt,
					source_doctype=SM,
					source_docname=sm.name,
					remarks=base_remarks,
				)
			)
			ledger_names.append(
				_post_sle(
					store=to_store,
					item_code=code,
					entry_type="Transfer",
					entry_direction="In",
					quantity=qty,
					unit_of_measure=uom,
					posting_datetime=dt,
					source_doctype=SM,
					source_docname=sm.name,
					remarks=base_remarks,
				)
			)
	except Exception:
		_rollback_sles_for_source(SM, sm.name)
		frappe.delete_doc(SM, sm.name, force=True, ignore_permissions=True)
		raise

	frappe.db.set_value(SM, sm.name, "status", "Completed")

	return {
		"stock_movement": sm.name,
		"stock_movement_business_id": sm.business_id,
		"store_ledger_entries": ledger_names,
	}


def issue_stock_from_store(
	store: str,
	issued_to_user: str,
	items: list[dict[str, Any]] | str | None = None,
	*,
	issue_business_id: str | None = None,
	issue_datetime=None,
	purpose: str | None = None,
	remarks: str | None = None,
) -> dict[str, Any]:
	"""Create a **Store Issue** and post **Issue** (outbound) ledger lines."""
	items_list = _validate_lines(_normalize_items(items))
	if not items_list:
		frappe.throw(_("items must contain at least one line."), frappe.ValidationError)
	if not frappe.db.exists(STORE, store):
		frappe.throw(_("Store not found."), frappe.ValidationError)
	if not issued_to_user or not frappe.db.exists("User", issued_to_user):
		frappe.throw(_("Issued To user not found."), frappe.ValidationError)

	dt = issue_datetime or now_datetime()
	biz = (issue_business_id or "").strip() or frappe.generate_hash(length=16)
	if frappe.db.exists(SI, {"business_id": biz}):
		frappe.throw(_("Store Issue Business ID already exists."), frappe.ValidationError)

	si_rows = [
		{
			"item_code": r["item_code"],
			"item_name": r["item_name"],
			"quantity": r["quantity"],
			"unit_of_measure": r["unit_of_measure"],
			"remarks": r["remarks"],
		}
		for r in items_list
	]

	si = frappe.get_doc(
		{
			"doctype": SI,
			"business_id": biz,
			"store": store,
			"issue_datetime": dt,
			"issued_to_user": issued_to_user,
			"purpose": purpose,
			"status": "Draft",
			"remarks": remarks,
			"items": si_rows,
		}
	)
	si.insert(ignore_permissions=True)

	ledger_names: list[str] = []
	try:
		for line in si.items:
			qty = flt(line.quantity)
			uom = (line.unit_of_measure or "").strip() or "Nos"
			code = (line.item_code or "").strip()
			ledger_names.append(
				_post_sle(
					store=store,
					item_code=code,
					entry_type="Issue",
					entry_direction="Out",
					quantity=qty,
					unit_of_measure=uom,
					posting_datetime=dt,
					source_doctype=SI,
					source_docname=si.name,
					remarks=f"Issue {si.business_id} · {code}",
				)
			)
	except Exception:
		_rollback_sles_for_source(SI, si.name)
		frappe.delete_doc(SI, si.name, force=True, ignore_permissions=True)
		raise

	frappe.db.set_value(SI, si.name, "status", "Issued")

	return {
		"store_issue": si.name,
		"store_issue_business_id": si.business_id,
		"store_ledger_entries": ledger_names,
	}


@frappe.whitelist()
def transfer_stock_between_stores_api(
	from_store: str | None = None,
	to_store: str | None = None,
	items: str | list | None = None,
	movement_business_id: str | None = None,
	initiated_by_user: str | None = None,
	movement_datetime=None,
	remarks: str | None = None,
):
	if not from_store or not to_store:
		frappe.throw(_("from_store and to_store are required."), frappe.ValidationError)
	return transfer_stock_between_stores(
		from_store,
		to_store,
		items,
		movement_business_id=movement_business_id,
		initiated_by_user=initiated_by_user,
		movement_datetime=movement_datetime,
		remarks=remarks,
	)


@frappe.whitelist()
def issue_stock_from_store_api(
	store: str | None = None,
	issued_to_user: str | None = None,
	items: str | list | None = None,
	issue_business_id: str | None = None,
	issue_datetime=None,
	purpose: str | None = None,
	remarks: str | None = None,
):
	if not store or not issued_to_user:
		frappe.throw(_("store and issued_to_user are required."), frappe.ValidationError)
	return issue_stock_from_store(
		store,
		issued_to_user,
		items,
		issue_business_id=issue_business_id,
		issue_datetime=issue_datetime,
		purpose=purpose,
		remarks=remarks,
	)
