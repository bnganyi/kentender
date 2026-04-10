# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Opening Register — formal record of opened bids (PROC-STORY-050)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

TENDER = "Tender"
SESSION = "Bid Opening Session"
BS = "Bid Submission"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class BidOpeningRegister(Document):
	def validate(self):
		self._normalize_text()
		self._set_display_label()
		self._validate_tender()
		self._validate_session()
		self._validate_register_lines()

	def _normalize_text(self) -> None:
		self.business_id = _strip(self.business_id)
		self.register_hash = _strip(self.register_hash)
		self.remarks = _strip(self.remarks)
		if self.summary_notes and isinstance(self.summary_notes, str):
			self.summary_notes = self.summary_notes.strip()

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(self.business_id, _strip(self.tender) or "—")

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

	def _validate_session(self) -> None:
		sn = _strip(self.bid_opening_session)
		if not sn:
			return
		if not frappe.db.exists(SESSION, sn):
			frappe.throw(
				_("Bid Opening Session {0} does not exist.").format(frappe.bold(sn)),
				frappe.ValidationError,
				title=_("Invalid session"),
			)
		st = _strip(self.tender)
		st_parent = frappe.db.get_value(SESSION, sn, "tender")
		if st and st_parent and _strip(st_parent) != st:
			frappe.throw(
				_("Opening Register tender must match the linked Bid Opening Session tender."),
				frappe.ValidationError,
				title=_("Tender mismatch"),
			)

	def _validate_register_lines(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		for row in self.get("register_lines") or []:
			bn = _strip(row.get("bid_submission"))
			if not bn:
				continue
			if not frappe.db.exists(BS, bn):
				frappe.throw(
					_("Bid Submission {0} does not exist.").format(frappe.bold(bn)),
					frappe.ValidationError,
					title=_("Invalid bid submission"),
				)
			bt = frappe.db.get_value(BS, bn, "tender")
			if bt and _strip(bt) != tn:
				frappe.throw(
					_("Each register line’s bid submission must belong to the same tender as this register."),
					frappe.ValidationError,
					title=_("Line tender mismatch"),
				)
