# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Minimal Golden — seed two Bid Submission rows (future_business_ids bid_1 / bid_2)."""

from __future__ import annotations

from typing import Any

import frappe

BS = "Bid Submission"
BSE = "Bid Submission Event"
BD = "Bid Document"
BES = "Bid Envelope Section"
BR = "Bid Receipt"
TENDER = "Tender"

# Align with canonical suppliers: first bid → supplier1 persona, second → supplier2.
_BID_KEYS = (
	("bid_1", "MG-SUP-01"),
	("bid_2", "MG-SUP-02"),
)


def delete_minimal_golden_bid_submissions(ds: dict[str, Any]) -> None:
	"""Remove golden bids by ``business_id`` (children first). Safe if missing."""
	fut = ds.get("future_business_ids") or {}
	for label, _sup in _BID_KEYS:
		bid = (fut.get(label) or "").strip()
		if bid:
			_delete_bid_submission_tree_by_business_id(bid)


def _delete_bid_submission_tree_by_business_id(business_id: str) -> None:
	name = frappe.db.get_value(BS, {"business_id": business_id}, "name")
	if not name:
		return
	for br in frappe.get_all(BR, filters={"bid_submission": name}, pluck="name"):
		frappe.delete_doc(BR, br, force=True, ignore_permissions=True)
	for dt, field in (
		(BSE, "bid_submission"),
		(BD, "bid_submission"),
		(BES, "bid_submission"),
	):
		for child in frappe.get_all(dt, filters={field: name}, pluck="name"):
			frappe.delete_doc(dt, child, force=True, ignore_permissions=True)
	frappe.delete_doc(BS, name, force=True, ignore_permissions=True)


def load_bid_submissions(ds: dict[str, Any], *, procuring_entity: str) -> dict[str, Any]:
	"""Insert two Bid Submission docs for ``future_business_ids`` bid_1 / bid_2; idempotent on business_id."""
	t_spec = ds.get("tender") or {}
	t_name = (t_spec.get("name") or "").strip()
	if not t_name or not frappe.db.exists(TENDER, t_name):
		return {}

	t_row = frappe.db.get_value(
		TENDER,
		t_name,
		[
			"procuring_entity",
			"procurement_method",
			"submission_deadline",
			"opening_datetime",
		],
		as_dict=True,
	)
	if not t_row:
		return {}

	fut = ds.get("future_business_ids") or {}
	out: list[dict[str, Any]] = []

	for label, supplier_code in _BID_KEYS:
		business_id = (fut.get(label) or "").strip()
		if not business_id:
			continue
		_delete_bid_submission_tree_by_business_id(business_id)

		row: dict[str, Any] = {
			"doctype": BS,
			"business_id": business_id,
			"tender": t_name,
			"tender_lot_scope": "Whole Tender",
			"supplier": supplier_code,
			"status": "Draft",
			"workflow_state": "Draft",
			"submission_version_no": 1,
			"procuring_entity": t_row.get("procuring_entity") or procuring_entity,
			"procurement_method": t_row.get("procurement_method"),
			"submission_deadline": t_row.get("submission_deadline"),
			"opening_datetime": t_row.get("opening_datetime"),
		}
		doc = frappe.get_doc(row)
		doc.insert(ignore_permissions=True)
		out.append({"future_key": label, "business_id": business_id, "name": doc.name})

	return {"bid_submissions": out}
