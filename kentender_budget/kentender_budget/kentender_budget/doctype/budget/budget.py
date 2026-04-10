# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from kentender.utils.display_label import code_title_label

from kentender_budget.services.budget_rollup import sum_allocated_amount_for_budget


class Budget(Document):
	def validate(self):
		self._normalize_text_fields()
		self.display_label = code_title_label(self.name, self.budget_title)
		self._validate_unique_version_per_period()
		self._validate_period_entity_alignment()
		self._validate_supersedes_budget()
		self._rollup_total_allocated_from_lines()

	def after_insert(self):
		self._demote_other_current_versions()

	def on_update(self):
		self._demote_other_current_versions()

	def _normalize_text_fields(self):
		for fn in ("budget_title", "workflow_state"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_unique_version_per_period(self):
		entity = (self.procuring_entity or "").strip()
		period = (self.budget_control_period or "").strip()
		if not entity or not period or self.version_no is None:
			return
		vn = int(self.version_no)
		filters = {
			"procuring_entity": entity,
			"budget_control_period": period,
			"version_no": vn,
		}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Budget", filters, "name")
		if existing:
			frappe.throw(
				_(
					"Version {0} already exists for this entity and budget control period ({1})."
				).format(frappe.bold(str(vn)), frappe.bold(existing)),
				frappe.DuplicateEntryError,
				title=_("Duplicate budget version"),
			)

	def _validate_period_entity_alignment(self):
		entity = (self.procuring_entity or "").strip()
		period = (self.budget_control_period or "").strip()
		if not period:
			return
		if not frappe.db.exists("Budget Control Period", period):
			frappe.throw(
				_("Budget Control Period {0} does not exist.").format(frappe.bold(period)),
				frappe.ValidationError,
				title=_("Invalid period"),
			)
		period_entity = frappe.db.get_value("Budget Control Period", period, "procuring_entity")
		if period_entity and entity and period_entity != entity:
			frappe.throw(
				_(
					"Procuring Entity must match the selected Budget Control Period "
					"(expected {0}, got {1})."
				).format(frappe.bold(period_entity), frappe.bold(entity)),
				frappe.ValidationError,
				title=_("Entity mismatch"),
			)

	def _rollup_total_allocated_from_lines(self):
		"""``total_allocated_amount`` is read-only in Desk; always derive from Budget Lines (BUD rollup)."""
		if not self.name:
			self.total_allocated_amount = 0.0
			return
		self.total_allocated_amount = sum_allocated_amount_for_budget(self.name)

	def _validate_supersedes_budget(self):
		entity = (self.procuring_entity or "").strip()
		period = (self.budget_control_period or "").strip()
		other = (self.supersedes_budget or "").strip()
		if not other:
			return
		if self.name and other == self.name:
			frappe.throw(
				_("Supersedes Budget cannot reference this same document."),
				frappe.ValidationError,
				title=_("Invalid supersession"),
			)
		if not frappe.db.exists("Budget", other):
			frappe.throw(
				_("Supersedes Budget {0} does not exist.").format(frappe.bold(other)),
				frappe.ValidationError,
				title=_("Invalid supersession"),
			)
		row = frappe.db.get_value(
			"Budget",
			other,
			["procuring_entity", "budget_control_period"],
			as_dict=True,
		)
		if not row:
			return
		if entity and row.procuring_entity and row.procuring_entity != entity:
			frappe.throw(
				_("Supersedes Budget must belong to the same procuring entity as this budget."),
				frappe.ValidationError,
				title=_("Invalid supersession"),
			)
		if period and row.budget_control_period and row.budget_control_period != period:
			frappe.throw(
				_(
					"Supersedes Budget must use the same Budget Control Period as this budget "
					"(expected {0}, got {1})."
				).format(frappe.bold(period), frappe.bold(row.budget_control_period)),
				frappe.ValidationError,
				title=_("Invalid supersession"),
			)

	def _demote_other_current_versions(self):
		if not cint(self.is_current_active_version):
			return
		ent = (self.procuring_entity or "").strip()
		period = (self.budget_control_period or "").strip()
		if not ent or not period or not self.name:
			return
		frappe.db.sql(
			"""
			UPDATE `tabBudget`
			SET `is_current_active_version` = 0
			WHERE `procuring_entity` = %s
				AND `budget_control_period` = %s
				AND `name` != %s
				AND `is_current_active_version` = 1
			""",
			(ent, period, self.name),
		)
