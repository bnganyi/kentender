# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-039: Bid Submission Event."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_LOT = "Tender Lot"
BS = "Bid Submission"
BSE = "Bid Submission Event"
BCP = "Budget Control Period"


def _cleanup_bse039():
	for row in frappe.get_all(BSE, filters={"bid_submission": ("like", "_KT_BSE039_%")}, pluck="name") or []:
		frappe.delete_doc(BSE, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BSE039_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TENDER_LOT, filters={"tender": ("like", "_KT_BSE039_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_LOT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BSE039_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BSE039_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("in", ["_KT_BSE039_PE"])})


class TestBidSubmissionEvent(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bse039)
		self.entity = _make_entity("_KT_BSE039_PE").insert()
		self.period = _bcp("_KT_BSE039_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bse039)
		super().tearDown()

	def _tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BSE039 tender",
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
			"business_id": "_KT_BSE039_B1",
			"tender": tender_name,
			"supplier": "SUP-001",
			"tender_lot_scope": "Whole Tender",
			"status": "Draft",
			"workflow_state": "Draft",
			"submission_version_no": 1,
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def _minimal_event(self, bid_name: str, **extra):
		kw = {
			"doctype": BSE,
			"bid_submission": bid_name,
			"event_type": "Submitted",
			"event_datetime": frappe.utils.now_datetime(),
			"actor_user": "Administrator",
			"event_summary": "Bid submitted",
			"event_hash": "sha256:testhash_bse039",
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_valid_insert(self):
		t = self._tender("_KT_BSE039_T1")
		bid = self._minimal_bid(t.name, business_id="_KT_BSE039_B1")
		doc = self._minimal_event(bid.name)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("Submitted", doc.display_label or "")
		self.assertIn("Bid submitted", doc.display_label or "")

	def test_invalid_bid_submission_blocked(self):
		doc = self._minimal_event("_KT_BSE039_MISSING")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_update_blocked(self):
		t = self._tender("_KT_BSE039_T2")
		bid = self._minimal_bid(t.name, business_id="_KT_BSE039_B2")
		doc = self._minimal_event(bid.name)
		doc.insert(ignore_permissions=True)
		doc.event_summary = "Changed"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_delete_blocked(self):
		t = self._tender("_KT_BSE039_T3")
		bid = self._minimal_bid(t.name, business_id="_KT_BSE039_B3")
		doc = self._minimal_event(bid.name)
		doc.insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, BSE, doc.name, force=True)

	def test_blank_event_hash_blocked(self):
		t = self._tender("_KT_BSE039_T4")
		bid = self._minimal_bid(t.name, business_id="_KT_BSE039_B4")
		doc = self._minimal_event(bid.name, event_hash="   ")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
