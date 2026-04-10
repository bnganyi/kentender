# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation Aggregation Result — derived per-bid aggregation row for an evaluation session (PROC-STORY-064).

Rows are intended to be written by server-side services (PROC-STORY-070). Desk roles are read-only for
Procurement Officer and Auditor; System Manager retains full access for administration and tests.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

EVALUATION_SESSION = "Evaluation Session"
BID_SUBMISSION = "Bid Submission"
DOCTYPE = "Evaluation Aggregation Result"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class EvaluationAggregationResult(Document):
	def validate(self):
		if not getattr(frappe.flags, "in_evaluation_aggregation_service", False) and not frappe.in_test:
			frappe.throw(
				_("Evaluation Aggregation Result is derived. Use the aggregation service to create or update rows."),
				frappe.ValidationError,
				title=_("Read-only"),
			)
		self._normalize_text()
		self._validate_evaluation_session()
		self._validate_bid_submission()
		self._validate_supplier_matches_bid()
		self._validate_ranking_position()
		self._validate_unique_session_bid()
		self._set_display_label()

	def _normalize_text(self) -> None:
		if self.supplier and isinstance(self.supplier, str):
			self.supplier = self.supplier.strip()

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

	def _validate_ranking_position(self) -> None:
		rp = self.ranking_position
		if rp is None:
			return
		try:
			val = int(rp)
		except (TypeError, ValueError):
			return
		if val < 0:
			frappe.throw(
				_("Ranking Position cannot be negative."),
				frappe.ValidationError,
				title=_("Invalid ranking"),
			)

	def _validate_unique_session_bid(self) -> None:
		es = _strip(self.evaluation_session)
		bn = _strip(self.bid_submission)
		if not es or not bn:
			return
		filters: dict = {"evaluation_session": es, "bid_submission": bn}
		if _strip(self.name):
			filters["name"] = ("!=", self.name)
		others = frappe.get_all(DOCTYPE, filters=filters, pluck="name", limit=1)
		if others:
			frappe.throw(
				_("Only one aggregation result is allowed per evaluation session and bid submission."),
				frappe.ValidationError,
				title=_("Duplicate aggregation result"),
			)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.supplier), _strip(self.calculation_status) or "—")
