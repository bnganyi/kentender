# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Purchase Requisition — internal procurement demand header (PROC-STORY-001)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from kentender.status_model import apply_registered_summary_fields
from kentender.utils.display_label import code_title_label
from kentender.services.sensitivity_classification import normalize_sensitivity_class
from kentender_procurement.services.purchase_requisition_validation import (
	recompute_requested_amount_from_items,
	validate_minimum_items_for_submission,
	validate_purchase_requisition_budget_and_strategy,
)
from kentender_procurement.services.requisition_planning_allocation import (
	refresh_purchase_requisition_item_planning_quantities,
)
from kentender_procurement.services.requisition_planning_derivation import (
	apply_requisition_planning_derivation_to_doc,
)


class PurchaseRequisition(Document):
	def after_insert(self):
		refresh_purchase_requisition_item_planning_quantities(self.name)

	def validate(self):
		apply_registered_summary_fields(self)
		self._guard_approved_direct_edit()
		self._normalize_text_fields()
		self._sync_fields_from_budget_line()
		self.display_label = code_title_label(self.name, self.title)
		self._validate_dates()
		self._validate_emergency()
		self._validate_sensitivity_class()
		self._validate_items()
		recompute_requested_amount_from_items(self)
		validate_minimum_items_for_submission(self)
		validate_purchase_requisition_budget_and_strategy(self)
		apply_requisition_planning_derivation_to_doc(self)
		refresh_purchase_requisition_item_planning_quantities(self.name)

	def _guard_approved_direct_edit(self):
		"""Block in-place edits while workflow is already Approved (PROC-STORY-008)."""
		if self.is_new():
			return
		if frappe.flags.get("allow_approved_requisition_mutation"):
			return
		if (self.workflow_state or "").strip() != "Approved":
			return
		prev_ws = frappe.db.get_value(self.doctype, self.name, "workflow_state")
		if (prev_ws or "").strip() != "Approved":
			return
		frappe.throw(
			_(
				"This purchase requisition is already approved. Use the amendment apply service "
				"to make controlled changes."
			),
			frappe.ValidationError,
			title=_("Direct edit blocked"),
		)

	def _validate_items(self):
		# Frappe does not run child controller ``validate`` on save; call explicitly (PROC-STORY-002).
		for row in self.get("items") or []:
			row.run_method("validate")

	def _normalize_text_fields(self):
		for fn in ("title", "fiscal_year", "delivery_location"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _sync_fields_from_budget_line(self) -> None:
		"""When ``budget_line`` is set, copy budget/strategy context from the line (denormalized snapshot)."""
		bl = (self.budget_line or "").strip()
		if not bl or not frappe.db.exists("Budget Line", bl):
			return
		line = frappe.db.get_value(
			"Budget Line",
			bl,
			[
				"budget",
				"budget_control_period",
				"procuring_entity",
				"fiscal_year",
				"currency",
				"entity_strategic_plan",
				"program",
				"sub_program",
				"output_indicator",
				"performance_target",
				"funding_source",
			],
			as_dict=True,
		)
		if not line:
			return
		line_ent = (line.get("procuring_entity") or "").strip()
		pr_ent = (self.procuring_entity or "").strip()
		if line_ent and pr_ent and line_ent != pr_ent:
			frappe.throw(
				_("Budget Line belongs to a different Procuring Entity than this requisition."),
				frappe.ValidationError,
				title=_("Entity mismatch"),
			)
		self.budget = line.get("budget")
		self.budget_control_period = line.get("budget_control_period")
		self.fiscal_year = line.get("fiscal_year") or self.fiscal_year
		self.currency = line.get("currency") or self.currency
		self.entity_strategic_plan = line.get("entity_strategic_plan")
		self.program = line.get("program")
		self.sub_program = line.get("sub_program")
		self.output_indicator = line.get("output_indicator")
		self.performance_target = line.get("performance_target")
		prg = (line.get("program") or "").strip()
		if prg:
			no = frappe.db.get_value("Strategic Program", prg, "national_objective")
			if no:
				self.national_objective = no
		fs = (line.get("funding_source") or "").strip()
		if fs:
			if frappe.db.exists("Funding Source", fs):
				self.funding_source = fs
			else:
				by_name = frappe.db.get_value("Funding Source", {"funding_source_name": fs}, "name")
				if by_name:
					self.funding_source = by_name

	def _validate_dates(self):
		rd = self.request_date
		by = self.required_by_date
		if rd and by:
			if getdate(by) < getdate(rd):
				frappe.throw(
					_("Required By Date cannot be before Request Date."),
					frappe.ValidationError,
					title=_("Invalid dates"),
				)

	def _validate_emergency(self):
		if not self.is_emergency_request:
			return
		just = (self.emergency_justification or "").strip()
		if not just:
			frappe.throw(
				_("Emergency justification is required when Is Emergency Request is set."),
				frappe.ValidationError,
				title=_("Emergency request"),
			)

	def _validate_sensitivity_class(self):
		raw = self.sensitivity_class
		if not (raw or "").strip():
			return
		if normalize_sensitivity_class(raw) is None:
			frappe.throw(
				_("Sensitivity Class must be a valid canonical label."),
				frappe.ValidationError,
				title=_("Invalid sensitivity"),
			)
