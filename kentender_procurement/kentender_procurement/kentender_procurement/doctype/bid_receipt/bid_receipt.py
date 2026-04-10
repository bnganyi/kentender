# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Receipt — acknowledgement record for final bid submission (PROC-STORY-040)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

BS = "Bid Submission"
TENDER = "Tender"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class BidReceipt(Document):
	def validate(self):
		self._normalize_text_fields()
		self._set_display_label()
		self._validate_bid_submission_exists()
		self._validate_tender_exists()
		self._validate_tender_matches_bid()
		self._validate_supplier_matches_bid()
		self._validate_issued_to_user_exists()
		self._validate_hashes()

	def _normalize_text_fields(self) -> None:
		self.business_id = _strip(self.business_id)
		self.receipt_no = _strip(self.receipt_no)
		self.supplier = _strip(self.supplier)
		self.submission_hash = _strip(self.submission_hash)
		self.receipt_hash = _strip(self.receipt_hash)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.receipt_no), _strip(self.business_id))

	def _validate_bid_submission_exists(self) -> None:
		bn = _strip(self.bid_submission)
		if not bn:
			return
		if not frappe.db.exists(BS, bn):
			frappe.throw(
				_("Bid Submission {0} does not exist.").format(frappe.bold(bn)),
				frappe.ValidationError,
				title=_("Invalid bid submission"),
			)

	def _validate_tender_exists(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		if not frappe.db.exists(TENDER, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)

	def _validate_tender_matches_bid(self) -> None:
		bn = _strip(self.bid_submission)
		tn = _strip(self.tender)
		if not bn or not tn:
			return
		bt = frappe.db.get_value(BS, bn, "tender")
		if _strip(bt) != tn:
			frappe.throw(
				_("Tender must match the linked Bid Submission."),
				frappe.ValidationError,
				title=_("Tender mismatch"),
			)

	def _validate_supplier_matches_bid(self) -> None:
		bn = _strip(self.bid_submission)
		if not bn:
			return
		bs_sup = frappe.db.get_value(BS, bn, "supplier")
		if _strip(bs_sup) != _strip(self.supplier):
			frappe.throw(
				_("Supplier must match the linked Bid Submission."),
				frappe.ValidationError,
				title=_("Supplier mismatch"),
			)

	def _validate_issued_to_user_exists(self) -> None:
		un = _strip(self.issued_to_user)
		if not un:
			return
		if not frappe.db.exists("User", un):
			frappe.throw(
				_("User {0} does not exist.").format(frappe.bold(un)),
				frappe.ValidationError,
				title=_("Invalid user"),
			)

	def _validate_hashes(self) -> None:
		if not _strip(self.submission_hash):
			frappe.throw(
				_("Submission Hash is required."),
				frappe.ValidationError,
				title=_("Invalid submission hash"),
			)
		if not _strip(self.receipt_hash):
			frappe.throw(
				_("Receipt Hash is required."),
				frappe.ValidationError,
				title=_("Invalid receipt hash"),
			)
