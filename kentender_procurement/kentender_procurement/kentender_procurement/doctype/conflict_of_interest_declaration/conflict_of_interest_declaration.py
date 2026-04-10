# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Conflict of Interest Declaration — evaluator COI record (PROC-STORY-060)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

EVALUATION_SESSION = "Evaluation Session"
BID_SUBMISSION = "Bid Submission"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ConflictofInterestDeclaration(Document):
	def validate(self):
		self._normalize_text()
		self._validate_evaluation_session()
		self._validate_related_bid()
		self._validate_review_pairing()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("conflict_summary", "review_notes", "related_supplier"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

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

	def _validate_related_bid(self) -> None:
		bn = _strip(self.related_bid_submission)
		if not bn:
			return
		if not frappe.db.exists(BID_SUBMISSION, bn):
			frappe.throw(
				_("Bid Submission {0} does not exist.").format(frappe.bold(bn)),
				frappe.ValidationError,
				title=_("Invalid bid submission"),
			)
		es = _strip(self.evaluation_session)
		if not es:
			return
		tn = frappe.db.get_value(EVALUATION_SESSION, es, "tender")
		bt = frappe.db.get_value(BID_SUBMISSION, bn, "tender")
		if tn and bt and _strip(bt) != _strip(tn):
			frappe.throw(
				_("Related Bid Submission must belong to the same Tender as the Evaluation Session."),
				frappe.ValidationError,
				title=_("Bid tender mismatch"),
			)

	def _validate_review_pairing(self) -> None:
		rb = _strip(self.reviewed_by)
		ro = self.reviewed_on
		if ro and not rb:
			frappe.throw(
				_("Reviewed By is required when Reviewed On is set."),
				frappe.ValidationError,
				title=_("Incomplete review"),
			)
		if rb and not ro:
			frappe.throw(
				_("Reviewed On is required when Reviewed By is set."),
				frappe.ValidationError,
				title=_("Incomplete review"),
			)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.evaluator_user), _strip(self.declaration_status) or "—")
