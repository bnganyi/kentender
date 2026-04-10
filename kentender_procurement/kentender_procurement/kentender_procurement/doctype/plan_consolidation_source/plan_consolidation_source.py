# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Plan Consolidation Source — auditable traceability from requisition to plan item (PROC-STORY-013)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label
from kentender_procurement.services.procurement_plan_totals import refresh_procurement_plan_totals

PPI_DOCTYPE = "Procurement Plan Item"
PR_DOCTYPE = "Purchase Requisition"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class PlanConsolidationSource(Document):
	def validate(self):
		self._sync_currency_from_item()
		self._validate_linked_amount_positive()
		self._validate_procuring_entity_alignment()
		ppi = _strip(self.procurement_plan_item)
		pr = _strip(self.purchase_requisition)
		st = _strip(self.status)
		self.display_label = code_title_label(
			ppi,
			code_title_label(pr, st),
		)

	def after_insert(self):
		self._refresh_parent_plan_totals()

	def on_update(self):
		self._refresh_parent_plan_totals()

	def on_trash(self):
		self._refresh_parent_plan_totals()

	def _refresh_parent_plan_totals(self) -> None:
		ppi = _strip(self.procurement_plan_item)
		if not ppi:
			return
		plan = frappe.db.get_value(PPI_DOCTYPE, ppi, "procurement_plan")
		if _strip(plan):
			refresh_procurement_plan_totals(_strip(plan))

	def _sync_currency_from_item(self) -> None:
		ppi = _strip(self.procurement_plan_item)
		if not ppi or not frappe.db.exists(PPI_DOCTYPE, ppi):
			return
		cur = frappe.db.get_value(PPI_DOCTYPE, ppi, "currency")
		if cur:
			self.currency = cur

	def _validate_linked_amount_positive(self) -> None:
		if flt(self.linked_amount) <= 0:
			frappe.throw(
				_("Linked Amount must be greater than zero."),
				frappe.ValidationError,
				title=_("Invalid amount"),
			)

	def _validate_procuring_entity_alignment(self) -> None:
		ppi = _strip(self.procurement_plan_item)
		pr = _strip(self.purchase_requisition)
		if not ppi or not pr:
			return
		if not frappe.db.exists(PPI_DOCTYPE, ppi) or not frappe.db.exists(PR_DOCTYPE, pr):
			return
		p_ent = _strip(frappe.db.get_value(PPI_DOCTYPE, ppi, "procuring_entity"))
		r_ent = _strip(frappe.db.get_value(PR_DOCTYPE, pr, "procuring_entity"))
		if p_ent and r_ent and p_ent != r_ent:
			frappe.throw(
				_(
					"Purchase Requisition must belong to the same Procuring Entity as the "
					"Procurement Plan Item."
				),
				frappe.ValidationError,
				title=_("Entity mismatch"),
			)
