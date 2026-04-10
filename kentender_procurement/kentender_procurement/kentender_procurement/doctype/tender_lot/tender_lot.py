# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender Lot — structured lot under a multi-lot tender (PROC-STORY-024)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

TENDER_DOCTYPE = "Tender"
DOCTYPE = "Tender Lot"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class TenderLot(Document):
	def validate(self):
		self._validate_multi_lot_parent()
		self._validate_lot_no_positive()
		self._validate_unique_lot_no_per_tender()
		lot_no = self.lot_no
		lt = _strip(self.lot_title)
		self.display_label = code_title_label(str(lot_no) if lot_no is not None else "", lt)

	def _validate_multi_lot_parent(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		if not frappe.db.exists(TENDER_DOCTYPE, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)
		multi = frappe.db.get_value(TENDER_DOCTYPE, tn, "is_multi_lot")
		if not multi:
			frappe.throw(
				_("Lots can only be added when the tender is marked as multi-lot."),
				frappe.ValidationError,
				title=_("Multi-lot required"),
			)

	def _validate_lot_no_positive(self) -> None:
		n = self.lot_no
		if n is None:
			return
		if int(n) < 1:
			frappe.throw(
				_("Lot No must be a positive integer."),
				frappe.ValidationError,
				title=_("Invalid lot number"),
			)

	def _validate_unique_lot_no_per_tender(self) -> None:
		tn = _strip(self.tender)
		n = self.lot_no
		if not tn or n is None:
			return
		filters: dict = {"tender": tn, "lot_no": int(n)}
		if _strip(self.name):
			filters["name"] = ("!=", self.name)
		others = frappe.get_all(DOCTYPE, filters=filters, pluck="name", limit=1)
		if others:
			frappe.throw(
				_("Lot No {0} already exists for this tender.").format(frappe.bold(str(n))),
				frappe.ValidationError,
				title=_("Duplicate lot"),
			)
