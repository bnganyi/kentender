# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Contract Milestone (PROC-STORY-088)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from kentender.utils.display_label import code_title_label

PC = "Procurement Contract"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ProcurementContractMilestone(Document):
	def validate(self):
		self._validate_contract_dates()
		self._validate_completion()
		self._set_display_label()

	def _validate_contract_dates(self) -> None:
		cn = _strip(self.procurement_contract)
		if not cn or not frappe.db.exists(PC, cn):
			frappe.throw(_("Procurement Contract not found."), frappe.ValidationError)
		cs = frappe.db.get_value(PC, cn, "contract_start_date")
		ce = frappe.db.get_value(PC, cn, "contract_end_date")
		pd = self.planned_due_date
		if pd and cs and getdate(pd) < getdate(cs):
			frappe.throw(_("Planned due date cannot be before contract start."), frappe.ValidationError)
		if pd and ce and getdate(pd) > getdate(ce):
			frappe.throw(_("Planned due date cannot be after contract end."), frappe.ValidationError)
		ac = self.actual_completion_date
		if ac and cs and getdate(ac) < getdate(cs):
			frappe.throw(_("Actual completion cannot be before contract start."), frappe.ValidationError)
		if ac and ce and getdate(ac) > getdate(ce):
			frappe.throw(_("Actual completion cannot be after contract end."), frappe.ValidationError)

	def _validate_completion(self) -> None:
		cp = self.completion_percent
		if cp is None:
			return
		v = flt(cp)
		if v < 0 or v > 100:
			frappe.throw(_("Completion percent must be between 0 and 100."), frappe.ValidationError)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(
			_strip(self.business_id),
			_strip(self.title) or "—",
		)
