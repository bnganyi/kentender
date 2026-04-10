# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for bid desk queues and script reports (PROC-STORY-047).

These functions return lightweight row dicts; they do not mutate data.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
BS = "Bid Submission"
BR = "Bid Receipt"
TENDER = "Tender"

WS_DRAFT = "Draft"
WS_SUB = "Submitted"
ST_DRAFT = "Draft"
ST_SUB = "Submitted"
ST_WD = "Withdrawn"

WS_PUB = "Published"
SEALED = "Sealed"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _entity_filter(procuring_entity: str | None) -> dict[str, Any]:
	ent = _norm(procuring_entity)
	if not ent:
		return {}
	return {"procuring_entity": ent}


def _tender_names_for_entity(procuring_entity: str | None) -> list[str] | None:
	ent = _norm(procuring_entity)
	if not ent:
		return None
	return frappe.get_all(TENDER, filters={"procuring_entity": ent}, pluck="name") or []


def _bs_filters(procuring_entity: str | None, extra: dict[str, Any]) -> dict[str, Any]:
	filters = dict(extra)
	filters.update(_entity_filter(procuring_entity))
	return filters


_BS_LIST_FIELDS = [
	"name",
	"business_id",
	"tender",
	"supplier",
	"workflow_state",
	"status",
	"procuring_entity",
	"submission_version_no",
	"is_final_submission",
	"submitted_on",
	"modified",
]

_BR_LIST_FIELDS = [
	"name",
	"business_id",
	"receipt_no",
	"bid_submission",
	"tender",
	"supplier",
	"status",
	"submission_timestamp",
	"issued_on",
	"modified",
]


def get_draft_bids(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Bids in **Draft** workflow (active supplier work-in-progress)."""
	return frappe.get_all(
		BS,
		filters=_bs_filters(
			procuring_entity,
			{"workflow_state": WS_DRAFT, "status": ST_DRAFT, "active_submission_flag": 1},
		),
		fields=_BS_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_submitted_bids(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Final **submitted** bids (pre-opening / general submitted queue)."""
	return frappe.get_all(
		BS,
		filters=_bs_filters(
			procuring_entity,
			{
				"workflow_state": WS_SUB,
				"status": ST_SUB,
				"is_final_submission": 1,
			},
		),
		fields=_BS_LIST_FIELDS,
		order_by="submitted_on desc",
		limit=limit,
	)


def get_withdrawn_bids(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Withdrawn bids (historical)."""
	return frappe.get_all(
		BS,
		filters=_bs_filters(
			procuring_entity,
			{"workflow_state": "Withdrawn", "status": ST_WD},
		),
		fields=_BS_LIST_FIELDS + ["withdrawn_on"],
		order_by="withdrawn_on desc",
		limit=limit,
	)


def get_bids_awaiting_opening(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Submitted sealed bids not yet opening-visible on a **Published** tender (opening desk)."""
	base: dict[str, Any] = {
		"workflow_state": WS_SUB,
		"status": ST_SUB,
		"is_final_submission": 1,
		"is_opening_visible": 0,
		"sealed_status": SEALED,
	}
	filters = _bs_filters(procuring_entity, base)
	rows = frappe.get_all(
		BS,
		filters=filters,
		fields=_BS_LIST_FIELDS + ["sealed_status", "opening_datetime"],
		order_by="tender asc, submitted_on asc",
		limit=limit * 3,
	)
	out: list[dict[str, Any]] = []
	for r in rows:
		tender_name = _norm(r.get("tender"))
		if not tender_name:
			continue
		trow = frappe.db.get_value(
			TENDER,
			tender_name,
			["workflow_state", "opening_datetime"],
			as_dict=True,
		)
		if not trow or _norm(trow.get("workflow_state")) != WS_PUB:
			continue
		out.append({**r, "tender_opening_datetime": trow.get("opening_datetime")})
		if len(out) >= limit:
			break
	return out


def get_submission_receipts(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Bid Receipt rows; optional procuring entity via linked Tender."""
	tn = _tender_names_for_entity(procuring_entity)
	if procuring_entity and not tn:
		return []
	filters: dict[str, Any] = {"status": ("!=", "Voided")}
	if tn is not None:
		filters["tender"] = ("in", tn)
	return frappe.get_all(
		BR,
		filters=filters,
		fields=_BR_LIST_FIELDS,
		order_by="issued_on desc",
		limit=limit,
	)


def bid_queue_report_columns() -> list[str]:
	return [
		_("Bid Submission") + ":Link/Bid Submission:180",
		_("Business ID") + ":Data:140",
		_("Tender") + ":Link/Tender:160",
		_("Supplier") + ":Data:120",
		_("Workflow Stage") + ":Data:110",
		_("Status") + ":Data:110",
		_("Version") + ":Int:70",
		_("Submitted On") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def bid_queue_row_values(row: dict[str, Any]) -> list[Any]:
	return [
		row.get("name"),
		row.get("business_id"),
		row.get("tender"),
		row.get("supplier"),
		row.get("workflow_state"),
		row.get("status"),
		row.get("submission_version_no"),
		row.get("submitted_on"),
		row.get("modified"),
	]


def bid_awaiting_opening_report_columns() -> list[str]:
	return [
		_("Bid Submission") + ":Link/Bid Submission:180",
		_("Business ID") + ":Data:140",
		_("Tender") + ":Link/Tender:160",
		_("Supplier") + ":Data:120",
		_("Workflow Stage") + ":Data:110",
		_("Status") + ":Data:110",
		_("Version") + ":Int:70",
		_("Submitted On") + ":Datetime:150",
		_("Sealed Status") + ":Data:100",
		_("Tender Opening") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def bid_awaiting_opening_row_values(row: dict[str, Any]) -> list[Any]:
	return [
		row.get("name"),
		row.get("business_id"),
		row.get("tender"),
		row.get("supplier"),
		row.get("workflow_state"),
		row.get("status"),
		row.get("submission_version_no"),
		row.get("submitted_on"),
		row.get("sealed_status"),
		row.get("tender_opening_datetime"),
		row.get("modified"),
	]


def bid_receipt_report_columns() -> list[str]:
	return [
		_("Bid Receipt") + ":Link/Bid Receipt:160",
		_("Receipt No") + ":Data:140",
		_("Business ID") + ":Data:140",
		_("Tender") + ":Link/Tender:160",
		_("Supplier") + ":Data:120",
		_("Bid Submission") + ":Link/Bid Submission:180",
		_("Status") + ":Data:90",
		_("Submission Timestamp") + ":Datetime:150",
		_("Issued On") + ":Datetime:150",
	]


def bid_receipt_row_values(row: dict[str, Any]) -> list[Any]:
	return [
		row.get("name"),
		row.get("receipt_no"),
		row.get("business_id"),
		row.get("tender"),
		row.get("supplier"),
		row.get("bid_submission"),
		row.get("status"),
		row.get("submission_timestamp"),
		row.get("issued_on"),
	]


def bid_report_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": _("Procuring Entity"),
			"fieldtype": "Link",
			"options": "Procuring Entity",
		},
	]


__all__ = [
	"bid_awaiting_opening_report_columns",
	"bid_awaiting_opening_row_values",
	"bid_queue_report_columns",
	"bid_queue_row_values",
	"bid_receipt_report_columns",
	"bid_receipt_row_values",
	"bid_report_entity_filter",
	"get_bids_awaiting_opening",
	"get_draft_bids",
	"get_submission_receipts",
	"get_submitted_bids",
	"get_withdrawn_bids",
]
