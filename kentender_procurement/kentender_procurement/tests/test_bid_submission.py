# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-036: Bid Submission."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_LOT = "Tender Lot"
BS = "Bid Submission"
BCP = "Budget Control Period"


def _cleanup_bs036():
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BS036_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TENDER_LOT, filters={"tender": ("like", "_KT_BS036_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_LOT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BS036_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BS036_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("in", ["_KT_BS036_PE", "_KT_BS036_PE2"])})


class TestBidSubmission(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bs036)
		self.entity = _make_entity("_KT_BS036_PE").insert()
		self.period = _bcp("_KT_BS036_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bs036)
		super().tearDown()

	def _tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BS036 tender",
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
			"business_id": "_KT_BS036_B1",
			"tender": tender_name,
			"supplier": "SUP-001",
			"tender_lot_scope": "Whole Tender",
			"status": "Draft",
			"workflow_state": "Draft",
			"submission_version_no": 1,
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_valid_create(self):
		t = self._tender("_KT_BS036_T1")
		doc = self._minimal_bid(t.name, business_id="_KT_BS036_B1")
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("_KT_BS036_B1", doc.display_label or "")
		self.assertIn("SUP-001", doc.display_label or "")

	def test_invalid_tender_blocked(self):
		doc = self._minimal_bid("_KT_BS036_MISSING", business_id="_KT_BS036_B2")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_blank_supplier_blocked(self):
		t = self._tender("_KT_BS036_T2")
		doc = self._minimal_bid(t.name, business_id="_KT_BS036_B3", supplier="  ")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_invalid_sensitivity_blocked(self):
		t = self._tender("_KT_BS036_T3")
		doc = self._minimal_bid(t.name, business_id="_KT_BS036_B4", sensitivity_class="Ultra Secret")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_procuring_entity_must_match_tender_when_set(self):
		t = self._tender("_KT_BS036_T4")
		other = _make_entity("_KT_BS036_PE2").insert()
		doc = self._minimal_bid(
			t.name,
			business_id="_KT_BS036_B5",
			procuring_entity=other.name,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_single_lot_requires_tender_lot(self):
		t = self._tender("_KT_BS036_T5", is_multi_lot=1)
		doc = self._minimal_bid(
			t.name,
			business_id="_KT_BS036_B6",
			tender_lot_scope="Single Lot",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_whole_tender_rejects_tender_lot(self):
		t = self._tender("_KT_BS036_T6", is_multi_lot=1)
		lot = frappe.get_doc(
			{
				"doctype": TENDER_LOT,
				"tender": t.name,
				"lot_no": 1,
				"lot_title": "L1",
				"estimated_amount": 100,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"award_status": "Not Awarded",
			}
		).insert(ignore_permissions=True)
		doc = self._minimal_bid(
			t.name,
			business_id="_KT_BS036_B7",
			tender_lot=lot.name,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_single_lot_with_matching_lot_ok(self):
		t = self._tender("_KT_BS036_T7", is_multi_lot=1)
		lot = frappe.get_doc(
			{
				"doctype": TENDER_LOT,
				"tender": t.name,
				"lot_no": 1,
				"lot_title": "L1",
				"estimated_amount": 100,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"award_status": "Not Awarded",
			}
		).insert(ignore_permissions=True)
		doc = self._minimal_bid(
			t.name,
			business_id="_KT_BS036_B8",
			tender_lot_scope="Single Lot",
			tender_lot=lot.name,
		)
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.tender_lot, lot.name)
