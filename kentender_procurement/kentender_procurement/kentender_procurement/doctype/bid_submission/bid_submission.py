# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Submission — supplier bid record against a tender (PROC-STORY-036 / EPIC-PROC-004)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime

from kentender.services.sensitivity_classification import normalize_sensitivity_class
from kentender.utils.display_label import code_title_label

TENDER_DOCTYPE = "Tender"
TENDER_LOT_DOCTYPE = "Tender Lot"
BID_SUBMISSION_DOCTYPE = "Bid Submission"

SCOPE_WHOLE = "Whole Tender"
SCOPE_SINGLE = "Single Lot"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class BidSubmission(Document):
	def validate(self):
		self._normalize_text()
		self._validate_submission_via_service_only()
		self._validate_withdraw_via_service_only()
		self._validate_tender()
		self._validate_supplier()
		self._validate_tender_context_fields()
		self._validate_prior_bid_submission()
		self._validate_lot_scope()
		self._validate_numeric_fields()
		self._validate_sensitivity()
		self._set_display_label()

	def _validate_submission_via_service_only(self) -> None:
		"""Final submit must use :func:`kentender_procurement.services.bid_final_submit_services.submit_bid`."""
		if getattr(frappe.flags, "in_bid_submit_service", None):
			return
		prev = self.get_doc_before_save()
		if not prev:
			if _strip(self.workflow_state) == "Submitted" or cint(self.is_final_submission) or cint(
				self.get("is_locked")
			):
				frappe.throw(
					_("Final submission must use the **Submit Bid** service, not direct edits."),
					frappe.ValidationError,
					title=_("Use submit service"),
				)
			return
		if _strip(prev.get("workflow_state")) != "Draft":
			return
		if _strip(self.workflow_state) == "Submitted":
			frappe.throw(
				_("Final submission must use the **Submit Bid** service, not direct edits."),
				frappe.ValidationError,
				title=_("Use submit service"),
			)
		if cint(self.is_final_submission) and not cint(prev.get("is_final_submission")):
			frappe.throw(
				_("Final submission must use the **Submit Bid** service, not direct edits."),
				frappe.ValidationError,
				title=_("Use submit service"),
			)
		if cint(self.get("is_locked")) and not cint(prev.get("is_locked")):
			frappe.throw(
				_("Final submission must use the **Submit Bid** service, not direct edits."),
				frappe.ValidationError,
				title=_("Use submit service"),
			)

	def _validate_withdraw_via_service_only(self) -> None:
		"""Withdrawal must use :func:`kentender_procurement.services.bid_withdraw_resubmit_services.withdraw_bid`."""
		if getattr(frappe.flags, "in_bid_withdraw_service", None):
			return
		prev = self.get_doc_before_save()
		if not prev:
			return
		if _strip(prev.get("workflow_state")) != "Submitted":
			return
		if _strip(self.workflow_state) == "Withdrawn" or _strip(self.status) == "Withdrawn":
			frappe.throw(
				_("Withdrawal must use the **Withdraw Bid** service, not direct edits."),
				frappe.ValidationError,
				title=_("Use withdraw service"),
			)

	def _normalize_text(self) -> None:
		for fn in (
			"business_id",
			"supplier",
			"submission_token",
			"receipt_no",
			"latest_receipt",
			"bid_security_reference",
			"opened_by_session",
		):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _validate_prior_bid_submission(self) -> None:
		prior = _strip(self.prior_bid_submission)
		if not prior:
			return
		if not frappe.db.exists(BID_SUBMISSION_DOCTYPE, prior):
			frappe.throw(
				_("Prior Bid Submission {0} does not exist.").format(frappe.bold(prior)),
				frappe.ValidationError,
				title=_("Invalid prior bid"),
			)
		row = frappe.db.get_value(BID_SUBMISSION_DOCTYPE, prior, ["tender", "supplier"], as_dict=True)
		if not row:
			return
		if _strip(row.get("tender")) != _strip(self.tender):
			frappe.throw(
				_("Prior bid must belong to the same tender."),
				frappe.ValidationError,
				title=_("Prior bid mismatch"),
			)
		if _strip(row.get("supplier")) != _strip(self.supplier):
			frappe.throw(
				_("Prior bid must be for the same supplier."),
				frappe.ValidationError,
				title=_("Prior bid mismatch"),
			)

	def _validate_tender(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			frappe.throw(_("Tender is required."), frappe.ValidationError, title=_("Missing tender"))
		if not frappe.db.exists(TENDER_DOCTYPE, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)

	def _validate_supplier(self) -> None:
		if not _strip(self.supplier):
			frappe.throw(_("Supplier is required."), frappe.ValidationError, title=_("Missing supplier"))

	def _validate_tender_context_fields(self) -> None:
		"""When set, market fields must match the linked Tender (no silent drift)."""
		tn = _strip(self.tender)
		row = frappe.db.get_value(
			TENDER_DOCTYPE,
			tn,
			[
				"procuring_entity",
				"procurement_method",
				"submission_deadline",
				"opening_datetime",
			],
			as_dict=True,
		)
		if not row:
			return

		def _must_match(field: str, label: str) -> None:
			doc_val = getattr(self, field, None)
			if doc_val is None or (isinstance(doc_val, str) and not doc_val.strip()):
				return
			t_val = row.get(field)
			if t_val is None or (isinstance(t_val, str) and not str(t_val).strip()):
				frappe.throw(
					_("{0} is set on the bid but missing on the tender; clear it or align the tender.").format(
						_(label),
					),
					frappe.ValidationError,
					title=_("Tender mismatch"),
				)
			if field in ("submission_deadline", "opening_datetime"):
				dt_doc = get_datetime(doc_val)
				dt_t = get_datetime(t_val)
				if dt_doc != dt_t:
					frappe.throw(
						_("{0} must match the tender.").format(_(label)),
						frappe.ValidationError,
						title=_("Tender mismatch"),
					)
				return
			if _strip(str(doc_val)) != _strip(str(t_val)):
				frappe.throw(
					_("{0} must match the tender.").format(_(label)),
					frappe.ValidationError,
					title=_("Tender mismatch"),
				)

		_must_match("procuring_entity", "Procuring Entity")
		_must_match("procurement_method", "Procurement Method")
		_must_match("submission_deadline", "Submission Deadline")
		_must_match("opening_datetime", "Opening Datetime")

	def _validate_lot_scope(self) -> None:
		scope = _strip(self.tender_lot_scope) or SCOPE_WHOLE
		lot = _strip(self.tender_lot)
		tn = _strip(self.tender)

		if scope == SCOPE_SINGLE:
			if not lot:
				frappe.throw(
					_("Tender Lot is required when scope is Single Lot."),
					frappe.ValidationError,
					title=_("Missing lot"),
				)
			if not frappe.db.exists(TENDER_LOT_DOCTYPE, lot):
				frappe.throw(
					_("Tender Lot {0} does not exist.").format(frappe.bold(lot)),
					frappe.ValidationError,
					title=_("Invalid lot"),
				)
			lot_tender = _strip(frappe.db.get_value(TENDER_LOT_DOCTYPE, lot, "tender"))
			if lot_tender != tn:
				frappe.throw(
					_("Tender Lot must belong to the selected Tender."),
					frappe.ValidationError,
					title=_("Lot mismatch"),
				)
		elif lot:
			frappe.throw(
				_("Tender Lot must be empty unless scope is Single Lot."),
				frappe.ValidationError,
				title=_("Lot not allowed"),
			)

	def _validate_numeric_fields(self) -> None:
		v = cint(self.submission_version_no)
		if v < 1:
			frappe.throw(
				_("Submission Version No must be at least 1."),
				frappe.ValidationError,
				title=_("Invalid version"),
			)
		if cint(self.lot_count) < 0 or cint(self.document_count) < 0:
			frappe.throw(_("Counts cannot be negative."), frappe.ValidationError, title=_("Invalid counts"))
		if self.quoted_total_amount is not None and flt(self.quoted_total_amount) < 0:
			frappe.throw(_("Quoted Total Amount cannot be negative."), frappe.ValidationError, title=_("Invalid amount"))

	def _validate_sensitivity(self) -> None:
		raw = _strip(self.sensitivity_class)
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

	def _set_display_label(self) -> None:
		bid = _strip(self.business_id)
		sup = _strip(self.supplier)
		self.display_label = code_title_label(bid, sup or _("Bid"))
