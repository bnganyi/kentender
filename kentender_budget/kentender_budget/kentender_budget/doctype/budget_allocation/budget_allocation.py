# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Budget Allocation — auditable allocation transactions (BUD-011).

``allocation_amount`` is strictly positive; ``allocation_type`` describes direction
(Increase / Decrease / Transfer Out / Transfer In / Revision Apply).
Effects on ``Budget Line.allocated_amount`` are applied only via controlled services (BUD-013).
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label

BL = "Budget Line"


class BudgetAllocation(Document):
	def validate(self):
		subtitle = (self.allocation_reference or self.allocation_type or "").strip()
		self.display_label = code_title_label((self.name or "").strip(), subtitle)
		self._validate_amount_positive()
		self._sync_and_validate_line_context()

	def _validate_amount_positive(self):
		if flt(self.allocation_amount) <= 0:
			frappe.throw(
				_("Allocation amount must be greater than zero."),
				frappe.ValidationError,
				title=_("Invalid amount"),
			)

	def _sync_and_validate_line_context(self):
		line_name = (self.budget_line or "").strip()
		if not line_name:
			return
		if not frappe.db.exists(BL, line_name):
			frappe.throw(
				_("Budget Line {0} does not exist.").format(frappe.bold(line_name)),
				frappe.ValidationError,
				title=_("Invalid budget line"),
			)
		row = frappe.db.get_value(
			BL,
			line_name,
			["budget", "procuring_entity", "fiscal_year", "currency"],
			as_dict=True,
		)
		if not row:
			return
		if not (self.budget or "").strip():
			self.budget = row.budget
		elif row.budget and self.budget != row.budget:
			frappe.throw(
				_("Budget must match the selected Budget Line."),
				frappe.ValidationError,
				title=_("Mismatch"),
			)
		if not (self.procuring_entity or "").strip():
			self.procuring_entity = row.procuring_entity
		elif row.procuring_entity and self.procuring_entity != row.procuring_entity:
			frappe.throw(
				_("Procuring Entity must match the selected Budget Line."),
				frappe.ValidationError,
				title=_("Mismatch"),
			)
		if not (self.fiscal_year or "").strip():
			self.fiscal_year = row.fiscal_year
		elif row.fiscal_year and self.fiscal_year != row.fiscal_year:
			frappe.throw(
				_("Fiscal Year must match the selected Budget Line."),
				frappe.ValidationError,
				title=_("Mismatch"),
			)
		if row.currency:
			self.currency = row.currency
