# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Contract Deliverable (PROC-STORY-089)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

PC = "Procurement Contract"
PCM = "Procurement Contract Milestone"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ProcurementContractDeliverable(Document):
	def validate(self):
		self._validate_links()
		self._set_display_label()

	def _validate_links(self) -> None:
		cn = _strip(self.procurement_contract)
		if not cn or not frappe.db.exists(PC, cn):
			frappe.throw(_("Procurement Contract not found."), frappe.ValidationError)
		mn = _strip(self.contract_milestone)
		if not mn:
			return
		if not frappe.db.exists(PCM, mn):
			frappe.throw(_("Contract Milestone not found."), frappe.ValidationError)
		mc = _strip(frappe.db.get_value(PCM, mn, "procurement_contract"))
		if mc != cn:
			frappe.throw(_("Milestone must belong to the same contract."), frappe.ValidationError)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.deliverable_title) or "—", _strip(self.status) or "—")
