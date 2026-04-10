# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Contract readiness gate for Award Decision (PROC-STORY-084)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

AD = "Award Decision"
SSP = "Standstill Period"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def get_award_contract_readiness(award_decision_id: str) -> dict[str, Any]:
	"""Return whether an award may proceed to contract creation, with explainable blockers."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	doc = frappe.get_doc(AD, an)
	blockers: list[str] = []

	st = _norm(doc.status)
	ast = _norm(doc.approval_status)

	if st in ("Rejected", "Cancelled"):
		blockers.append("award_terminal_state")
	elif ast != "Approved" or st != "Approved":
		blockers.append("award_not_approved")

	if int(doc.standstill_required or 0):
		spn = _norm(doc.standstill_period)
		if not spn:
			blockers.append("standstill_missing")
		else:
			row = frappe.db.get_value(
				SSP,
				spn,
				["status", "complaint_hold_flag"],
				as_dict=True,
			)
			if row:
				if int(row.get("complaint_hold_flag") or 0):
					blockers.append("complaint_hold")
				sst = _norm(row.get("status"))
				if sst not in ("Released", "Completed"):
					blockers.append("standstill_not_released")
	else:
		# No mandatory standstill: readiness follows approval; optional active standstill still blocks if present.
		spn = _norm(doc.standstill_period)
		if spn:
			row = frappe.db.get_value(
				SSP,
				spn,
				["status", "complaint_hold_flag"],
				as_dict=True,
			)
			if row and int(row.get("complaint_hold_flag") or 0):
				blockers.append("complaint_hold")
			if row and _norm(row.get("status")) == "Active":
				blockers.append("standstill_active")

	ready = len(blockers) == 0
	return {"ready": ready, "blockers": blockers, "award_decision": an}
