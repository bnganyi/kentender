# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation Record — per-evaluator scoring header for a stage and bid (PROC-STORY-061)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

from kentender_procurement.kentender_procurement.doctype.evaluation_score_line.evaluation_score_line import (
	validate_evaluation_score_line_row,
)

EVALUATION_SESSION = "Evaluation Session"
EVALUATION_STAGE = "Evaluation Stage"
BID_SUBMISSION = "Bid Submission"
DOCTYPE = "Evaluation Record"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class EvaluationRecord(Document):
	def validate(self):
		self._normalize_text()
		self._validate_evaluation_session()
		self._validate_evaluation_stage()
		self._validate_bid_submission()
		self._validate_supplier_matches_bid()
		self._validate_unique_tuple()
		self._validate_lock_requires_submit()
		self._validate_score_lines()
		self._validate_unique_score_line_criteria()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("business_id", "supplier", "summary_comments"):
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

	def _validate_unique_tuple(self) -> None:
		es = _strip(self.evaluation_session)
		st = _strip(self.evaluation_stage)
		bn = _strip(self.bid_submission)
		eu = _strip(self.evaluator_user)
		if not es or not st or not bn or not eu:
			return
		filters: dict = {
			"evaluation_session": es,
			"evaluation_stage": st,
			"bid_submission": bn,
			"evaluator_user": eu,
		}
		if _strip(self.name):
			filters["name"] = ("!=", self.name)
		others = frappe.get_all(DOCTYPE, filters=filters, pluck="name", limit=1)
		if others:
			frappe.throw(
				_("An evaluation record already exists for this session, stage, bid, and evaluator."),
				frappe.ValidationError,
				title=_("Duplicate evaluation record"),
			)

	def _validate_lock_requires_submit(self) -> None:
		if self.locked_on and not self.submitted_on:
			frappe.throw(
				_("Submitted On is required when Locked On is set."),
				frappe.ValidationError,
				title=_("Incomplete lock"),
			)

	def _validate_score_lines(self) -> None:
		for row in self.score_lines or []:
			validate_evaluation_score_line_row(self, row)

	def _validate_unique_score_line_criteria(self) -> None:
		seen: set[str] = set()
		for row in self.score_lines or []:
			tc = _strip(getattr(row, "tender_criteria", None))
			if not tc:
				continue
			if tc in seen:
				frappe.throw(
					_("Each Tender Criteria may appear only once on an Evaluation Record."),
					frappe.ValidationError,
					title=_("Duplicate criteria line"),
				)
			seen.add(tc)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.business_id), _strip(self.status) or "—")
