# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Purchase Requisition Item — line-level demand (PROC-STORY-002)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PurchaseRequisitionItem(Document):
	def validate(self):
		self._validate_positive_amounts()
		self._set_line_total()

	def _validate_positive_amounts(self):
		q = flt(self.quantity)
		if q <= 0:
			frappe.throw(
				_("Quantity must be greater than zero."),
				frappe.ValidationError,
				title=_("Invalid quantity"),
			)
		uc = flt(self.estimated_unit_cost)
		if uc <= 0:
			frappe.throw(
				_("Estimated unit cost must be greater than zero."),
				frappe.ValidationError,
				title=_("Invalid unit cost"),
			)

	def _set_line_total(self):
		self.line_total = flt(self.quantity) * flt(self.estimated_unit_cost)
