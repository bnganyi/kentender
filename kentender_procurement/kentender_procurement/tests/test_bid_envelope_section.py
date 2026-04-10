# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-037: Bid Envelope Section."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_LOT = "Tender Lot"
BS = "Bid Submission"
BES = "Bid Envelope Section"
BCP = "Budget Control Period"


def _cleanup_bes037():
	for bs in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BES037_%")}, pluck="name") or []:
		for row in frappe.get_all(BES, filters={"bid_submission": bs}, pluck="name") or []:
			frappe.delete_doc(BES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BES037_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TENDER_LOT, filters={"tender": ("like", "_KT_BES037_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_LOT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BES037_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BES037_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_BES037_PE"})


class TestBidEnvelopeSection(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bes037)
		self.entity = _make_entity("_KT_BES037_PE").insert()
		self.period = _bcp("_KT_BES037_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bes037)
		super().tearDown()

	def _tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BES037 tender",
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

	def _bid(self, tender_name: str, bid_id: str):
		return frappe.get_doc(
			{
				"doctype": BS,
				"business_id": bid_id,
				"tender": tender_name,
				"supplier": "SUP-1",
				"tender_lot_scope": "Whole Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)

	def test_valid_section(self):
		t = self._tender("_KT_BES037_T1")
		bs = self._bid(t.name, "_KT_BES037_B1")
		doc = frappe.get_doc(
			{
				"doctype": BES,
				"bid_submission": bs.name,
				"section_type": "Technical Proposal",
				"section_title": "Tech",
				"display_order": 1,
				"status": "Draft",
				"completion_status": "Not Started",
			}
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("Tech", doc.display_label or "")

	def test_invalid_bid_blocked(self):
		doc = frappe.get_doc(
			{
				"doctype": BES,
				"bid_submission": "_KT_BES037_NOPE",
				"section_type": "Mandatory Documents",
				"section_title": "X",
				"display_order": 0,
				"status": "Draft",
				"completion_status": "Not Started",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_lot_must_match_tender(self):
		t1 = self._tender("_KT_BES037_TA", is_multi_lot=1)
		t2 = self._tender("_KT_BES037_TB", is_multi_lot=1)
		bs = self._bid(t1.name, "_KT_BES037_B2")
		lot_on_other = frappe.get_doc(
			{
				"doctype": TENDER_LOT,
				"tender": t2.name,
				"lot_no": 1,
				"lot_title": "Other",
				"estimated_amount": 100,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"award_status": "Not Awarded",
			}
		).insert(ignore_permissions=True)
		doc = frappe.get_doc(
			{
				"doctype": BES,
				"bid_submission": bs.name,
				"section_type": "Lot Response",
				"section_title": "Lot bid",
				"lot": lot_on_other.name,
				"display_order": 1,
				"status": "Draft",
				"completion_status": "Not Started",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
