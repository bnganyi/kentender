# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label
from kentender_strategy.services.strategic_linkage_validation import assert_procuring_department_scoped


class StrategicProgram(Document):
	def validate(self):
		self._normalize_text_fields()
		self.display_label = code_title_label(self.program_code, self.program_name)
		self._validate_unique_program_code_per_plan()
		self._validate_plan_and_entity_alignment()
		self._validate_national_objective_alignment()
		self._validate_responsible_department_scope()

	def _normalize_text_fields(self):
		for fn in ("program_code", "program_name"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_unique_program_code_per_plan(self):
		plan = (self.entity_strategic_plan or "").strip()
		code = (self.program_code or "").strip()
		if not plan or not code:
			return
		filters = {"entity_strategic_plan": plan, "program_code": code}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Strategic Program", filters, "name")
		if existing:
			frappe.throw(
				_(
					"Program Code {0} already exists for this strategic plan ({1})."
				).format(frappe.bold(code), frappe.bold(existing)),
				frappe.DuplicateEntryError,
				title=_("Duplicate program code"),
			)

	def _validate_plan_and_entity_alignment(self):
		plan_name = (self.entity_strategic_plan or "").strip()
		if not plan_name:
			return
		if not frappe.db.exists("Entity Strategic Plan", plan_name):
			frappe.throw(
				_("Entity Strategic Plan {0} does not exist.").format(frappe.bold(plan_name)),
				frappe.ValidationError,
				title=_("Invalid plan"),
			)
		plan_entity = frappe.db.get_value(
			"Entity Strategic Plan",
			plan_name,
			"procuring_entity",
		)
		ent = (self.procuring_entity or "").strip()
		if ent and plan_entity and ent != plan_entity:
			frappe.throw(
				_(
					"Procuring Entity must match the selected Entity Strategic Plan "
					"(expected {0}, got {1})."
				).format(frappe.bold(plan_entity), frappe.bold(ent)),
				frappe.ValidationError,
				title=_("Entity mismatch"),
			)
		self.procuring_entity = plan_entity

	def _validate_national_objective_alignment(self):
		plan_name = (self.entity_strategic_plan or "").strip()
		obj_name = (self.national_objective or "").strip()
		if not plan_name or not obj_name:
			return
		if not frappe.db.exists("National Objective", obj_name):
			frappe.throw(
				_("National Objective {0} does not exist.").format(frappe.bold(obj_name)),
				frappe.ValidationError,
				title=_("Invalid objective"),
			)
		plan_fw = frappe.db.get_value(
			"Entity Strategic Plan",
			plan_name,
			"primary_national_framework",
		)
		obj_fw = frappe.db.get_value("National Objective", obj_name, "national_framework")
		if plan_fw and obj_fw and plan_fw != obj_fw:
			frappe.throw(
				_(
					"National Objective must align with the plan's primary national framework "
					"(objective framework {0} vs plan {1})."
				).format(frappe.bold(obj_fw), frappe.bold(plan_fw)),
				frappe.ValidationError,
				title=_("Objective alignment"),
			)

	def _validate_responsible_department_scope(self):
		assert_procuring_department_scoped(
			self.responsible_department,
			procuring_entity=self.procuring_entity,
		)
