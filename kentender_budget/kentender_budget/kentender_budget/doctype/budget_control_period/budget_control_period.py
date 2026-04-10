# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

OPEN_STATUS = "Open"


class BudgetControlPeriod(Document):
	def validate(self):
		self._normalize_text_fields()
		self.display_label = code_title_label(self.name, self.period_label)
		self._validate_date_range()
		self._validate_single_open_per_entity_fy()

	def _normalize_text_fields(self):
		for fn in ("fiscal_year", "period_label"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_date_range(self):
		if self.start_date and self.end_date and self.end_date < self.start_date:
			frappe.throw(
				_("End Date cannot be before Start Date."),
				frappe.ValidationError,
				title=_("Invalid period"),
			)

	def _validate_single_open_per_entity_fy(self):
		if (self.status or "").strip() != OPEN_STATUS:
			return
		entity = (self.procuring_entity or "").strip()
		fy = (self.fiscal_year or "").strip()
		if not entity or not fy:
			return
		filters = {
			"procuring_entity": entity,
			"fiscal_year": fy,
			"status": OPEN_STATUS,
		}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Budget Control Period", filters, "name")
		if existing:
			frappe.throw(
				_(
					"An Open budget control period already exists for this entity and fiscal year ({0})."
				).format(frappe.bold(existing)),
				frappe.ValidationError,
				title=_("Duplicate open period"),
			)
