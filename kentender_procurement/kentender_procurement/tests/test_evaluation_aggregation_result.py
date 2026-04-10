# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-064: Evaluation Aggregation Result."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EAR = "Evaluation Aggregation Result"
BCP = "Budget Control Period"


def _cleanup_es064():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES064_%")}, pluck="name") or []:
		for row in frappe.get_all(EAR, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EAR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES064_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES064_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES064_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES064_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES064_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES064_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES064_PE"})


class TestEvaluationAggregationResult064(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es064)
		self.entity = _make_entity("_KT_ES064_PE").insert()
		self.period = _bcp("_KT_ES064_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es064)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES064 tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _opening_session(self, tender_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": business_id,
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)

	def _register(self, tender_name: str, session_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": business_id,
				"tender": tender_name,
				"bid_opening_session": session_name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	def _evaluation_session(self, tender_name: str, bos_name: str, bor_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": ES,
				"business_id": business_id,
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
				"opening_session": bos_name,
				"opening_register": bor_name,
				"evaluation_mode": "Two Envelope",
				"conflict_clearance_status": "Pending",
			}
		).insert(ignore_permissions=True)

	def _minimal_chain(self, suffix: str):
		t = self._tender(f"_KT_ES064_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES064_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES064_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES064_E{suffix}")
		return t, s, r, e

	def _bid(self, tender_name: str, business_id: str, supplier: str):
		return frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": business_id,
				"tender": tender_name,
				"supplier": supplier,
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)

	def _aggregation(self, **kw):
		base = {
			"doctype": EAR,
			"evaluation_session": kw.pop("evaluation_session"),
			"bid_submission": kw.pop("bid_submission"),
			"supplier": kw.pop("supplier"),
			"preliminary_result": kw.pop("preliminary_result", "Pending"),
			"overall_result": kw.pop("overall_result", "Pending"),
			"calculation_status": kw.pop("calculation_status", "Pending"),
		}
		base.update(kw)
		return frappe.get_doc(base)

	def test_valid_aggregation_create(self):
		_, _, _, e = self._minimal_chain("1")
		b = self._bid(e.tender, "_KT_ES064_B1", "ES064-SUP-1")
		doc = self._aggregation(
			evaluation_session=e.name,
			bid_submission=b.name,
			supplier="ES064-SUP-1",
			technical_score_total=10.0,
			technical_score_average=5.0,
			financial_score=7.5,
			combined_score=6.25,
			calculation_status="Complete",
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertTrue(doc.display_label)
		self.assertIn("ES064-SUP-1", doc.display_label)
		self.assertIn("Complete", doc.display_label)

	def test_bid_wrong_tender_blocked(self):
		t_a = self._tender("_KT_ES064_T2A")
		t_b = self._tender("_KT_ES064_T2B")
		s = self._opening_session(t_a.name, "_KT_ES064_S2")
		r = self._register(t_a.name, s.name, "_KT_ES064_R2")
		e = self._evaluation_session(t_a.name, s.name, r.name, "_KT_ES064_E2")
		b = self._bid(t_b.name, "_KT_ES064_B2", "ES064-SUP-2")
		doc = self._aggregation(
			evaluation_session=e.name,
			bid_submission=b.name,
			supplier="ES064-SUP-2",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_supplier_mismatch_blocked(self):
		_, _, _, e = self._minimal_chain("3")
		b = self._bid(e.tender, "_KT_ES064_B3", "ES064-SUP-3")
		doc = self._aggregation(
			evaluation_session=e.name,
			bid_submission=b.name,
			supplier="Wrong Supplier",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_duplicate_session_bid_blocked(self):
		_, _, _, e = self._minimal_chain("4")
		b = self._bid(e.tender, "_KT_ES064_B4", "ES064-SUP-4")
		self._aggregation(
			evaluation_session=e.name,
			bid_submission=b.name,
			supplier="ES064-SUP-4",
		).insert(ignore_permissions=True)
		dup = self._aggregation(
			evaluation_session=e.name,
			bid_submission=b.name,
			supplier="ES064-SUP-4",
		)
		self.assertRaises(frappe.ValidationError, dup.insert, ignore_permissions=True)

	def test_ranking_position_negative_blocked(self):
		_, _, _, e = self._minimal_chain("5")
		b = self._bid(e.tender, "_KT_ES064_B5", "ES064-SUP-5")
		doc = self._aggregation(
			evaluation_session=e.name,
			bid_submission=b.name,
			supplier="ES064-SUP-5",
			ranking_position=-1,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
