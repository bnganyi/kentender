# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender Criteria — evaluation criterion under a tender (PROC-STORY-025)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label

TENDER_DOCTYPE = "Tender"
LOT_DOCTYPE = "Tender Lot"
DOCTYPE = "Tender Criteria"

SCORE_NUMERIC = "Numeric"
SCORE_PASS_FAIL = "Pass/Fail"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class TenderCriteria(Document):
	def validate(self):
		self._reject_edit_if_locked()
		self._normalize_strings()
		self.display_label = code_title_label(self.criteria_code, self.criteria_title)
		self._validate_tender()
		self._validate_lot()
		self._validate_criteria_code_unique()
		self._validate_display_order()
		self._validate_score_fields()

	def _reject_edit_if_locked(self) -> None:
		if self.is_new():
			return
		prev = frappe.db.get_value(DOCTYPE, self.name, "is_locked")
		if prev:
			frappe.throw(
				_("This criteria is locked and cannot be modified."),
				frappe.ValidationError,
				title=_("Locked"),
			)

	def _normalize_strings(self) -> None:
		for fn in ("criteria_code", "criteria_title", "description"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _validate_tender(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		if not frappe.db.exists(TENDER_DOCTYPE, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)

	def _validate_lot(self) -> None:
		ln = _strip(self.lot)
		if not ln:
			return
		if not frappe.db.exists(LOT_DOCTYPE, ln):
			frappe.throw(
				_("Tender Lot {0} does not exist.").format(frappe.bold(ln)),
				frappe.ValidationError,
				title=_("Invalid lot"),
			)
		lot_tender = frappe.db.get_value(LOT_DOCTYPE, ln, "tender")
		tn = _strip(self.tender)
		if (lot_tender or "").strip() != tn:
			frappe.throw(
				_("Lot must belong to the same tender."),
				frappe.ValidationError,
				title=_("Lot mismatch"),
			)

	def _validate_criteria_code_unique(self) -> None:
		tn = _strip(self.tender)
		code = _strip(self.criteria_code)
		if not tn or not code:
			return
		lot_key = _strip(self.lot)
		rows = frappe.get_all(
			DOCTYPE,
			filters={"tender": tn, "criteria_code": code},
			fields=["name", "lot"],
		)
		for row in rows:
			if _strip(row.get("name") or "") == _strip(self.name or ""):
				continue
			other_lot = _strip(row.get("lot") or "")
			if other_lot == lot_key:
				frappe.throw(
					_("Criteria Code {0} is already used for this tender/lot scope.").format(
						frappe.bold(code)
					),
					frappe.ValidationError,
					title=_("Duplicate criteria code"),
				)

	def _validate_display_order(self) -> None:
		n = self.display_order
		if n is None:
			return
		if int(n) < 0:
			frappe.throw(
				_("Display Order cannot be negative."),
				frappe.ValidationError,
				title=_("Invalid display order"),
			)

	def _validate_score_fields(self) -> None:
		st = _strip(self.score_type)
		wp = self.weight_percentage
		if wp is not None and (float(wp) < 0 or float(wp) > 100):
			frappe.throw(
				_("Weight Percentage must be between 0 and 100."),
				frappe.ValidationError,
				title=_("Invalid weight"),
			)

		if st == SCORE_NUMERIC:
			mx = self.max_score
			if mx is None or float(mx) <= 0:
				frappe.throw(
					_("Max Score is required and must be greater than zero for Numeric score type."),
					frappe.ValidationError,
					title=_("Invalid max score"),
				)
			max_v = float(mx)
			mp = self.minimum_pass_mark
			if mp is not None:
				v = float(mp)
				if v < 0 or v > max_v:
					frappe.throw(
						_("Minimum Pass Mark must be between 0 and Max Score."),
						frappe.ValidationError,
						title=_("Invalid pass mark"),
					)
			return

		if st == SCORE_PASS_FAIL:
			# Normalize to 1 (Pass/Fail scale); same convention as PROC-STORY-025 tests.
			self.max_score = 1.0
			mp = flt(self.minimum_pass_mark)
			if mp < 0 or mp > 1:
				frappe.throw(
					_("Minimum Pass Mark must be between 0 and 1 for Pass/Fail."),
					frappe.ValidationError,
					title=_("Invalid pass mark"),
				)
			return

		frappe.throw(
			_("Unsupported Score Type."),
			frappe.ValidationError,
			title=_("Invalid score type"),
		)
