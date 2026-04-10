# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label
from kentender_strategy.services.strategic_linkage_validation import (
	assert_procuring_department_scoped,
	sync_strategic_sub_program_plan,
)


class StrategicSubProgram(Document):
	def validate(self):
		self._normalize_text_fields()
		self.display_label = code_title_label(self.sub_program_code, self.sub_program_name)
		self._validate_unique_sub_code_per_program()
		sync_strategic_sub_program_plan(self)
		self._validate_responsible_department_scope()

	def _normalize_text_fields(self):
		for fn in ("sub_program_code", "sub_program_name"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_unique_sub_code_per_program(self):
		prg = (self.program or "").strip()
		code = (self.sub_program_code or "").strip()
		if not prg or not code:
			return
		filters = {"program": prg, "sub_program_code": code}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Strategic Sub Program", filters, "name")
		if existing:
			frappe.throw(
				_(
					"Sub Program Code {0} already exists for this program ({1})."
				).format(frappe.bold(code), frappe.bold(existing)),
				frappe.DuplicateEntryError,
				title=_("Duplicate sub program code"),
			)

	def _validate_responsible_department_scope(self):
		assert_procuring_department_scoped(
			self.responsible_department,
			program_id=self.program,
			message=_(
				"Responsible Department must belong to the same procuring entity as the parent program."
			),
		)
