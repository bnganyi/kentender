# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Resolve candidate bids eligible for opening (PROC-STORY-053)."""

from __future__ import annotations

from typing import Any

import frappe

BS = "Bid Submission"

WS_SUB = "Submitted"
ST_SUB = "Submitted"
ST_WD = "Withdrawn"


def _row_ok(r: dict[str, Any]) -> tuple[bool, list[str]]:
	reasons: list[str] = []
	if (r.get("workflow_state") or "").strip() == "Draft":
		reasons.append("draft_workflow")
	if (r.get("status") or "").strip() == ST_WD:
		reasons.append("withdrawn")
	if not int(r.get("is_final_submission") or 0):
		reasons.append("not_final_submission")
	if not int(r.get("active_submission_flag") or 0):
		reasons.append("inactive_submission_row")
	if (r.get("workflow_state") or "").strip() != WS_SUB:
		reasons.append("workflow_not_submitted")
	if (r.get("status") or "").strip() != ST_SUB:
		reasons.append("status_not_submitted")
	if int(r.get("is_opening_visible") or 0):
		reasons.append("already_opening_visible")
	if (r.get("sealed_status") or "").strip() == "Opened":
		reasons.append("already_sealed_opened")
	return (len(reasons) == 0, reasons)


def resolve_candidate_bids_for_tender(tender_id: str) -> dict[str, Any]:
	"""Return ``candidates`` (latest eligible row per supplier) and ``excluded`` with reasons."""
	tid = (tender_id or "").strip()
	out: dict[str, Any] = {"tender": tid, "candidates": [], "excluded": []}
	if not tid:
		return out

	rows = frappe.get_all(
		BS,
		filters={"tender": tid},
		fields=[
			"name",
			"business_id",
			"supplier",
			"workflow_state",
			"status",
			"is_final_submission",
			"active_submission_flag",
			"sealed_status",
			"is_opening_visible",
			"submission_version_no",
			"submitted_on",
		],
		order_by="supplier asc, submission_version_no desc, modified desc",
	)

	candidates: list[dict[str, Any]] = []
	excluded: list[dict[str, Any]] = []
	chosen_supplier: set[str] = set()

	for r in rows:
		name = r.get("name")
		supplier = (r.get("supplier") or "").strip()
		ok, reasons = _row_ok(r)
		if not ok:
			excluded.append({"bid_submission": name, "supplier": supplier, "reasons": reasons})
			continue
		if supplier in chosen_supplier:
			excluded.append({"bid_submission": name, "supplier": supplier, "reasons": ["superseded_by_newer_row"]})
			continue
		chosen_supplier.add(supplier)
		candidates.append(dict(r))

	return {"tender": tid, "candidates": candidates, "excluded": excluded}
