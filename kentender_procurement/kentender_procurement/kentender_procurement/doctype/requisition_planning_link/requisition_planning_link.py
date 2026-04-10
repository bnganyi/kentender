# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Requisition Planning Link — traceability to procurement plan (PROC-STORY-009)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label
from kentender_procurement.services.procurement_plan_totals import (
	procurement_plans_affected_by_rpl,
	refresh_procurement_plan_totals,
)
from kentender_procurement.services.requisition_planning_allocation import (
	refresh_purchase_requisition_item_planning_quantities,
	validate_requisition_planning_link_allocation,
)
from kentender_procurement.services.requisition_planning_derivation import (
	refresh_requisition_planning_derived_fields,
)


class RequisitionPlanningLink(Document):
	def validate(self):
		self.display_label = code_title_label(
			(self.purchase_requisition or "").strip(),
			(self.status or "").strip(),
		)
		validate_requisition_planning_link_allocation(self)
		if flt(self.linked_amount) <= 0:
			frappe.throw(
				_("Linked Amount must be greater than zero."),
				frappe.ValidationError,
				title=_("Invalid amount"),
			)

	def on_update(self):
		self._sync_parent()

	def after_insert(self):
		self._sync_parent()

	def on_trash(self):
		pr = (self.purchase_requisition or "").strip()
		if pr:
			refresh_requisition_planning_derived_fields(pr, exclude_planning_link=self.name)
			refresh_purchase_requisition_item_planning_quantities(pr)
		for plan_name in procurement_plans_affected_by_rpl(self):
			refresh_procurement_plan_totals(plan_name)

	def _sync_parent(self):
		pr = (self.purchase_requisition or "").strip()
		if pr:
			refresh_requisition_planning_derived_fields(pr)
			refresh_purchase_requisition_item_planning_quantities(pr)
		for plan_name in procurement_plans_affected_by_rpl(self):
			refresh_procurement_plan_totals(plan_name)
