# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label
from kentender_strategy.services.national_reference_immutability import (
	enforce_active_locked_immutability,
	national_pillar_tracked_fieldnames,
)


class NationalPillar(Document):
	def validate(self):
		self._normalize_text_fields()
		self.display_label = code_title_label(self.pillar_code, self.pillar_name)
		self._validate_unique_pillar_code_per_framework()
		self._validate_display_order()
		enforce_active_locked_immutability(self, national_pillar_tracked_fieldnames())

	def _normalize_text_fields(self):
		for fn in ("pillar_code", "pillar_name"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_unique_pillar_code_per_framework(self):
		fw = (self.national_framework or "").strip()
		code = (self.pillar_code or "").strip()
		if not fw or not code:
			return
		filters = {"national_framework": fw, "pillar_code": code}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("National Pillar", filters, "name")
		if existing:
			frappe.throw(
				_(
					"Pillar Code {0} already exists for this National Framework ({1})."
				).format(frappe.bold(code), frappe.bold(existing)),
				frappe.DuplicateEntryError,
				title=_("Duplicate pillar code"),
			)

	def _validate_display_order(self):
		if self.display_order is None:
			return
		if int(self.display_order) < 0:
			frappe.throw(
				_("Display Order cannot be negative."),
				frappe.ValidationError,
				title=_("Invalid display order"),
			)
