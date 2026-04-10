# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-041: Bid Withdrawal Record."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_LOT = "Tender Lot"
BS = "Bid Submission"
BWR = "Bid Withdrawal Record"
BCP = "Budget Control Period"


def _cleanup_bw041():
	# Append-only records block delete_doc/on_trash; use direct DB delete for test cleanup.
	for bs in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BW041_%")}, pluck="name") or []:
		for row in frappe.get_all(BWR, filters={"bid_submission": bs}, pluck="name") or []:
			frappe.db.delete(BWR, {"name": row})
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BW041_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TENDER_LOT, filters={"tender": ("like", "_KT_BW041_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_LOT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BW041_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BW041_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("in", ["_KT_BW041_PE"])})


class TestBidWithdrawalRecord(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bw041)
		self.entity = _make_entity("_KT_BW041_PE").insert()
		self.period = _bcp("_KT_BW041_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bw041)
		super().tearDown()

	def _tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BW041 tender",
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
			"business_id": "_KT_BW041_B1",
			"tender": tender_name,
			"supplier": "SUP-001",
			"tender_lot_scope": "Whole Tender",
			"status": "Draft",
			"workflow_state": "Draft",
			"submission_version_no": 1,
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def _minimal_wdr(self, bid_name: str, **extra):
		kw = {
			"doctype": BWR,
			"bid_submission": bid_name,
			"withdrawal_datetime": frappe.utils.now_datetime(),
			"withdrawn_by_user": "Administrator",
			"reason": "Strategic withdrawal for testing",
			"status": "Withdrawn",
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_valid_insert(self):
		t = self._tender("_KT_BW041_T1")
		bid = self._minimal_bid(t.name, business_id="_KT_BW041_B1")
		doc = self._minimal_wdr(bid.name)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("Withdrawn", doc.display_label or "")

	def test_invalid_bid_submission_blocked(self):
		doc = self._minimal_wdr("_KT_BW041_MISSING")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_blank_reason_blocked(self):
		t = self._tender("_KT_BW041_T2")
		bid = self._minimal_bid(t.name, business_id="_KT_BW041_B2")
		doc = self._minimal_wdr(bid.name, reason="  ")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_update_blocked(self):
		t = self._tender("_KT_BW041_T3")
		bid = self._minimal_bid(t.name, business_id="_KT_BW041_B3")
		doc = self._minimal_wdr(bid.name)
		doc.insert(ignore_permissions=True)
		doc.reason = "Changed"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_delete_blocked(self):
		t = self._tender("_KT_BW041_T4")
		bid = self._minimal_bid(t.name, business_id="_KT_BW041_B4")
		doc = self._minimal_wdr(bid.name)
		doc.insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, BWR, doc.name, force=True)
