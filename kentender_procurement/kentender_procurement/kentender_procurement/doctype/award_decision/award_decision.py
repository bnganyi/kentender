# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Award Decision — contract-gating award header (PROC-STORY-073)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

from kentender_procurement.kentender_procurement.doctype.award_outcome_line.award_outcome_line import (
	validate_award_outcome_line_row,
)

TENDER = "Tender"
EVALUATION_SESSION = "Evaluation Session"
EVALUATION_REPORT = "Evaluation Report"
BID_SUBMISSION = "Bid Submission"
DOCTYPE = "Award Decision"
ADR = "Award Deviation Record"
SSP = "Standstill Period"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class AwardDecision(Document):
	def validate(self):
		self._normalize_text()
		self._validate_tender()
		self._validate_evaluation_session()
		self._validate_evaluation_report()
		self._validate_bid_links()
		self._validate_counts()
		self._validate_deviation_link()
		self._validate_standstill_link()
		self._validate_outcome_lines()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("business_id", "recommended_supplier", "approved_supplier", "tender_committee_ref", "lock_reason", "remarks"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _validate_tender(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		if not frappe.db.exists(TENDER, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)

	def _validate_evaluation_session(self) -> None:
		es = _strip(self.evaluation_session)
		if not es:
			return
		if not frappe.db.exists(EVALUATION_SESSION, es):
			frappe.throw(
				_("Evaluation Session {0} does not exist.").format(frappe.bold(es)),
				frappe.ValidationError,
				title=_("Invalid evaluation session"),
			)
		tn = _strip(self.tender)
		st = frappe.db.get_value(EVALUATION_SESSION, es, "tender")
		if tn and st and _strip(st) != tn:
			frappe.throw(
				_("Evaluation Session must belong to the selected Tender."),
				frappe.ValidationError,
				title=_("Session tender mismatch"),
			)

	def _validate_evaluation_report(self) -> None:
		rn = _strip(self.evaluation_report)
		es = _strip(self.evaluation_session)
		if not rn:
			return
		if not frappe.db.exists(EVALUATION_REPORT, rn):
			frappe.throw(
				_("Evaluation Report {0} does not exist.").format(frappe.bold(rn)),
				frappe.ValidationError,
				title=_("Invalid evaluation report"),
			)
		rs = frappe.db.get_value(EVALUATION_REPORT, rn, "evaluation_session")
		if es and rs and _strip(rs) != es:
			frappe.throw(
				_("Evaluation Report must belong to the selected Evaluation Session."),
				frappe.ValidationError,
				title=_("Report session mismatch"),
			)
		tn = _strip(self.tender)
		rt = frappe.db.get_value(EVALUATION_REPORT, rn, "tender")
		if tn and rt and _strip(rt) != tn:
			frappe.throw(
				_("Evaluation Report tender must match the Award Decision tender."),
				frappe.ValidationError,
				title=_("Report tender mismatch"),
			)

	def _validate_bid_one(self, bid_field: str, supplier_field: str, label: str) -> None:
		bn = _strip(getattr(self, bid_field, None))
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
				_("{0} must belong to the award Tender.").format(label),
				frappe.ValidationError,
				title=_("Bid tender mismatch"),
			)
		sup = _strip(getattr(self, supplier_field, None))
		if not sup:
			return
		bs_sup = frappe.db.get_value(BID_SUBMISSION, bn, "supplier")
		if bs_sup is not None and _strip(bs_sup) != sup:
			frappe.throw(
				_("{0} supplier must match the bid submission.").format(label),
				frappe.ValidationError,
				title=_("Supplier mismatch"),
			)

	def _validate_bid_links(self) -> None:
		self._validate_bid_one("recommended_bid_submission", "recommended_supplier", _("Recommended bid"))
		self._validate_bid_one("approved_bid_submission", "approved_supplier", _("Approved bid"))

	def _validate_counts(self) -> None:
		for fn in ("responsive_bid_count", "non_responsive_bid_count", "disqualified_bid_count"):
			val = getattr(self, fn, None)
			if val is None:
				continue
			try:
				n = int(val)
			except (TypeError, ValueError):
				continue
			if n < 0:
				frappe.throw(
					_("Bid counts cannot be negative."),
					frappe.ValidationError,
					title=_("Invalid bid count"),
				)

	def _validate_deviation_link(self) -> None:
		dn = _strip(self.deviation_record)
		if not dn:
			return
		if not frappe.db.exists(ADR, dn):
			frappe.throw(
				_("Award Deviation Record {0} does not exist.").format(frappe.bold(dn)),
				frappe.ValidationError,
				title=_("Invalid deviation record"),
			)
		my = _strip(self.name)
		if not my:
			return
		ad = frappe.db.get_value(ADR, dn, "award_decision")
		if ad and _strip(ad) != my:
			frappe.throw(
				_("Deviation record must reference this Award Decision."),
				frappe.ValidationError,
				title=_("Deviation mismatch"),
			)

	def _validate_standstill_link(self) -> None:
		sn = _strip(self.standstill_period)
		if not sn:
			return
		if not frappe.db.exists(SSP, sn):
			frappe.throw(
				_("Standstill Period {0} does not exist.").format(frappe.bold(sn)),
				frappe.ValidationError,
				title=_("Invalid standstill period"),
			)
		my = _strip(self.name)
		if not my:
			return
		ad = frappe.db.get_value(SSP, sn, "award_decision")
		if ad and _strip(ad) != my:
			frappe.throw(
				_("Standstill period must reference this Award Decision."),
				frappe.ValidationError,
				title=_("Standstill mismatch"),
			)

	def _validate_outcome_lines(self) -> None:
		for row in self.outcome_lines or []:
			validate_award_outcome_line_row(self, row)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.business_id), _strip(self.status) or "—")
