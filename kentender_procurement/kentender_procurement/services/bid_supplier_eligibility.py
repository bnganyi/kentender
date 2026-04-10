# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Supplier eligibility to prepare a bid against a tender (PROC-STORY-043).

All tender/supplier eligibility rules for bid drafting live here so product logic is not
scattered or hardcoded in controllers. Extend this module when prequalified lists and
reserved-group checks are implemented.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.services.tender_workflow_actions import (
	SUB_CANCELLED,
	SUB_CLOSED,
	SUB_OPEN,
	WS_CANCELLED,
	WS_PUBLISHED,
)

TENDER_DOCTYPE = "Tender"

MODE_OPEN = "Open"
MODES_REQUIRING_EXTENDED_RULES = frozenset({"Prequalified", "Reserved Group", "Mixed"})


def _strip(s: str | None) -> str:
	return (s or "").strip()


def assess_supplier_bid_eligibility(tender_name: str, supplier_id: str) -> dict[str, Any]:
	"""Return whether the supplier may open or continue a draft bid for this tender.

	:returns: ``eligible`` (bool), ``reasons`` (list[str]), plus diagnostic fields.
	"""
	tn = _strip(tender_name)
	sup = _strip(supplier_id)
	empty: dict[str, Any] = {
		"eligible": False,
		"reasons": [],
		"tender": tn or None,
		"supplier": sup or None,
		"tender_workflow_state": None,
		"tender_submission_status": None,
		"supplier_eligibility_rule_mode": None,
	}
	if not tn:
		empty["reasons"].append("Tender is required.")
		return empty
	if not sup:
		empty["reasons"].append("Supplier is required.")
		return empty

	row = frappe.db.get_value(
		TENDER_DOCTYPE,
		tn,
		[
			"name",
			"workflow_state",
			"submission_status",
			"supplier_eligibility_rule_mode",
		],
		as_dict=True,
	)
	if not row:
		empty["reasons"].append(f"Tender {tn!r} does not exist.")
		return empty

	ws = _strip(row.get("workflow_state"))
	ss = _strip(row.get("submission_status")) or "Not Open"
	mode = _strip(row.get("supplier_eligibility_rule_mode")) or MODE_OPEN

	out: dict[str, Any] = {
		"eligible": True,
		"reasons": [],
		"tender": tn,
		"supplier": sup,
		"tender_workflow_state": ws,
		"tender_submission_status": ss,
		"supplier_eligibility_rule_mode": mode,
	}

	if ws == WS_CANCELLED:
		out["eligible"] = False
		out["reasons"].append("Tender is cancelled.")
	if ws != WS_PUBLISHED:
		out["eligible"] = False
		out["reasons"].append(f"Tender must be published to accept bids (current stage: {ws or '—'}).")
	if ss != SUB_OPEN:
		out["eligible"] = False
		if ss == SUB_CLOSED:
			out["reasons"].append("Submission window is closed.")
		elif ss == SUB_CANCELLED:
			out["reasons"].append("Tender submission is cancelled.")
		else:
			out["reasons"].append(f"Submission window is not open (status: {ss or '—'}).")

	if mode == MODE_OPEN:
		pass
	elif mode in MODES_REQUIRING_EXTENDED_RULES:
		out["eligible"] = False
		out["reasons"].append(
			f"Supplier eligibility mode {mode!r} requires extended rules (not yet applied for this supplier)."
		)
	else:
		out["eligible"] = False
		out["reasons"].append(f"Unsupported supplier eligibility mode {mode!r}.")

	return out
