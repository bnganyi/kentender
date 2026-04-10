# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Minimal Golden — one Bid Receipt for ``bid_1`` (PROC-STORY-040)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

BR = "Bid Receipt"
BS = "Bid Submission"


def delete_minimal_golden_bid_receipt(ds: dict[str, Any]) -> None:
	"""Remove canonical Bid Receipt and clear ``latest_receipt`` on the linked bid."""
	spec = ds.get("bid_receipt") or {}
	biz = (spec.get("business_id") or "").strip()
	if not biz:
		return
	name = frappe.db.get_value(BR, {"business_id": biz}, "name")
	if not name:
		return
	for bn in frappe.get_all(BS, filters={"latest_receipt": name}, pluck="name"):
		frappe.db.set_value(BS, bn, "latest_receipt", None)
	frappe.delete_doc(BR, name, force=True, ignore_permissions=True)


def load_bid_receipts(ds: dict[str, Any], *, procuring_entity: str) -> dict[str, Any]:
	"""Create Bid Receipt for ``bid_receipt`` spec after Bid Submissions exist; sets ``latest_receipt`` on the bid."""
	del procuring_entity  # reserved for symmetry with other loaders
	spec = ds.get("bid_receipt") or {}
	biz = (spec.get("business_id") or "").strip()
	if not biz:
		return {}

	key = (spec.get("for_bid_future_key") or "bid_1").strip()
	fut = ds.get("future_business_ids") or {}
	bs_business_id = (fut.get(key) or "").strip()
	if not bs_business_id:
		return {}

	delete_minimal_golden_bid_receipt(ds)

	bs_name = frappe.db.get_value(BS, {"business_id": bs_business_id}, "name")
	if not bs_name:
		return {}

	bid_row = frappe.db.get_value(
		BS,
		bs_name,
		["tender", "supplier"],
		as_dict=True,
	)
	if not bid_row or not bid_row.get("tender"):
		return {}

	tn = bid_row["tender"]
	sub_ts = frappe.db.get_value("Tender", tn, "submission_deadline")
	stamp = get_datetime(sub_ts) if sub_ts else now_datetime()
	issued = stamp

	proc_email = "procurement.test@ken-tender.test"
	if not frappe.db.exists("User", proc_email):
		proc_email = "Administrator"

	row = {
		"doctype": BR,
		"business_id": biz,
		"receipt_no": (spec.get("receipt_no") or "RCPT-MOH-2026-0001").strip(),
		"bid_submission": bs_name,
		"tender": tn,
		"supplier": (bid_row.get("supplier") or "").strip(),
		"issued_to_user": proc_email,
		"submission_timestamp": stamp,
		"submission_hash": (spec.get("submission_hash") or "sha256:minimal_golden_submission_v1").strip(),
		"receipt_hash": (spec.get("receipt_hash") or "sha256:minimal_golden_receipt_v1").strip(),
		"issued_on": issued,
		"status": "Issued",
	}
	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	frappe.db.set_value(BS, bs_name, "latest_receipt", doc.name, update_modified=False)
	return {"name": doc.name, "business_id": biz, "bid_submission": bs_name}
