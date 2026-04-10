# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-025: Tender Criteria."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_LOT = "Tender Lot"
TENDER_CRITERIA = "Tender Criteria"
BCP = "Budget Control Period"


def _cleanup_tcr025():
	for row in frappe.get_all(TENDER_CRITERIA, filters={"tender": ("like", "_KT_TCR025_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_CRITERIA, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TENDER_LOT, filters={"tender": ("like", "_KT_TCR025_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_LOT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TCR025_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_TCR025_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TCR025_PE"})


class TestTenderCriteria(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tcr025)
		self.entity = _make_entity("_KT_TCR025_PE").insert()
		self.period = _bcp("_KT_TCR025_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tcr025)
		super().tearDown()

	def _tender(self, name: str, *, is_multi_lot: int = 0):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "TCR tender",
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

	def _lot(self, tender_name: str, lot_no: int = 1):
		return frappe.get_doc(
			{
				"doctype": TENDER_LOT,
				"tender": tender_name,
				"lot_no": lot_no,
				"lot_title": "Lot",
				"estimated_amount": 5000,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"award_status": "Not Awarded",
			}
		).insert(ignore_permissions=True)

	def _criteria(self, **kwargs):
		base = {
			"doctype": TENDER_CRITERIA,
			"criteria_type": "Technical",
			"criteria_code": "T-01",
			"criteria_title": "Sample criterion",
			"score_type": "Numeric",
			"max_score": 100,
			"weight_percentage": 25,
			"minimum_pass_mark": 40,
			"status": "Draft",
		}
		base.update(kwargs)
		return frappe.get_doc(base)

	def test_valid_numeric_criteria(self):
		t = self._tender("_KT_TCR025_T1")
		doc = self._criteria(tender=t.name, criteria_code="N-01")
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("N-01", doc.display_label or "")

	def test_valid_pass_fail_criteria(self):
		t = self._tender("_KT_TCR025_T2")
		doc = self._criteria(
			tender=t.name,
			criteria_code="PF-01",
			score_type="Pass/Fail",
			max_score=99,
			minimum_pass_mark=0.5,
			weight_percentage=10,
		)
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.max_score, 1.0)

	def test_numeric_rejects_min_above_max(self):
		t = self._tender("_KT_TCR025_T3")
		doc = self._criteria(
			tender=t.name,
			criteria_code="BAD-01",
			max_score=10,
			minimum_pass_mark=15,
			weight_percentage=5,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_lot_tender_mismatch_blocked(self):
		t1 = self._tender("_KT_TCR025_TA", is_multi_lot=1)
		t2 = self._tender("_KT_TCR025_TB", is_multi_lot=1)
		lot_on_a = self._lot(t1.name, 1)
		doc = self._criteria(
			tender=t2.name,
			lot=lot_on_a.name,
			criteria_code="MIS-01",
			max_score=50,
			minimum_pass_mark=25,
			weight_percentage=10,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_duplicate_criteria_code_same_scope_blocked(self):
		t = self._tender("_KT_TCR025_T4")
		self._criteria(tender=t.name, criteria_code="DUP").insert(ignore_permissions=True)
		doc2 = self._criteria(tender=t.name, criteria_code="DUP", criteria_title="Second")
		self.assertRaises(frappe.ValidationError, doc2.insert, ignore_permissions=True)
