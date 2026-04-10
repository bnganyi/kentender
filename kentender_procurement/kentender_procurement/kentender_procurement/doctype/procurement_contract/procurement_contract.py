# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Contract — obligation record (PROC-STORY-086). Named to avoid ERPNext CRM **Contract**."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from kentender.utils.display_label import code_title_label

AD = "Award Decision"
BS = "Bid Submission"
PPI = "Procurement Plan Item"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ProcurementContract(Document):
	def validate(self):
		self._normalize()
		self._validate_award_triangle()
		self._validate_bid()
		self._validate_plan_item()
		self._validate_dates()
		self._validate_completion()
		self._set_display_label()

	def _normalize(self) -> None:
		for fn in (
			"business_id",
			"contract_title",
			"supplier",
			"related_budget_commitment_ref",
			"lock_reason",
			"remarks",
			"generated_contract_version_hash",
			"signed_document_hash",
		):
			v = getattr(self, fn, None)
			if v and isinstance(v, str):
				setattr(self, fn, v.strip())

	def _validate_award_triangle(self) -> None:
		ad_name = _strip(self.award_decision)
		if not ad_name or not frappe.db.exists(AD, ad_name):
			frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))
		tn = _strip(self.tender)
		at = _strip(frappe.db.get_value(AD, ad_name, "tender"))
		if tn and at and tn != at:
			frappe.throw(_("Tender must match the Award Decision tender."), frappe.ValidationError)
		es = _strip(self.evaluation_session)
		aes = _strip(frappe.db.get_value(AD, ad_name, "evaluation_session"))
		if es and aes and es != aes:
			frappe.throw(_("Evaluation Session must match the Award Decision."), frappe.ValidationError)

	def _validate_bid(self) -> None:
		bn = _strip(self.approved_bid_submission)
		tn = _strip(self.tender)
		if not bn or not frappe.db.exists(BS, bn):
			frappe.throw(_("Approved Bid Submission not found."), frappe.ValidationError)
		bt = _strip(frappe.db.get_value(BS, bn, "tender"))
		if tn and bt and tn != bt:
			frappe.throw(_("Bid Submission must belong to the contract tender."), frappe.ValidationError)
		bs = _strip(frappe.db.get_value(BS, bn, "supplier"))
		sup = _strip(self.supplier)
		if bs and sup and bs != sup:
			frappe.throw(_("Supplier must match the bid submission."), frappe.ValidationError)
		ad_name = _strip(self.award_decision)
		ab = _strip(frappe.db.get_value(AD, ad_name, "approved_bid_submission"))
		rb = _strip(frappe.db.get_value(AD, ad_name, "recommended_bid_submission"))
		if ab and bn != ab:
			frappe.throw(_("Approved Bid Submission must match the Award Decision approved bid."), frappe.ValidationError)
		if not ab and rb and bn != rb:
			frappe.throw(_("Approved Bid Submission must match the Award Decision recommended bid."), frappe.ValidationError)

	def _validate_plan_item(self) -> None:
		pi = _strip(self.procurement_plan_item)
		tn = _strip(self.tender)
		if not pi:
			return
		if not frappe.db.exists(PPI, pi):
			frappe.throw(_("Procurement Plan Item not found."), frappe.ValidationError)
		pt = _strip(frappe.db.get_value(PPI, pi, "tender"))
		if tn and pt and tn != pt:
			frappe.throw(_("Procurement Plan Item must belong to the contract tender."), frappe.ValidationError)

	def _validate_dates(self) -> None:
		sd = self.contract_start_date
		ed = self.contract_end_date
		if sd and ed and getdate(ed) < getdate(sd):
			frappe.throw(_("Contract End Date cannot be before Start Date."), frappe.ValidationError)

	def _validate_completion(self) -> None:
		cp = self.completion_percent
		if cp is None:
			return
		v = flt(cp)
		if v < 0 or v > 100:
			frappe.throw(_("Completion percent must be between 0 and 100."), frappe.ValidationError)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.business_id), _strip(self.status) or "—")
