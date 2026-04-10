# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender Visibility Rule — who can see or access a tender (PROC-STORY-028 scaffold)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

TENDER_DOCTYPE = "Tender"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class TenderVisibilityRule(Document):
	def validate(self):
		self._normalize_text()
		self._validate_tender_exists()
		self._validate_rule_value()
		rt = _strip(self.rule_type)
		rv = _strip(self.rule_value)
		self.display_label = code_title_label(rt, rv)

	def _normalize_text(self) -> None:
		for fn in ("rule_value", "remarks"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _validate_tender_exists(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		if not frappe.db.exists(TENDER_DOCTYPE, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)

	def _validate_rule_value(self) -> None:
		if not _strip(self.rule_value):
			frappe.throw(
				_("Rule Value is required."),
				frappe.ValidationError,
				title=_("Invalid rule value"),
			)
