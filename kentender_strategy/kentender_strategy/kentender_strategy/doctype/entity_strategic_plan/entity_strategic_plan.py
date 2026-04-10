# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class EntityStrategicPlan(Document):
	def validate(self):
		self._normalize_text_fields()
		self._validate_unique_version_per_entity()
		self._validate_date_range()
		self._validate_supersession_links()

	def after_insert(self):
		self._demote_other_current_versions()

	def on_update(self):
		self._demote_other_current_versions()

	def _normalize_text_fields(self):
		for fn in ("plan_title", "plan_period_label"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())
		ws = getattr(self, "workflow_state", None)
		if ws and str(ws).strip():
			self.workflow_state = str(ws).strip()

	def _validate_unique_version_per_entity(self):
		entity = (self.procuring_entity or "").strip()
		if not entity or self.version_no is None:
			return
		vn = int(self.version_no)
		filters = {"procuring_entity": entity, "version_no": vn}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Entity Strategic Plan", filters, "name")
		if existing:
			frappe.throw(
				_(
					"Version {0} already exists for this procuring entity ({1})."
				).format(frappe.bold(str(vn)), frappe.bold(existing)),
				frappe.DuplicateEntryError,
				title=_("Duplicate plan version"),
			)

	def _validate_date_range(self):
		if self.start_date and self.end_date and self.end_date < self.start_date:
			frappe.throw(
				_("End Date cannot be before Start Date."),
				frappe.ValidationError,
				title=_("Invalid period"),
			)

	def _validate_supersession_links(self):
		entity = (self.procuring_entity or "").strip()
		for field, label in (
			("supersedes_plan", _("Supersedes Plan")),
			("superseded_by_plan", _("Superseded By Plan")),
		):
			other = (self.get(field) or "").strip()
			if not other:
				continue
			if self.name and other == self.name:
				frappe.throw(
					_("{0} cannot reference this same document.").format(label),
					frappe.ValidationError,
					title=_("Invalid supersession"),
				)
			if not frappe.db.exists("Entity Strategic Plan", other):
				frappe.throw(
					_("{0} {1} does not exist.").format(label, frappe.bold(other)),
					frappe.ValidationError,
					title=_("Invalid supersession"),
				)
			other_entity = frappe.db.get_value("Entity Strategic Plan", other, "procuring_entity")
			if other_entity and entity and other_entity != entity:
				frappe.throw(
					_(
						"{0} must belong to the same procuring entity as this plan."
					).format(label),
					frappe.ValidationError,
					title=_("Invalid supersession"),
				)

	def _demote_other_current_versions(self):
		if not cint(self.is_current_active_version):
			return
		if not (self.procuring_entity or "").strip() or not self.name:
			return
		frappe.db.sql(
			"""
			UPDATE `tabEntity Strategic Plan`
			SET `is_current_active_version` = 0
			WHERE `procuring_entity` = %s
				AND `name` != %s
				AND `is_current_active_version` = 1
			""",
			(self.procuring_entity, self.name),
		)
