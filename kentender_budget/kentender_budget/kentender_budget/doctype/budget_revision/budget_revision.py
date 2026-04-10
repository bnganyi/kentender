# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Budget Revision — formal envelope changes (BUD-012). Apply via budget_revision_apply (BUD-013)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label

BL = "Budget Line"
BUD = "Budget"


class BudgetRevision(Document):
	def validate(self):
		self.display_label = code_title_label(
			(self.name or "").strip(),
			(self.revision_type or "").strip(),
		)
		self._validate_budget_header()
		self._validate_lines()

	def _validate_budget_header(self):
		bud = (self.budget or "").strip()
		if not bud or not frappe.db.exists(BUD, bud):
			return
		row = frappe.db.get_value(
			BUD,
			bud,
			["procuring_entity", "budget_control_period"],
			as_dict=True,
		)
		if not row:
			return
		ent = (self.procuring_entity or "").strip()
		if not ent:
			self.procuring_entity = row.procuring_entity
		elif row.procuring_entity and ent != row.procuring_entity:
			frappe.throw(
				_("Procuring Entity must match the selected Budget."),
				frappe.ValidationError,
				title=_("Mismatch"),
			)
		period = (self.budget_control_period or "").strip()
		if not period and row.budget_control_period:
			self.budget_control_period = row.budget_control_period
		elif period and row.budget_control_period and period != row.budget_control_period:
			frappe.throw(
				_("Budget Control Period must match the selected Budget."),
				frappe.ValidationError,
				title=_("Mismatch"),
			)

	def _validate_lines(self):
		bud = (self.budget or "").strip()
		ent = (self.procuring_entity or "").strip()
		if not self.lines:
			frappe.throw(_("At least one revision line is required."), frappe.ValidationError)
		for row in self.lines:
			self._validate_one_line(row, bud, ent)

	def _validate_one_line(self, row, budget_name: str, entity_name: str):
		amt = flt(row.change_amount)
		if amt <= 0:
			frappe.throw(
				_("Change amount must be greater than zero."),
				frappe.ValidationError,
				title=_("Invalid line"),
			)
		ct = (row.change_type or "").strip()
		src = (row.source_budget_line or "").strip()
		tgt = (row.target_budget_line or "").strip()
		if ct == "Increase":
			if not tgt or src:
				frappe.throw(
					_("Increase requires target budget line only."),
					frappe.ValidationError,
					title=_("Invalid line"),
				)
			self._line_belongs_to_budget(tgt, budget_name, entity_name)
		elif ct == "Decrease":
			if not src or tgt:
				frappe.throw(
					_("Decrease requires source budget line only."),
					frappe.ValidationError,
					title=_("Invalid line"),
				)
			self._line_belongs_to_budget(src, budget_name, entity_name)
		elif ct == "Transfer":
			if not src or not tgt or src == tgt:
				frappe.throw(
					_("Transfer requires two distinct budget lines."),
					frappe.ValidationError,
					title=_("Invalid line"),
				)
			self._line_belongs_to_budget(src, budget_name, entity_name)
			self._line_belongs_to_budget(tgt, budget_name, entity_name)
		else:
			frappe.throw(_("Unknown change type."), frappe.ValidationError)

	def _line_belongs_to_budget(self, line_name: str, budget_name: str, entity_name: str):
		if not frappe.db.exists(BL, line_name):
			frappe.throw(
				_("Budget Line {0} does not exist.").format(frappe.bold(line_name)),
				frappe.ValidationError,
			)
		row = frappe.db.get_value(
			BL,
			line_name,
			["budget", "procuring_entity"],
			as_dict=True,
		)
		if row.budget != budget_name:
			frappe.throw(
				_("Budget Line {0} does not belong to this budget.").format(frappe.bold(line_name)),
				frappe.ValidationError,
				title=_("Invalid line"),
			)
		if entity_name and row.procuring_entity != entity_name:
			frappe.throw(
				_("Budget Line {0} does not belong to this procuring entity.").format(
					frappe.bold(line_name)
				),
				frappe.ValidationError,
				title=_("Invalid line"),
			)
