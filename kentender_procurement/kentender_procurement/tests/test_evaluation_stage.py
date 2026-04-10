# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-058: Evaluation Stage."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EST = "Evaluation Stage"
BCP = "Budget Control Period"


def _cleanup_es058():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES058_%")}, pluck="name") or []:
		for st in frappe.get_all(EST, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EST, st, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES058_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES058_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES058_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES058_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES058_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES058_PE"})


class TestEvaluationStage058(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es058)
		self.entity = _make_entity("_KT_ES058_PE").insert()
		self.period = _bcp("_KT_ES058_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es058)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES058 tender",
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
		t = self._tender(f"_KT_ES058_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES058_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES058_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES058_E{suffix}")
		return t, s, r, e

	def _stage(self, evaluation_session_name: str, stage_order: int = 1, **extra):
		kw = {
			"doctype": EST,
			"evaluation_session": evaluation_session_name,
			"stage_type": "Preliminary Examination",
			"stage_order": stage_order,
			"status": "Draft",
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_valid_stage_create(self):
		_, _, _, e = self._minimal_chain("1")
		doc = self._stage(e.name, 1, stage_type="Technical Evaluation").insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("Technical Evaluation", doc.display_label or "")
		self.assertIn("1", doc.display_label or "")

	def test_duplicate_stage_order_same_session_blocked(self):
		_, _, _, e = self._minimal_chain("2")
		self._stage(e.name, 1).insert(ignore_permissions=True)
		doc2 = self._stage(e.name, 1, stage_type="Financial Evaluation")
		self.assertRaises(frappe.ValidationError, doc2.insert, ignore_permissions=True)

	def test_different_sessions_same_order_allowed(self):
		_, _, _, e1 = self._minimal_chain("3A")
		_, _, _, e2 = self._minimal_chain("3B")
		s1 = self._stage(e1.name, 1).insert(ignore_permissions=True)
		s2 = self._stage(e2.name, 1).insert(ignore_permissions=True)
		self.assertTrue(s1.name)
		self.assertTrue(s2.name)

	def test_invalid_evaluation_session_blocked(self):
		doc = self._stage("nonexistent-session-xyz-058", 1)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_stage_order_zero_blocked(self):
		_, _, _, e = self._minimal_chain("4")
		doc = self._stage(e.name, 0)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_completed_before_started_blocked(self):
		_, _, _, e = self._minimal_chain("5")
		doc = self._stage(
			e.name,
			1,
			started_on="2026-04-11 12:00:00",
			completed_on="2026-04-10 12:00:00",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
