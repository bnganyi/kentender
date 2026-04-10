# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Contract Variation (PROC-STORY-090)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

PC = "Procurement Contract"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ProcurementContractVariation(Document):
	def validate(self):
		self._validate_contract()
		self._set_display_label()

	def _validate_contract(self) -> None:
		cn = _strip(self.procurement_contract)
		if not cn or not frappe.db.exists(PC, cn):
			frappe.throw(_("Procurement Contract not found."), frappe.ValidationError)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(
			_strip(self.business_id),
			f"v{_strip(str(self.variation_no))}" if self.variation_no is not None else "—",
		)
