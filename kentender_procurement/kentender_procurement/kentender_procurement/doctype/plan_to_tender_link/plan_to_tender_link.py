# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Plan to Tender Link — traceability from plan item to tender (PROC-STORY-021)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

from kentender.utils.display_label import code_title_label
from kentender_procurement.services.plan_item_tender_eligibility import (
	get_plan_item_tender_eligibility,
)

PPI_DOCTYPE = "Procurement Plan Item"
PP_DOCTYPE = "Procurement Plan"
TENDER_DOCTYPE = "Tender"

STATUS_ACTIVE = "Active"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class PlantoTenderLink(Document):
	def validate(self):
		self._default_linked_on()
		self._validate_linked_amount_positive()
		self._validate_tender_ref()
		self._validate_entity_alignment()
		self._validate_active_eligibility()
		ppi = _strip(self.procurement_plan_item)
		tn = _strip(self.tender)
		lt = _strip(self.link_type)
		self.display_label = code_title_label(ppi, code_title_label(tn, lt))

	def _default_linked_on(self) -> None:
		if not self.linked_on:
			self.linked_on = now_datetime()

	def _validate_linked_amount_positive(self) -> None:
		if flt(self.linked_amount) <= 0:
			frappe.throw(
				_("Linked Amount must be greater than zero."),
				frappe.ValidationError,
				title=_("Invalid amount"),
			)

	def _validate_tender_ref(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			frappe.throw(
				_("Tender reference is required."),
				frappe.ValidationError,
				title=_("Missing tender"),
			)
		if not frappe.db.exists(TENDER_DOCTYPE, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)

	def _validate_entity_alignment(self) -> None:
		ppi = _strip(self.procurement_plan_item)
		if not ppi or not frappe.db.exists(PPI_DOCTYPE, ppi):
			frappe.throw(
				_("Procurement Plan Item does not exist."),
				frappe.ValidationError,
				title=_("Invalid item"),
			)
		plan = _strip(frappe.db.get_value(PPI_DOCTYPE, ppi, "procurement_plan"))
		if not plan:
			frappe.throw(
				_("Procurement Plan Item has no procurement plan."),
				frappe.ValidationError,
				title=_("Invalid item"),
			)
		p_ent = _strip(frappe.db.get_value(PPI_DOCTYPE, ppi, "procuring_entity"))
		pl_ent = _strip(frappe.db.get_value(PP_DOCTYPE, plan, "procuring_entity"))
		if p_ent and pl_ent and p_ent != pl_ent:
			frappe.throw(
				_(
					"Procurement Plan Item procuring entity must match the parent procurement plan entity."
				),
				frappe.ValidationError,
				title=_("Entity mismatch"),
			)

	def _validate_active_eligibility(self) -> None:
		if _strip(self.status) != STATUS_ACTIVE:
			return
		ppi = _strip(self.procurement_plan_item)
		info = get_plan_item_tender_eligibility(ppi)
		if not info.get("eligible"):
			reasons = info.get("reasons") or []
			detail = "; ".join(reasons) if reasons else _("Not eligible for tender linkage.")
			frappe.throw(
				_("Cannot create an Active plan-to-tender link: {0}").format(detail),
				frappe.ValidationError,
				title=_("Item not eligible"),
			)
