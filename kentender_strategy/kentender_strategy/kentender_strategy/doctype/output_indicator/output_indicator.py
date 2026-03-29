# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_strategy.services.strategic_linkage_validation import (
	assert_procuring_department_scoped,
	sync_output_indicator_hierarchy,
)


class OutputIndicator(Document):
	def validate(self):
		self._normalize_text_fields()
		self._validate_unique_business_id()
		self._validate_unique_indicator_code_per_sub_program()
		sync_output_indicator_hierarchy(self)
		self._validate_responsible_department_scope()

	def _normalize_text_fields(self):
		for fn in ("business_id", "indicator_code", "indicator_name", "unit_of_measure"):
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
		existing = frappe.db.get_value("Output Indicator", filters, "name")
		if existing:
			frappe.throw(
				_("Business ID {0} is already used by {1}.").format(
					frappe.bold(bid),
					frappe.bold(existing),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Business ID"),
			)

	def _validate_unique_indicator_code_per_sub_program(self):
		sub = (self.sub_program or "").strip()
		code = (self.indicator_code or "").strip()
		if not sub or not code:
			return
		filters = {"sub_program": sub, "indicator_code": code}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Output Indicator", filters, "name")
		if existing:
			frappe.throw(
				_(
					"Indicator Code {0} already exists for this Sub Program ({1})."
				).format(frappe.bold(code), frappe.bold(existing)),
				frappe.DuplicateEntryError,
				title=_("Duplicate indicator code"),
			)

	def _validate_responsible_department_scope(self):
		assert_procuring_department_scoped(self.responsible_department, program_id=self.program)
