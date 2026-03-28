# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


# Class name = DocType with spaces removed (Frappe get_controller).
class WorkflowGuardRule(Document):
	def validate(self):
		self._normalize_text_fields()
		self._validate_rule_code_unique()
		self._validate_evaluation_order_non_negative()
		self._validate_evaluation_order_unique_per_scope()

	def _normalize_text_fields(self):
		if (self.rule_code or "").strip():
			self.rule_code = self.rule_code.strip()
		if (self.rule_name or "").strip():
			self.rule_name = self.rule_name.strip()
		if (self.event_name or "").strip():
			self.event_name = self.event_name.strip()

	def _validate_rule_code_unique(self):
		code = (self.rule_code or "").strip()
		if not code:
			return
		filters = {"rule_code": code}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Workflow Guard Rule", filters, "name")
		if existing:
			frappe.throw(
				_("Rule Code {0} is already used by {1}.").format(
					frappe.bold(code),
					frappe.bold(existing),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate rule code"),
			)

	def _validate_evaluation_order_non_negative(self):
		if self.evaluation_order is None:
			return
		if int(self.evaluation_order) < 0:
			frappe.throw(
				_("Evaluation Order cannot be negative."),
				frappe.ValidationError,
				title=_("Invalid evaluation order"),
			)

	def _validate_evaluation_order_unique_per_scope(self):
		dt = (self.applies_to_doctype or "").strip()
		ev = (self.event_name or "").strip()
		if not dt or not ev or self.evaluation_order is None:
			return
		order = int(self.evaluation_order)
		filters = {
			"applies_to_doctype": dt,
			"event_name": ev,
			"evaluation_order": order,
		}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Workflow Guard Rule", filters, "name")
		if existing:
			frappe.throw(
				_(
					"Evaluation Order {0} is already used for {1} / {2} by rule {3}."
				).format(
					frappe.bold(str(order)),
					frappe.bold(dt),
					frappe.bold(ev),
					frappe.bold(existing),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate evaluation order"),
			)
