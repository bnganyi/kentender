# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Award Outcome Line — child table on Award Decision (PROC-STORY-078)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

BID_SUBMISSION = "Bid Submission"


def _strip(s: str | None) -> str:
	return (s or "").strip()


def validate_award_outcome_line_row(parent, row) -> None:
	"""Called from Award Decision.validate for each outcome line."""
	bn = _strip(getattr(row, "bid_submission", None))
	if bn and not frappe.db.exists(BID_SUBMISSION, bn):
		frappe.throw(
			_("Bid Submission {0} does not exist.").format(frappe.bold(bn)),
			frappe.ValidationError,
			title=_("Invalid bid submission"),
		)
	tender = _strip(getattr(parent, "tender", None))
	if tender and bn:
		bt = frappe.db.get_value(BID_SUBMISSION, bn, "tender")
		if bt and _strip(bt) != tender:
			frappe.throw(
				_("Outcome line bid must belong to the award tender."),
				frappe.ValidationError,
				title=_("Bid tender mismatch"),
			)
	bs_sup = frappe.db.get_value(BID_SUBMISSION, bn, "supplier") if bn else None
	sup = _strip(getattr(row, "supplier", None))
	if bn and bs_sup is not None and sup and _strip(bs_sup) != sup:
		frappe.throw(
			_("Supplier must match the bid submission supplier."),
			frappe.ValidationError,
			title=_("Supplier mismatch"),
		)
	rp = getattr(row, "ranking_position", None)
	if rp is not None:
		try:
			iv = int(rp)
		except (TypeError, ValueError):
			return
		if iv < 0:
			frappe.throw(
				_("Ranking Position cannot be negative."),
				frappe.ValidationError,
				title=_("Invalid ranking"),
			)


class AwardOutcomeLine(Document):
	"""Child table row; validation is driven from **Award Decision**."""

	pass
