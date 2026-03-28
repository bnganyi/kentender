# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class KenTenderAssignment(Document):
	def validate(self):
		self._validate_target_reference()
		self._validate_procuring_entity()
		self._validate_validity_period()

	def _validate_target_reference(self):
		dt = (self.target_doctype or "").strip()
		dn = (self.target_docname or "").strip()
		if not dt or not dn:
			frappe.throw(
				_("Target DocType and Target Document are required."),
				frappe.ValidationError,
				title=_("Invalid target"),
			)
		if not frappe.db.exists(dt, dn):
			frappe.throw(
				_("Target document {0} {1} does not exist.").format(
					frappe.bold(dt),
					frappe.bold(dn),
				),
				frappe.ValidationError,
				title=_("Invalid target"),
			)

	def _validate_procuring_entity(self):
		if not self.procuring_entity:
			return
		if not frappe.db.exists("Procuring Entity", self.procuring_entity):
			frappe.throw(
				_("Procuring Entity {0} does not exist.").format(
					frappe.bold(self.procuring_entity),
				),
				frappe.ValidationError,
				title=_("Invalid scope"),
			)

	def _validate_validity_period(self):
		if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
			frappe.throw(
				_("Valid To cannot be before Valid From."),
				frappe.ValidationError,
				title=_("Invalid validity period"),
			)
