# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation Session — post-opening evaluation header (PROC-STORY-057)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
BS = "Bid Submission"
EXCEPTION_RECORD = "Exception Record"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class EvaluationSession(Document):
	def validate(self):
		self._normalize_text()
		self._set_display_label()
		self._validate_tender_and_entity()
		self._validate_opening_context()
		self._validate_exception_record()
		self._validate_recommended_bid()

	def _normalize_text(self) -> None:
		for fn in (
			"business_id",
			"related_tender_criteria_snapshot_hash",
			"committee_assignment_ref",
			"recommended_supplier",
		):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())
		if self.returned_reason and isinstance(self.returned_reason, str):
			self.returned_reason = self.returned_reason.strip()
		if self.remarks and isinstance(self.remarks, str):
			self.remarks = self.remarks.strip()

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.business_id), _strip(self.tender) or "—")

	def _validate_tender_and_entity(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		if not frappe.db.exists(TENDER, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)
		ent = _strip(self.procuring_entity)
		if not ent:
			return
		t_ent = frappe.db.get_value(TENDER, tn, "procuring_entity")
		if t_ent and _strip(t_ent) != ent:
			frappe.throw(
				_("Procuring Entity must match the selected Tender."),
				frappe.ValidationError,
				title=_("Entity mismatch"),
			)

	def _validate_opening_context(self) -> None:
		tn = _strip(self.tender)
		os_name = _strip(self.opening_session)
		or_name = _strip(self.opening_register)

		if not os_name:
			frappe.throw(
				_("Opening Session is required to link evaluation to bid opening."),
				frappe.ValidationError,
				title=_("Missing opening context"),
			)
		if not or_name:
			frappe.throw(
				_("Opening Register is required to link evaluation to opened bids."),
				frappe.ValidationError,
				title=_("Missing opening context"),
			)

		if not frappe.db.exists(BOS, os_name):
			frappe.throw(
				_("Bid Opening Session {0} does not exist.").format(frappe.bold(os_name)),
				frappe.ValidationError,
				title=_("Invalid opening session"),
			)
		session_tender = frappe.db.get_value(BOS, os_name, "tender")
		if tn and session_tender and _strip(session_tender) != tn:
			frappe.throw(
				_("Opening Session must belong to the same Tender as this Evaluation Session."),
				frappe.ValidationError,
				title=_("Opening tender mismatch"),
			)

		if not frappe.db.exists(BOR, or_name):
			frappe.throw(
				_("Bid Opening Register {0} does not exist.").format(frappe.bold(or_name)),
				frappe.ValidationError,
				title=_("Invalid opening register"),
			)
		row = frappe.db.get_value(BOR, or_name, ["tender", "bid_opening_session"], as_dict=True)
		if not row:
			return
		if tn and _strip(row.get("tender")) != tn:
			frappe.throw(
				_("Opening Register must belong to the same Tender as this Evaluation Session."),
				frappe.ValidationError,
				title=_("Register tender mismatch"),
			)
		if _strip(row.get("bid_opening_session")) != os_name:
			frappe.throw(
				_("Opening Register must be linked to the selected Opening Session."),
				frappe.ValidationError,
				title=_("Register session mismatch"),
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

	def _validate_recommended_bid(self) -> None:
		bn = _strip(self.recommended_bid_submission)
		if not bn:
			return
		if not frappe.db.exists(BS, bn):
			frappe.throw(
				_("Bid Submission {0} does not exist.").format(frappe.bold(bn)),
				frappe.ValidationError,
				title=_("Invalid bid submission"),
			)
		tn = _strip(self.tender)
		bt = frappe.db.get_value(BS, bn, "tender")
		if tn and bt and _strip(bt) != tn:
			frappe.throw(
				_("Recommended Bid Submission must belong to the same Tender as this Evaluation Session."),
				frappe.ValidationError,
				title=_("Bid tender mismatch"),
			)
