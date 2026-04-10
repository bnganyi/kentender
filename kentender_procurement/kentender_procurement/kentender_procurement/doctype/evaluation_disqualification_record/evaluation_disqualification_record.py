# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation Disqualification Record — formal DQ row for a bid at a stage (PROC-STORY-063)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

EVALUATION_SESSION = "Evaluation Session"
EVALUATION_STAGE = "Evaluation Stage"
BID_SUBMISSION = "Bid Submission"
EXCEPTION_RECORD = "Exception Record"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class EvaluationDisqualificationRecord(Document):
	def validate(self):
		self._normalize_text()
		self._validate_evaluation_session()
		self._validate_evaluation_stage()
		self._validate_bid_submission()
		self._validate_supplier_matches_bid()
		self._validate_exception_record()
		self._validate_decision_pairing()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("supplier", "reason_details"):
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

	def _validate_evaluation_stage(self) -> None:
		st = _strip(self.evaluation_stage)
		if not st:
			return
		if not frappe.db.exists(EVALUATION_STAGE, st):
			frappe.throw(
				_("Evaluation Stage {0} does not exist.").format(frappe.bold(st)),
				frappe.ValidationError,
				title=_("Invalid evaluation stage"),
			)
		es = _strip(self.evaluation_session)
		if not es:
			return
		stage_es = frappe.db.get_value(EVALUATION_STAGE, st, "evaluation_session")
		if stage_es and _strip(stage_es) != es:
			frappe.throw(
				_("Evaluation Stage must belong to the selected Evaluation Session."),
				frappe.ValidationError,
				title=_("Stage session mismatch"),
			)

	def _validate_bid_submission(self) -> None:
		bn = _strip(self.bid_submission)
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
				_("Bid Submission must belong to the same Tender as the Evaluation Session."),
				frappe.ValidationError,
				title=_("Bid tender mismatch"),
			)

	def _validate_supplier_matches_bid(self) -> None:
		bn = _strip(self.bid_submission)
		if not bn:
			return
		bs_sup = frappe.db.get_value(BID_SUBMISSION, bn, "supplier")
		rec_sup = _strip(self.supplier)
		if bs_sup is not None and _strip(bs_sup) != rec_sup:
			frappe.throw(
				_("Supplier must match the Bid Submission supplier."),
				frappe.ValidationError,
				title=_("Supplier mismatch"),
			)

	def _validate_exception_record(self) -> None:
		er = _strip(self.exception_record)
		if not er:
			return
		if not frappe.db.exists(EXCEPTION_RECORD, er):
			frappe.throw(
				_("Exception Record {0} does not exist.").format(frappe.bold(er)),
				frappe.ValidationError,
				title=_("Invalid exception record"),
			)

	def _validate_decision_pairing(self) -> None:
		du = _strip(self.decided_by_user)
		do = self.decided_on
		if do and not du:
			frappe.throw(
				_("Decided By User is required when Decided On is set."),
				frappe.ValidationError,
				title=_("Incomplete decision"),
			)
		if du and not do:
			frappe.throw(
				_("Decided On is required when Decided By User is set."),
				frappe.ValidationError,
				title=_("Incomplete decision"),
			)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.supplier), _strip(self.status) or "—")
