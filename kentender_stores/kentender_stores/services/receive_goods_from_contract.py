# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-009: create GRN + inbound Store Ledger from an approved Acceptance Record."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

PC = "Procurement Contract"
AR = "Acceptance Record"
GRN = "Goods Receipt Note"
SLE = "Store Ledger Entry"
STORE = "Store"


def _resolve_pc(ref: str) -> str | None:
	ref = (ref or "").strip()
	if not ref:
		return None
	if frappe.db.exists(PC, ref):
		return ref
	return frappe.db.get_value(PC, {"business_id": ref}, "name")


def _resolve_ar(ref: str) -> str | None:
	ref = (ref or "").strip()
	if not ref:
		return None
	if frappe.db.exists(AR, ref):
		return ref
	return frappe.db.get_value(AR, {"business_id": ref}, "name")


def _normalize_items(items: Any) -> list[dict[str, Any]]:
	if items is None:
		return []
	if isinstance(items, str):
		items = json.loads(items)
	if not isinstance(items, list):
		frappe.throw(_("items must be a list of GRN lines."), frappe.ValidationError)
	return items


def _rollback_grn_and_ledgers(grn_name: str) -> None:
	for name in (
		frappe.get_all(SLE, filters={"source_doctype": GRN, "source_docname": grn_name}, pluck="name") or []
	):
		frappe.flags.allow_store_ledger_delete = True
		try:
			frappe.delete_doc(SLE, name, force=True, ignore_permissions=True)
		finally:
			frappe.flags.allow_store_ledger_delete = False
	if frappe.db.exists(GRN, grn_name):
		frappe.delete_doc(GRN, grn_name, force=True, ignore_permissions=True)


def receive_goods_from_contract(
	contract_id: str,
	acceptance_record_id: str,
	store: str,
	items: list[dict[str, Any]] | str | None = None,
	*,
	grn_business_id: str | None = None,
	received_by_user: str | None = None,
	remarks: str | None = None,
) -> dict[str, Any]:
	"""Create a **Goods Receipt Note**, post **inbound Store Ledger** lines, and bump **contract completion**.

	:param contract_id: **Procurement Contract** ``name`` or ``business_id``.
	:param acceptance_record_id: **Acceptance Record** ``name`` or ``business_id``.
	:param store: **Store** ``name`` (receiving location).
	:param items: GRN line dicts: ``item_code``, ``quantity``; optional ``item_name``, ``unit_of_measure``, ``unit_rate``.
	:param grn_business_id: Optional unique GRN ``business_id`` (defaults to generated id).
	:param received_by_user: Defaults to current user.
	:param remarks: Optional GRN remarks.

	Requires Acceptance Record **status** ``Approved``, **acceptance_decision** ``Accepted``, not locked;
	contract must match the acceptance record; inspection/acceptance chain is not bypassed (GRN carries IR + AR links).
	"""
	items_list = _normalize_items(items)
	if not items_list:
		frappe.throw(_("items must contain at least one line."), frappe.ValidationError)
	if not frappe.db.exists(STORE, store):
		frappe.throw(_("Store not found."), frappe.ValidationError)

	pc_name = _resolve_pc(contract_id)
	if not pc_name:
		frappe.throw(_("Procurement Contract not found."), frappe.ValidationError)

	ar_name = _resolve_ar(acceptance_record_id)
	if not ar_name:
		frappe.throw(_("Acceptance Record not found."), frappe.ValidationError)

	ar = frappe.get_doc(AR, ar_name)
	if ar.contract != pc_name:
		frappe.throw(
			_("Acceptance Record does not belong to the given Procurement Contract."),
			frappe.ValidationError,
		)
	if ar.status != "Approved":
		frappe.throw(_("Acceptance Record must be Approved to receive goods."), frappe.ValidationError)
	if ar.acceptance_decision != "Accepted":
		frappe.throw(_("Acceptance decision must be Accepted to receive goods."), frappe.ValidationError)
	if cint(ar.is_locked):
		frappe.throw(_("Acceptance Record is locked."), frappe.ValidationError)
	if not ar.inspection_record:
		frappe.throw(_("Acceptance Record must reference an Inspection Record."), frappe.ValidationError)

	if frappe.get_all(
		GRN,
		filters={"acceptance_reference": ar_name, "status": ["!=", "Cancelled"]},
		limit=1,
	):
		frappe.throw(_("Goods already received for this Acceptance Record."), frappe.ValidationError)

	pc = frappe.get_doc(PC, pc_name)
	supplier = (pc.supplier or "").strip()
	if not supplier:
		frappe.throw(_("Procurement Contract has no supplier."), frappe.ValidationError)
	currency = pc.currency
	if not currency or not frappe.db.exists("Currency", currency):
		frappe.throw(_("Procurement Contract currency is not valid."), frappe.ValidationError)

	recv_user = received_by_user or frappe.session.user
	if not frappe.db.exists("User", recv_user):
		frappe.throw(_("Received By user not found."), frappe.ValidationError)

	biz = (grn_business_id or "").strip() or frappe.generate_hash(length=16)
	if frappe.db.exists(GRN, {"business_id": biz}):
		frappe.throw(_("GRN Business ID already exists."), frappe.ValidationError)

	grn_rows: list[dict[str, Any]] = []
	for row in items_list:
		if not isinstance(row, dict):
			frappe.throw(_("Each item row must be an object."), frappe.ValidationError)
		code = (row.get("item_code") or "").strip()
		if not code:
			frappe.throw(_("Each line must have item_code."), frappe.ValidationError)
		qty = flt(row.get("quantity"))
		if qty <= 0:
			frappe.throw(_("Each line must have a positive quantity."), frappe.ValidationError)
		grn_rows.append(
			{
				"item_code": code,
				"item_name": (row.get("item_name") or "").strip(),
				"quantity": qty,
				"unit_of_measure": (row.get("unit_of_measure") or "").strip() or None,
				"unit_rate": flt(row.get("unit_rate")) if row.get("unit_rate") is not None else None,
			}
		)

	grn = frappe.get_doc(
		{
			"doctype": GRN,
			"business_id": biz,
			"contract": pc_name,
			"supplier": supplier,
			"store": store,
			"receipt_datetime": now_datetime(),
			"received_by_user": recv_user,
			"inspection_reference": ar.inspection_record,
			"acceptance_reference": ar_name,
			"status": "Received",
			"currency": currency,
			"remarks": remarks,
			"items": grn_rows,
		}
	)

	grn.insert(ignore_permissions=True)

	try:
		posting_dt = grn.receipt_datetime or now_datetime()
		ledger_names: list[str] = []
		for line in grn.items:
			uom = (line.unit_of_measure or "").strip() or "Nos"
			sle = frappe.get_doc(
				{
					"doctype": SLE,
					"store": store,
					"item_reference": (line.item_code or "").strip(),
					"entry_type": "Receipt",
					"entry_direction": "In",
					"quantity": flt(line.quantity),
					"unit_of_measure": uom,
					"posting_datetime": posting_dt,
					"source_doctype": GRN,
					"source_docname": grn.name,
					"remarks": f"GRN receipt {grn.business_id}",
				}
			)
			sle.insert(ignore_permissions=True)
			ledger_names.append(sle.name)
	except Exception:
		_rollback_grn_and_ledgers(grn.name)
		raise

	new_pct = None
	cv = flt(pc.contract_value)
	if cv > 0:
		grn_total = flt(grn.total_received_value)
		delta = (grn_total / cv) * 100.0
		prev = flt(frappe.db.get_value(PC, pc_name, "completion_percent"))
		new_pct = min(100.0, prev + delta)
		frappe.db.set_value(PC, pc_name, "completion_percent", new_pct, update_modified=True)

	return {
		"goods_receipt_note": grn.name,
		"grn_business_id": grn.business_id,
		"store_ledger_entries": ledger_names,
		"completion_percent": new_pct,
	}


@frappe.whitelist()
def receive_goods_from_contract_api(
	contract_id: str | None = None,
	acceptance_record_id: str | None = None,
	store: str | None = None,
	items: str | list | None = None,
	grn_business_id: str | None = None,
	received_by_user: str | None = None,
	remarks: str | None = None,
):
	"""Whitelisted entry point for ``frappe.call`` (JSON ``items`` when sent as string)."""
	if not contract_id or not acceptance_record_id or not store:
		frappe.throw(_("contract_id, acceptance_record_id, and store are required."), frappe.ValidationError)
	return receive_goods_from_contract(
		contract_id,
		acceptance_record_id,
		store,
		items,
		grn_business_id=grn_business_id,
		received_by_user=received_by_user,
		remarks=remarks,
	)
