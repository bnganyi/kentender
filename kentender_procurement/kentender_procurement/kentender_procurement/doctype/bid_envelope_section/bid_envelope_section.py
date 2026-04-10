# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Envelope Section — structural envelope for supplier bid parts (PROC-STORY-037)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from kentender.utils.display_label import code_title_label

BID_SUBMISSION = "Bid Submission"
TENDER_LOT = "Tender Lot"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class BidEnvelopeSection(Document):
	def validate(self):
		self._normalize_text()
		self._validate_bid_submission()
		self._validate_lot_alignment()
		self._validate_display_order()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("section_title", "section_hash"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _validate_bid_submission(self) -> None:
		bs = _strip(self.bid_submission)
		if not bs:
			frappe.throw(_("Bid Submission is required."), frappe.ValidationError, title=_("Missing link"))
		if not frappe.db.exists(BID_SUBMISSION, bs):
			frappe.throw(
				_("Bid Submission {0} does not exist.").format(frappe.bold(bs)),
				frappe.ValidationError,
				title=_("Invalid bid"),
			)

	def _validate_lot_alignment(self) -> None:
		ln = _strip(self.lot)
		if not ln:
			return
		if not frappe.db.exists(TENDER_LOT, ln):
			frappe.throw(
				_("Tender Lot {0} does not exist.").format(frappe.bold(ln)),
				frappe.ValidationError,
				title=_("Invalid lot"),
			)
		bs = _strip(self.bid_submission)
		tender = _strip(frappe.db.get_value(BID_SUBMISSION, bs, "tender"))
		lot_tender = _strip(frappe.db.get_value(TENDER_LOT, ln, "tender"))
		if lot_tender != tender:
			frappe.throw(
				_("Tender Lot must belong to the same tender as the bid submission."),
				frappe.ValidationError,
				title=_("Lot mismatch"),
			)

	def _validate_display_order(self) -> None:
		if cint(self.display_order) < 0:
			frappe.throw(_("Display Order cannot be negative."), frappe.ValidationError, title=_("Invalid order"))

	def _set_display_label(self) -> None:
		st = _strip(self.section_type)
		title = _strip(self.section_title)
		self.display_label = code_title_label(st, title or _("Section"))
