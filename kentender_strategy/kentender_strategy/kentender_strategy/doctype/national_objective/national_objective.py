# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label
from kentender_strategy.services.national_reference_immutability import (
	enforce_active_locked_immutability,
	national_objective_tracked_fieldnames,
)


class NationalObjective(Document):
	def validate(self):
		self._normalize_text_fields()
		self.display_label = code_title_label(self.objective_code, self.objective_name)
		self._validate_pillar_and_framework_alignment()
		self._validate_unique_objective_code_per_pillar()
		self._validate_display_order()
		enforce_active_locked_immutability(self, national_objective_tracked_fieldnames())

	def _normalize_text_fields(self):
		for fn in ("objective_code", "objective_name"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_pillar_and_framework_alignment(self):
		pillar = (self.national_pillar or "").strip()
		if not pillar:
			return
		if not frappe.db.exists("National Pillar", pillar):
			frappe.throw(
				_("National Pillar {0} does not exist.").format(frappe.bold(pillar)),
				frappe.ValidationError,
				title=_("Invalid pillar"),
			)
		fw_from_pillar = frappe.db.get_value("National Pillar", pillar, "national_framework")
		if not fw_from_pillar:
			frappe.throw(
				_("National Pillar {0} has no National Framework.").format(frappe.bold(pillar)),
				frappe.ValidationError,
				title=_("Invalid pillar"),
			)
		current_fw = (self.national_framework or "").strip()
		if current_fw and current_fw != fw_from_pillar:
			frappe.throw(
				_(
					"National Framework must match the selected pillar's framework "
					"(expected {0}, got {1})."
				).format(frappe.bold(fw_from_pillar), frappe.bold(current_fw)),
				frappe.ValidationError,
				title=_("Framework mismatch"),
			)
		self.national_framework = fw_from_pillar

	def _validate_unique_objective_code_per_pillar(self):
		pillar = (self.national_pillar or "").strip()
		code = (self.objective_code or "").strip()
		if not pillar or not code:
			return
		filters = {"national_pillar": pillar, "objective_code": code}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("National Objective", filters, "name")
		if existing:
			frappe.throw(
				_(
					"Objective Code {0} already exists for this National Pillar ({1})."
				).format(frappe.bold(code), frappe.bold(existing)),
				frappe.DuplicateEntryError,
				title=_("Duplicate objective code"),
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
