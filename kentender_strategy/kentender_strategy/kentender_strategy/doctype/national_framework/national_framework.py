# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_strategy.services.national_reference_immutability import (
	enforce_active_locked_immutability,
	national_framework_tracked_fieldnames,
)


class NationalFramework(Document):
	def validate(self):
		self._normalize_text_fields()
		self._validate_unique_framework_code_version()
		self._validate_date_range()
		enforce_active_locked_immutability(self, national_framework_tracked_fieldnames())

	def _normalize_text_fields(self):
		for fn in ("framework_code", "framework_name", "version_label"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_unique_framework_code_version(self):
		code = (self.framework_code or "").strip()
		ver = (self.version_label or "").strip()
		if not code or not ver:
			return
		filters = {"framework_code": code, "version_label": ver}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("National Framework", filters, "name")
		if existing:
			frappe.throw(
				_(
					"Framework Code {0} with Version Label {1} already exists ({2})."
				).format(frappe.bold(code), frappe.bold(ver), frappe.bold(existing)),
				frappe.DuplicateEntryError,
				title=_("Duplicate framework version"),
			)

	def _validate_date_range(self):
		if self.start_date and self.end_date and self.end_date < self.start_date:
			frappe.throw(
				_("End Date cannot be before Start Date."),
				frappe.ValidationError,
				title=_("Invalid period"),
			)

