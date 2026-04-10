# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation Report — session-level evaluation outcome document (PROC-STORY-065).

Generation and submission workflows belong to PROC-STORY-071; this DocType is model and validation only.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import strip_html

from kentender.utils.display_label import code_title_label

EVALUATION_SESSION = "Evaluation Session"
TENDER = "Tender"
BID_SUBMISSION = "Bid Submission"
DOCTYPE = "Evaluation Report"

_COUNT_FIELDS = ("responsive_bid_count", "non_responsive_bid_count", "disqualified_bid_count")


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _justification_plain(s: str | None) -> str:
	return _strip(strip_html(s or ""))


class EvaluationReport(Document):
	def validate(self):
		self._normalize_text()
		self._validate_evaluation_session()
		self._validate_tender_matches_session()
		self._validate_recommended_bid_submission()
		self._validate_currency()
		self._validate_bid_counts()
		self._validate_recommendation_justification()
		self._validate_unique_per_session()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("business_id", "recommended_supplier", "locked_hash"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())
		if self.special_conditions_notes and isinstance(self.special_conditions_notes, str):
			self.special_conditions_notes = self.special_conditions_notes.strip()

	def _validate_evaluation_session(self) -> None:
		sn = _strip(self.evaluation_session)
		if not sn:
			return
		if not frappe.db.exists(EVALUATION_SESSION, sn):
			frappe.throw(
				_("Evaluation Session {0} does not exist.").format(frappe.bold(sn)),
				frappe.ValidationError,
				title=_("Invalid evaluation session"),
			)

	def _validate_tender_matches_session(self) -> None:
		es = _strip(self.evaluation_session)
		tn = _strip(self.tender)
		if not es or not tn:
			return
		if not frappe.db.exists(TENDER, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)
		session_tender = frappe.db.get_value(EVALUATION_SESSION, es, "tender")
		if session_tender and _strip(session_tender) != tn:
			frappe.throw(
				_("Tender must match the selected Evaluation Session."),
				frappe.ValidationError,
				title=_("Tender session mismatch"),
			)

	def _validate_recommended_bid_submission(self) -> None:
		bn = _strip(self.recommended_bid_submission)
		if not bn:
			return
		if not frappe.db.exists(BID_SUBMISSION, bn):
			frappe.throw(
				_("Bid Submission {0} does not exist.").format(frappe.bold(bn)),
				frappe.ValidationError,
				title=_("Invalid bid submission"),
			)
		tn = _strip(self.tender)
		bt = frappe.db.get_value(BID_SUBMISSION, bn, "tender")
		if tn and bt and _strip(bt) != tn:
			frappe.throw(
				_("Recommended Bid Submission must belong to the same Tender as this report."),
				frappe.ValidationError,
				title=_("Bid tender mismatch"),
			)
		rec_sup = _strip(self.recommended_supplier)
		if not rec_sup:
			return
		bs_sup = frappe.db.get_value(BID_SUBMISSION, bn, "supplier")
		if bs_sup is not None and _strip(bs_sup) != rec_sup:
			frappe.throw(
				_("Recommended Supplier must match the recommended bid supplier."),
				frappe.ValidationError,
				title=_("Supplier mismatch"),
			)

	def _validate_currency(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		t_cur = frappe.db.get_value(TENDER, tn, "currency")
		t_cur = _strip(t_cur) if t_cur else ""
		if not t_cur:
			return
		# Tender currency is authoritative (recommended_amount / report context); align even if
		# framework defaults injected another company currency before validate.
		self.currency = t_cur

	def _validate_bid_counts(self) -> None:
		for fn in _COUNT_FIELDS:
			val = getattr(self, fn, None)
			if val is None:
				continue
			try:
				n = int(val)
			except (TypeError, ValueError):
				continue
			if n < 0:
				frappe.throw(
					_("Responsive, non-responsive, and disqualified bid counts cannot be negative."),
					frappe.ValidationError,
					title=_("Invalid bid count"),
				)

	def _validate_recommendation_justification(self) -> None:
		if not _strip(self.recommended_bid_submission):
			return
		if not _justification_plain(self.recommendation_justification):
			frappe.throw(
				_("Recommendation Justification is required when a Recommended Bid Submission is set."),
				frappe.ValidationError,
				title=_("Missing justification"),
			)

	def _validate_unique_per_session(self) -> None:
		es = _strip(self.evaluation_session)
		if not es:
			return
		filters: dict = {"evaluation_session": es}
		if _strip(self.name):
			filters["name"] = ("!=", self.name)
		others = frappe.get_all(DOCTYPE, filters=filters, pluck="name", limit=1)
		if others:
			frappe.throw(
				_("Only one Evaluation Report is allowed per evaluation session."),
				frappe.ValidationError,
				title=_("Duplicate evaluation report"),
			)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.business_id), _strip(self.status) or "—")
