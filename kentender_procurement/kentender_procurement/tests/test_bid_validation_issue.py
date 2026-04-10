# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-042: Bid Validation Issue."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_LOT = "Tender Lot"
BS = "Bid Submission"
BVI = "Bid Validation Issue"
BCP = "Budget Control Period"


def _cleanup_bvi042():
	for bs in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BVI042_%")}, pluck="name") or []:
		for row in frappe.get_all(BVI, filters={"bid_submission": bs}, pluck="name") or []:
			frappe.delete_doc(BVI, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BVI042_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TENDER_LOT, filters={"tender": ("like", "_KT_BVI042_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_LOT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BVI042_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BVI042_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("in", ["_KT_BVI042_PE"])})


class TestBidValidationIssue(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bvi042)
		self.entity = _make_entity("_KT_BVI042_PE").insert()
		self.period = _bcp("_KT_BVI042_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bvi042)
		super().tearDown()

	def _tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BVI042 tender",
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
			"business_id": "_KT_BVI042_B1",
			"tender": tender_name,
			"supplier": "SUP-001",
			"tender_lot_scope": "Whole Tender",
			"status": "Draft",
			"workflow_state": "Draft",
			"submission_version_no": 1,
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def _minimal_issue(self, bid_name: str, severity: str, **extra):
		kw = {
			"doctype": BVI,
			"bid_submission": bid_name,
			"issue_type": "Structure",
			"severity": severity,
			"issue_message": "Missing envelope section linkage.",
			"detected_on": frappe.utils.now_datetime(),
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_valid_insert_blocking(self):
		t = self._tender("_KT_BVI042_T1")
		bid = self._minimal_bid(t.name, business_id="_KT_BVI042_B1")
		doc = self._minimal_issue(bid.name, "Blocking")
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("Blocking", doc.display_label or "")

	def test_valid_insert_warning(self):
		t = self._tender("_KT_BVI042_T2")
		bid = self._minimal_bid(t.name, business_id="_KT_BVI042_B2")
		doc = self._minimal_issue(bid.name, "Warning")
		doc.insert(ignore_permissions=True)
		self.assertIn("Warning", doc.display_label or "")

	def test_invalid_bid_submission_blocked(self):
		doc = self._minimal_issue("_KT_BVI042_MISSING", "Blocking")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_blank_issue_message_blocked(self):
		t = self._tender("_KT_BVI042_T3")
		bid = self._minimal_bid(t.name, business_id="_KT_BVI042_B3")
		doc = self._minimal_issue(bid.name, "Blocking", issue_message="  ")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_resolved_flag_sets_resolved_on(self):
		t = self._tender("_KT_BVI042_T4")
		bid = self._minimal_bid(t.name, business_id="_KT_BVI042_B4")
		doc = self._minimal_issue(bid.name, "Info")
		doc.resolved_flag = 1
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.resolved_on)

	def test_clear_resolved_flag_clears_resolution_fields(self):
		t = self._tender("_KT_BVI042_T5")
		bid = self._minimal_bid(t.name, business_id="_KT_BVI042_B5")
		doc = self._minimal_issue(bid.name, "Warning")
		doc.resolved_flag = 1
		doc.resolved_notes = "Fixed in revision 2"
		doc.insert(ignore_permissions=True)
		doc.resolved_flag = 0
		doc.save(ignore_permissions=True)
		doc.reload()
		self.assertFalse(doc.resolved_on)
		self.assertFalse(doc.resolved_notes)
