# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-024: Tender Lot."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_LOT = "Tender Lot"
BCP = "Budget Control Period"


def _cleanup_tlot024():
	for row in frappe.get_all(TENDER_LOT, filters={"tender": ("like", "_KT_TLOT024_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_LOT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TLOT024_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_TLOT024_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TLOT024_PE"})


class TestTenderLot(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tlot024)
		self.entity = _make_entity("_KT_TLOT024_PE").insert()
		self.period = _bcp("_KT_TLOT024_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tlot024)
		super().tearDown()

	def _tender(self, name: str, *, is_multi_lot: int = 1):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "TLOT tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"is_multi_lot": is_multi_lot,
			}
		).insert(ignore_permissions=True)

	def _lot(self, tender_name: str, lot_no: int, title: str = "Lot A"):
		return frappe.get_doc(
			{
				"doctype": TENDER_LOT,
				"tender": tender_name,
				"lot_no": lot_no,
				"lot_title": title,
				"estimated_amount": 10000,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"award_status": "Not Awarded",
			}
		).insert(ignore_permissions=True)

	def test_valid_lot_when_tender_multi_lot(self):
		t = self._tender("_KT_TLOT024_T1", is_multi_lot=1)
		lot = self._lot(t.name, 1, "Civil works")
		self.assertTrue(lot.name)
		self.assertIn("Civil", lot.display_label or "")
		self.assertIn("1", lot.display_label or "")

	def test_lot_rejected_when_tender_not_multi_lot(self):
		t = self._tender("_KT_TLOT024_T2", is_multi_lot=0)
		doc = frappe.get_doc(
			{
				"doctype": TENDER_LOT,
				"tender": t.name,
				"lot_no": 1,
				"lot_title": "Should fail",
				"estimated_amount": 100,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"award_status": "Not Awarded",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_duplicate_lot_no_same_tender_blocked(self):
		t = self._tender("_KT_TLOT024_T3", is_multi_lot=1)
		self._lot(t.name, 1, "First")
		doc2 = frappe.get_doc(
			{
				"doctype": TENDER_LOT,
				"tender": t.name,
				"lot_no": 1,
				"lot_title": "Duplicate number",
				"estimated_amount": 200,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"award_status": "Not Awarded",
			}
		)
		self.assertRaises(frappe.ValidationError, doc2.insert, ignore_permissions=True)
