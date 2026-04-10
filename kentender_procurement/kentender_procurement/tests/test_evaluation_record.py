# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-061: Evaluation Record."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EST = "Evaluation Stage"
ER = "Evaluation Record"
BCP = "Budget Control Period"


def _cleanup_es061():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES061_%")}, pluck="name") or []:
		for row in frappe.get_all(ER, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(ER, row, force=True, ignore_permissions=True)
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES061_%")}, pluck="name") or []:
		for st in frappe.get_all(EST, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EST, st, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES061_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES061_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES061_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES061_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES061_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES061_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES061_PE"})


class TestEvaluationRecord061(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es061)
		self.entity = _make_entity("_KT_ES061_PE").insert()
		self.period = _bcp("_KT_ES061_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es061)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES061 tender",
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
		t = self._tender(f"_KT_ES061_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES061_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES061_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES061_E{suffix}")
		return t, s, r, e

	def _stage(self, evaluation_session_name: str, stage_order: int = 1, **extra):
		kw = {
			"doctype": EST,
			"evaluation_session": evaluation_session_name,
			"stage_type": "Technical Evaluation",
			"stage_order": stage_order,
			"status": "Draft",
		}
		kw.update(extra)
		return frappe.get_doc(kw)

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

	def _record(self, **kw):
		base = {
			"doctype": ER,
			"business_id": "_KT_ES061_REC",
			"evaluation_session": kw.pop("evaluation_session"),
			"evaluation_stage": kw.pop("evaluation_stage"),
			"bid_submission": kw.pop("bid_submission"),
			"evaluator_user": kw.pop("evaluator_user", frappe.session.user),
			"supplier": kw.pop("supplier"),
			"status": kw.pop("status", "Draft"),
			"pass_fail_result": kw.pop("pass_fail_result", "Pending"),
		}
		base.update(kw)
		return frappe.get_doc(base)

	def test_valid_record_create(self):
		_, _, _, e = self._minimal_chain("1")
		st = self._stage(e.name, 1).insert(ignore_permissions=True)
		b = self._bid(e.tender, "_KT_ES061_B1", "ES061-SUP-1")
		doc = self._record(
			business_id="_KT_ES061_ER1",
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES061-SUP-1",
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("Draft", doc.display_label or "")

	def test_stage_wrong_session_blocked(self):
		_, _, _, e1 = self._minimal_chain("2A")
		_, _, _, e2 = self._minimal_chain("2B")
		st2 = self._stage(e2.name, 1).insert(ignore_permissions=True)
		b = self._bid(e1.tender, "_KT_ES061_B2", "ES061-SUP-2")
		doc = self._record(
			business_id="_KT_ES061_ER2",
			evaluation_session=e1.name,
			evaluation_stage=st2.name,
			bid_submission=b.name,
			supplier="ES061-SUP-2",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_bid_wrong_tender_blocked(self):
		t_a = self._tender("_KT_ES061_T3A")
		t_b = self._tender("_KT_ES061_T3B")
		s = self._opening_session(t_a.name, "_KT_ES061_S3")
		r = self._register(t_a.name, s.name, "_KT_ES061_R3")
		e = self._evaluation_session(t_a.name, s.name, r.name, "_KT_ES061_E3")
		st = self._stage(e.name, 1).insert(ignore_permissions=True)
		b = self._bid(t_b.name, "_KT_ES061_B3", "ES061-SUP-3")
		doc = self._record(
			business_id="_KT_ES061_ER3",
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES061-SUP-3",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_supplier_mismatch_blocked(self):
		_, _, _, e = self._minimal_chain("4")
		st = self._stage(e.name, 1).insert(ignore_permissions=True)
		b = self._bid(e.tender, "_KT_ES061_B4", "ES061-SUP-4A")
		doc = self._record(
			business_id="_KT_ES061_ER4",
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES061-SUP-4B",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_duplicate_evaluator_stage_bid_blocked(self):
		_, _, _, e = self._minimal_chain("5")
		st = self._stage(e.name, 1).insert(ignore_permissions=True)
		b = self._bid(e.tender, "_KT_ES061_B5", "ES061-SUP-5")
		self._record(
			business_id="_KT_ES061_ER5A",
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES061-SUP-5",
		).insert(ignore_permissions=True)
		dup = self._record(
			business_id="_KT_ES061_ER5B",
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES061-SUP-5",
		)
		self.assertRaises(frappe.ValidationError, dup.insert, ignore_permissions=True)
