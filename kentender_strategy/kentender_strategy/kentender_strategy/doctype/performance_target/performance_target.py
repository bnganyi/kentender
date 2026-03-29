# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender_strategy.services.strategic_linkage_validation import (
	assert_procuring_department_scoped,
	sync_performance_target_hierarchy,
)


class PerformanceTarget(Document):
	def validate(self):
		self._normalize_text_fields()
		self._validate_unique_business_id()
		sync_performance_target_hierarchy(self)
		self._validate_period_dates()
		self._validate_target_values()
		self._validate_responsible_department_scope()

	def _normalize_text_fields(self):
		for fn in ("business_id", "target_title", "period_label"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_unique_business_id(self):
		bid = (self.business_id or "").strip()
		if not bid:
			return
		filters = {"business_id": bid}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Performance Target", filters, "name")
		if existing:
			frappe.throw(
				_("Business ID {0} is already used by {1}.").format(
					frappe.bold(bid),
					frappe.bold(existing),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Business ID"),
			)

	def _validate_period_dates(self):
		start = self.period_start_date
		end = self.period_end_date
		if not start or not end:
			return
		if start > end:
			frappe.throw(
				_("Period Start Date cannot be after Period End Date."),
				frappe.ValidationError,
				title=_("Invalid period"),
			)

	def _validate_target_values(self):
		mtype = (self.target_measurement_type or "").strip()
		if not mtype:
			return

		num = self.get("target_value_numeric")
		txt = (self.target_value_text or "").strip()
		pct = self.get("target_value_percent")

		if mtype == "Numeric":
			if num is None:
				frappe.throw(
					_("Set Target Value (Numeric) when measurement type is Numeric."),
					frappe.ValidationError,
					title=_("Target value"),
				)
			if txt:
				frappe.throw(
					_("Target Value (Text) must be empty when measurement type is Numeric."),
					frappe.ValidationError,
					title=_("Target value"),
				)
			if pct is not None:
				frappe.throw(
					_("Target Value (Percent) must be empty when measurement type is Numeric."),
					frappe.ValidationError,
					title=_("Target value"),
				)
		elif mtype == "Text":
			if not txt:
				frappe.throw(
					_("Set Target Value (Text) when measurement type is Text."),
					frappe.ValidationError,
					title=_("Target value"),
				)
			if num is not None:
				frappe.throw(
					_("Target Value (Numeric) must be empty when measurement type is Text."),
					frappe.ValidationError,
					title=_("Target value"),
				)
			if pct is not None:
				frappe.throw(
					_("Target Value (Percent) must be empty when measurement type is Text."),
					frappe.ValidationError,
					title=_("Target value"),
				)
		elif mtype == "Percent":
			if pct is None:
				frappe.throw(
					_("Set Target Value (Percent) when measurement type is Percent."),
					frappe.ValidationError,
					title=_("Target value"),
				)
			pv = flt(pct)
			if pv < 0 or pv > 100:
				frappe.throw(
					_("Target Value (Percent) must be between 0 and 100."),
					frappe.ValidationError,
					title=_("Target value"),
				)
			if num is not None:
				frappe.throw(
					_("Target Value (Numeric) must be empty when measurement type is Percent."),
					frappe.ValidationError,
					title=_("Target value"),
				)
			if txt:
				frappe.throw(
					_("Target Value (Text) must be empty when measurement type is Percent."),
					frappe.ValidationError,
					title=_("Target value"),
				)

	def _validate_responsible_department_scope(self):
		assert_procuring_department_scoped(self.responsible_department, program_id=self.program)
