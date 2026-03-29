# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_budget.services.budget_line_scope_validation import validate_budget_line_scope_and_strategy


class BudgetLine(Document):
	def validate(self):
		self._normalize_text_fields()
		self._validate_unique_business_id()
		self._sync_and_validate_budget_context()
		self._sync_strategy_fields_from_links()
		validate_budget_line_scope_and_strategy(self)

	def _normalize_text_fields(self):
		for fn in ("business_id", "fiscal_year", "funding_source"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_unique_business_id(self):
		bid = (self.business_id or "").strip()
		if not bid:
			return
		filters = {"business_id": bid}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Budget Line", filters, "name")
		if existing:
			frappe.throw(
				_("Business ID {0} is already used by {1}.").format(
					frappe.bold(bid),
					frappe.bold(existing),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Business ID"),
			)

	def _sync_and_validate_budget_context(self):
		bud = (self.budget or "").strip()
		if not bud:
			return
		if not frappe.db.exists("Budget", bud):
			frappe.throw(
				_("Budget {0} does not exist.").format(frappe.bold(bud)),
				frappe.ValidationError,
				title=_("Invalid budget"),
			)
		row = frappe.db.get_value(
			"Budget",
			bud,
			["procuring_entity", "budget_control_period", "currency"],
			as_dict=True,
		)
		if not row:
			return
		labels = {
			"procuring_entity": _("Procuring Entity"),
			"budget_control_period": _("Budget Control Period"),
		}
		for field, expected in (
			("procuring_entity", row.procuring_entity),
			("budget_control_period", row.budget_control_period),
		):
			current = (getattr(self, field) or "").strip()
			if not current:
				setattr(self, field, expected)
			elif expected and current != expected:
				frappe.throw(
					_("{0} must match the selected Budget.").format(labels[field]),
					frappe.ValidationError,
					title=_("Budget mismatch"),
				)
		period = (self.budget_control_period or "").strip()
		if not period:
			return
		fy_bcp = frappe.db.get_value("Budget Control Period", period, "fiscal_year")
		fy_bcp = (fy_bcp or "").strip()
		fy_line = (self.fiscal_year or "").strip()
		if not fy_line:
			self.fiscal_year = fy_bcp
		elif fy_bcp and fy_line != fy_bcp:
			frappe.throw(
				_("Fiscal Year must match the Budget Control Period ({0}).").format(frappe.bold(fy_bcp)),
				frappe.ValidationError,
				title=_("Fiscal year mismatch"),
			)
		if row.currency:
			self.currency = row.currency

	def _sync_strategy_fields_from_links(self):
		ind = (self.output_indicator or "").strip()
		if ind and frappe.db.exists("Output Indicator", ind):
			row = frappe.db.get_value(
				"Output Indicator",
				ind,
				["sub_program", "program", "entity_strategic_plan"],
				as_dict=True,
			)
			if row:
				self._set_if_empty_or_equal("sub_program", row.sub_program)
				self._set_if_empty_or_equal("program", row.program)
				self._set_if_empty_or_equal("entity_strategic_plan", row.entity_strategic_plan)

		tgt = (self.performance_target or "").strip()
		if tgt and frappe.db.exists("Performance Target", tgt):
			row = frappe.db.get_value(
				"Performance Target",
				tgt,
				[
					"output_indicator",
					"sub_program",
					"program",
					"entity_strategic_plan",
				],
				as_dict=True,
			)
			if row:
				self._set_if_empty_or_equal("output_indicator", row.output_indicator)
				self._set_if_empty_or_equal("sub_program", row.sub_program)
				self._set_if_empty_or_equal("program", row.program)
				self._set_if_empty_or_equal("entity_strategic_plan", row.entity_strategic_plan)

	def _set_if_empty_or_equal(self, field: str, expected):
		if not expected:
			return
		current = (getattr(self, field) or "").strip()
		if not current:
			setattr(self, field, expected)
		elif current != expected:
			labels = {
				"sub_program": _("Sub Program"),
				"program": _("Program"),
				"entity_strategic_plan": _("Entity Strategic Plan"),
				"output_indicator": _("Output Indicator"),
			}
			frappe.throw(
				_("{0} must match the linked strategic record.").format(labels.get(field, field)),
				frappe.ValidationError,
				title=_("Strategy mismatch"),
			)
