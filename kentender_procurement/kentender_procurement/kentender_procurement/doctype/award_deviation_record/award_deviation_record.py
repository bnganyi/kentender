# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Award Deviation Record — explicit deviation from evaluation recommendation (PROC-STORY-075)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

AWARD_DECISION = "Award Decision"
BID_SUBMISSION = "Bid Submission"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class AwardDeviationRecord(Document):
	def validate(self):
		self._normalize_text()
		self._validate_award_decision()
		self._validate_bids_match_tender()
		self._validate_suppliers_match_bids()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("recommended_supplier", "approved_supplier"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _validate_award_decision(self) -> None:
		an = _strip(self.award_decision)
		if not an:
			return
		if not frappe.db.exists(AWARD_DECISION, an):
			frappe.throw(
				_("Award Decision {0} does not exist.").format(frappe.bold(an)),
				frappe.ValidationError,
				title=_("Invalid award decision"),
			)

	def _tender_for_award(self) -> str | None:
		ad = _strip(self.award_decision)
		if not ad:
			return None
		return _strip(frappe.db.get_value(AWARD_DECISION, ad, "tender"))

	def _validate_bid(self, field: str, label: str) -> None:
		bn = _strip(getattr(self, field, None))
		if not bn:
			return
		if not frappe.db.exists(BID_SUBMISSION, bn):
			frappe.throw(
				_("Bid Submission {0} does not exist.").format(frappe.bold(bn)),
				frappe.ValidationError,
				title=_("Invalid bid submission"),
			)
		tn = self._tender_for_award()
		bt = frappe.db.get_value(BID_SUBMISSION, bn, "tender")
		if tn and bt and _strip(bt) != tn:
			frappe.throw(
				_("{0} must belong to the award decision tender.").format(label),
				frappe.ValidationError,
				title=_("Bid tender mismatch"),
			)

	def _validate_bids_match_tender(self) -> None:
		self._validate_bid("recommended_bid_submission", _("Recommended bid"))
		self._validate_bid("approved_bid_submission", _("Approved bid"))

	def _validate_suppliers_match_bids(self) -> None:
		for bid_field, sup_field in (
			("recommended_bid_submission", "recommended_supplier"),
			("approved_bid_submission", "approved_supplier"),
		):
			bn = _strip(getattr(self, bid_field, None))
			sup = _strip(getattr(self, sup_field, None))
			if not bn or not sup:
				continue
			bs_sup = frappe.db.get_value(BID_SUBMISSION, bn, "supplier")
			if bs_sup is not None and _strip(bs_sup) != sup:
				frappe.throw(
					_("Supplier must match the bid submission for {0}.").format(bid_field),
					frappe.ValidationError,
					title=_("Supplier mismatch"),
				)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(
			_strip(self.recommended_supplier) or "—",
			_strip(self.approved_supplier) or "—",
		)
