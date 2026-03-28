# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class ExceptionRecord(Document):
	def validate(self):
		self._validate_unique_business_id()
		self._validate_justification()
		self._validate_related_reference()
		self._validate_procuring_entity()
		self._validate_effective_period()

	def _validate_unique_business_id(self):
		if not self.business_id:
			return
		filters = {"business_id": self.business_id}
		if self.name:
			filters["name"] = ("!=", self.name)
		duplicate = frappe.db.get_value("Exception Record", filters, "name")
		if duplicate:
			frappe.throw(
				_("Business ID {0} is already used by {1}.").format(
					frappe.bold(self.business_id),
					frappe.bold(duplicate),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Business ID"),
			)

	def _validate_justification(self):
		text = (self.justification or "").strip()
		if len(text) < 10:
			frappe.throw(
				_("Justification must be at least 10 characters."),
				frappe.ValidationError,
				title=_("Invalid Justification"),
			)

	def _validate_related_reference(self):
		has_dt = bool((self.related_doctype or "").strip())
		has_dn = bool((self.related_docname or "").strip())
		if has_dt != has_dn:
			frappe.throw(
				_("Related DocType and Related Document must both be set or both left empty."),
				frappe.ValidationError,
				title=_("Invalid Related Reference"),
			)
		if not has_dt:
			return
		if not frappe.db.exists(self.related_doctype, self.related_docname):
			frappe.throw(
				_("Related document {0} {1} does not exist.").format(
					frappe.bold(self.related_doctype),
					frappe.bold(self.related_docname),
				),
				frappe.ValidationError,
				title=_("Invalid Related Reference"),
			)

	def _validate_procuring_entity(self):
		if not self.procuring_entity:
			return
		if not frappe.db.exists("Procuring Entity", self.procuring_entity):
			frappe.throw(
				_("Procuring Entity {0} does not exist.").format(
					frappe.bold(self.procuring_entity)
				),
				frappe.ValidationError,
				title=_("Invalid Scope"),
			)

	def _validate_effective_period(self):
		if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
			frappe.throw(
				_("Effective To cannot be before Effective From."),
				frappe.ValidationError,
				title=_("Invalid Effective Period"),
			)
