# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-040: Bid Receipt."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_LOT = "Tender Lot"
BS = "Bid Submission"
BR = "Bid Receipt"
BCP = "Budget Control Period"


def _cleanup_br040():
	for row in frappe.get_all(BR, filters={"business_id": ("like", "_KT_BR040_%")}, pluck="name") or []:
		frappe.delete_doc(BR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BR040_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TENDER_LOT, filters={"tender": ("like", "_KT_BR040_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_LOT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BR040_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BR040_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("in", ["_KT_BR040_PE"])})


class TestBidReceipt(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_br040)
		self.entity = _make_entity("_KT_BR040_PE").insert()
		self.period = _bcp("_KT_BR040_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_br040)
		super().tearDown()

	def _tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BR040 tender",
			"tender_number": f"{name}-TN",
			"workflow_state": "Draft",
			"status": "Draft",
			"approval_status": "Draft",
			"origin_type": "Manual",
			"procuring_entity": self.entity.name,
			"currency": self.currency,
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def _minimal_bid(self, tender_name: str, **extra):
		kw = {
			"doctype": BS,
			"business_id": "_KT_BR040_B1",
			"tender": tender_name,
			"supplier": "MG-SUP-01",
			"tender_lot_scope": "Whole Tender",
			"status": "Draft",
			"workflow_state": "Draft",
			"submission_version_no": 1,
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def _minimal_receipt(self, bid_name: str, tender_name: str, **extra):
		now = frappe.utils.now_datetime()
		kw = {
			"doctype": BR,
			"business_id": "_KT_BR040_RC1",
			"receipt_no": "RCPT-BR040-001",
			"bid_submission": bid_name,
			"tender": tender_name,
			"supplier": "MG-SUP-01",
			"issued_on": now,
			"submission_timestamp": now,
			"submission_hash": "sha256:sub_br040",
			"receipt_hash": "sha256:rec_br040",
			"issued_to_user": "Administrator",
			"status": "Issued",
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_valid_insert(self):
		t = self._tender("_KT_BR040_T1")
		bid = self._minimal_bid(t.name, business_id="_KT_BR040_B1")
		doc = self._minimal_receipt(bid.name, t.name)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("RCPT-BR040-001", doc.display_label or "")

	def test_invalid_bid_submission_blocked(self):
		t = self._tender("_KT_BR040_T2")
		doc = self._minimal_receipt("_KT_BR040_MISSING", t.name)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_tender_mismatch_blocked(self):
		t = self._tender("_KT_BR040_T3")
		t2 = self._tender("_KT_BR040_T3B")
		bid = self._minimal_bid(t.name, business_id="_KT_BR040_B2")
		doc = self._minimal_receipt(bid.name, t2.name)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_supplier_mismatch_blocked(self):
		t = self._tender("_KT_BR040_T4")
		bid = self._minimal_bid(t.name, business_id="_KT_BR040_B3")
		doc = self._minimal_receipt(bid.name, t.name, supplier="OTHER-SUP")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_blank_submission_hash_blocked(self):
		t = self._tender("_KT_BR040_T5")
		bid = self._minimal_bid(t.name, business_id="_KT_BR040_B4")
		doc = self._minimal_receipt(bid.name, t.name, submission_hash="   ")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_blank_receipt_hash_blocked(self):
		t = self._tender("_KT_BR040_T6")
		bid = self._minimal_bid(t.name, business_id="_KT_BR040_B5")
		doc = self._minimal_receipt(bid.name, t.name, receipt_hash="  ")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
