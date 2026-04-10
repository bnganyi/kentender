# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender — market-facing solicitation header (PROC-STORY-023 / EPIC-PROC-003)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime

from kentender.services.sensitivity_classification import normalize_sensitivity_class
from kentender.utils.display_label import code_title_label

PP_DOCTYPE = "Procurement Plan"
PPI_DOCTYPE = "Procurement Plan Item"
PTTL_DOCTYPE = "Plan to Tender Link"

ORIGIN_FROM_PLAN_ITEM = "From Plan Item"


class Tender(Document):
	def validate(self):
		self._normalize_key_fields()
		self.display_label = code_title_label(self.business_id, self.title)
		self._validate_sensitivity_class()
		self._validate_date_chain()
		self._validate_plan_links()
		self._validate_origin_requires_plan_item()
		self._validate_parent_tender()
		self._validate_plan_to_tender_link()
		self._validate_no_direct_publish()

	def _validate_no_direct_publish(self) -> None:
		"""Publication must go through :func:`kentender_procurement.services.tender_workflow_actions.publish_tender`."""
		ws = (self.workflow_state or "").strip()
		if ws != "Published":
			return
		if getattr(frappe.flags, "in_tender_publish_service", None):
			return
		prev = self.get_doc_before_save()
		if self.is_new() or not prev:
			frappe.throw(
				_("Tender cannot be created or saved as Published except via the publish tender service."),
				frappe.ValidationError,
				title=_("Publication blocked"),
			)
		prev_ws = (prev.get("workflow_state") or "").strip()
		if prev_ws == "Published":
			return
		frappe.throw(
			_("Workflow stage **Published** cannot be set by direct edit. Use the publish tender service."),
			frappe.ValidationError,
			title=_("Publication blocked"),
		)

	def _normalize_key_fields(self) -> None:
		for fn in ("business_id", "title", "tender_number"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _validate_sensitivity_class(self) -> None:
		raw = (self.sensitivity_class or "").strip()
		if not raw:
			return
		norm = normalize_sensitivity_class(raw)
		if norm is None:
			frappe.throw(
				_("Invalid Sensitivity Class."),
				frappe.ValidationError,
				title=_("Sensitivity"),
			)
		self.sensitivity_class = norm

	def _validate_date_chain(self) -> None:
		"""Enforce non-decreasing order for publication → clarification → submission → opening.

		Unset intermediates are skipped; only consecutive *set* milestones in this sequence
		are compared (e.g. submission vs opening when earlier fields are empty).
		"""
		labels = (
			_("Publication"),
			_("Clarification deadline"),
			_("Submission deadline"),
			_("Opening"),
		)
		fields = (
			"publication_datetime",
			"clarification_deadline",
			"submission_deadline",
			"opening_datetime",
		)
		last_label: str | None = None
		last_dt = None
		for i, fn in enumerate(fields):
			raw = getattr(self, fn, None)
			if raw is None:
				continue
			dt = get_datetime(raw)
			if dt is None:
				continue
			if last_dt is not None and last_label is not None:
				if dt < last_dt:
					frappe.throw(
						_("{0} must be on or after {1}.").format(labels[i], last_label),
						frappe.ValidationError,
						title=_("Invalid schedule"),
					)
			last_label = labels[i]
			last_dt = dt

	def _validate_plan_links(self) -> None:
		ppi = (self.procurement_plan_item or "").strip()
		pp = (self.procurement_plan or "").strip()
		if not ppi:
			return
		if not frappe.db.exists(PPI_DOCTYPE, ppi):
			frappe.throw(
				_("Procurement Plan Item {0} does not exist.").format(frappe.bold(ppi)),
				frappe.ValidationError,
				title=_("Invalid plan item"),
			)
		plan_from_item = (frappe.db.get_value(PPI_DOCTYPE, ppi, "procurement_plan") or "").strip()
		if not plan_from_item:
			frappe.throw(
				_("Procurement Plan Item has no procurement plan."),
				frappe.ValidationError,
				title=_("Invalid plan item"),
			)
		if pp and plan_from_item != pp:
			frappe.throw(
				_("Procurement Plan must match the plan item's parent plan."),
				frappe.ValidationError,
				title=_("Plan mismatch"),
			)
		if not pp:
			self.procurement_plan = plan_from_item

	def _validate_origin_requires_plan_item(self) -> None:
		if (self.origin_type or "").strip() != ORIGIN_FROM_PLAN_ITEM:
			return
		if not (self.procurement_plan_item or "").strip():
			frappe.throw(
				_("Procurement Plan Item is required when Origin Type is {0}.").format(
					frappe.bold(ORIGIN_FROM_PLAN_ITEM)
				),
				frappe.ValidationError,
				title=_("Missing plan item"),
			)
		if not (self.procurement_plan or "").strip():
			frappe.throw(
				_("Procurement Plan is required when Origin Type is {0}.").format(
					frappe.bold(ORIGIN_FROM_PLAN_ITEM)
				),
				frappe.ValidationError,
				title=_("Missing procurement plan"),
			)

	def _validate_parent_tender(self) -> None:
		pt = (self.parent_tender or "").strip()
		if not pt:
			return
		if not frappe.db.exists("Tender", pt):
			frappe.throw(
				_("Parent Tender {0} does not exist.").format(frappe.bold(pt)),
				frappe.ValidationError,
				title=_("Invalid parent"),
			)
		if self.name and pt == self.name:
			frappe.throw(
				_("Parent Tender cannot be the same document."),
				frappe.ValidationError,
				title=_("Invalid parent"),
			)

	def _validate_plan_to_tender_link(self) -> None:
		link_name = (self.plan_to_tender_link or "").strip()
		if not link_name:
			return
		if not frappe.db.exists(PTTL_DOCTYPE, link_name):
			frappe.throw(
				_("Plan to Tender Link {0} does not exist.").format(frappe.bold(link_name)),
				frappe.ValidationError,
				title=_("Invalid link"),
			)
		row = frappe.db.get_value(
			PTTL_DOCTYPE,
			link_name,
			["procurement_plan_item", "tender"],
			as_dict=True,
		)
		if not row:
			return
		ppi = (self.procurement_plan_item or "").strip()
		if ppi and (row.get("procurement_plan_item") or "").strip() != ppi:
			frappe.throw(
				_("Plan to Tender Link must reference the same Procurement Plan Item as this tender."),
				frappe.ValidationError,
				title=_("Link mismatch"),
			)
		tn = (row.get("tender") or "").strip()
		if self.name and tn and tn != self.name:
			frappe.throw(
				_("Plan to Tender Link must reference this tender."),
				frappe.ValidationError,
				title=_("Link mismatch"),
			)
