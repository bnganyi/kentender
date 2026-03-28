# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class NotificationTemplate(Document):
	def validate(self):
		self._normalize_text_fields()
		self._validate_template_code_unique()

	def _normalize_text_fields(self):
		if (self.template_code or "").strip():
			self.template_code = self.template_code.strip()
		if (self.template_name or "").strip():
			self.template_name = self.template_name.strip()
		if (self.event_name or "").strip():
			self.event_name = self.event_name.strip()
		if self.subject_template is not None and str(self.subject_template).strip():
			self.subject_template = str(self.subject_template).strip()
		if self.body_template is not None and str(self.body_template).strip():
			self.body_template = str(self.body_template).strip()

	def _validate_template_code_unique(self):
		code = (self.template_code or "").strip()
		if not code:
			return
		filters = {"template_code": code}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Notification Template", filters, "name")
		if existing:
			frappe.throw(
				_("Template Code {0} is already used by {1}.").format(
					frappe.bold(code),
					frappe.bold(existing),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate template code"),
			)
