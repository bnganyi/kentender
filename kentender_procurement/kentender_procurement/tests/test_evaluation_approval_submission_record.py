# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-066: Evaluation Approval Submission Record."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
ERPT = "Evaluation Report"
EASR = "Evaluation Approval Submission Record"
BCP = "Budget Control Period"


def _cleanup_es066():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES066_%")}, pluck="name") or []:
		for row in frappe.get_all(EASR, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.db.delete(EASR, {"name": row})
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES066_%")}, pluck="name") or []:
		for row in frappe.get_all(ERPT, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(ERPT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES066_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES066_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES066_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES066_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES066_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES066_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES066_PE"})


class TestEvaluationApprovalSubmissionRecord066(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es066)
		self.entity = _make_entity("_KT_ES066_PE").insert()
		self.period = _bcp("_KT_ES066_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es066)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES066 tender",
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
		t = self._tender(f"_KT_ES066_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES066_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES066_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES066_E{suffix}")
		return t, s, r, e

	def _report(self, **kw):
		base = {
			"doctype": ERPT,
			"business_id": kw.pop("business_id"),
			"evaluation_session": kw.pop("evaluation_session"),
			"tender": kw.pop("tender"),
			"status": kw.pop("status", "Draft"),
			"responsive_bid_count": kw.pop("responsive_bid_count", 0),
			"non_responsive_bid_count": kw.pop("non_responsive_bid_count", 0),
			"disqualified_bid_count": kw.pop("disqualified_bid_count", 0),
		}
		base.update(kw)
		return frappe.get_doc(base)

	def _approval_row(self, **kw):
		base = {
			"doctype": EASR,
			"evaluation_session": kw.pop("evaluation_session"),
			"evaluation_report": kw.pop("evaluation_report"),
			"actor_user": kw.pop("actor_user", frappe.session.user),
			"actor_role": kw.pop("actor_role", "System Manager"),
			"action_type": kw.pop("action_type", "Submit"),
			"action_datetime": kw.pop("action_datetime", "2026-04-10 12:00:00"),
			"comments": kw.pop("comments", "ES066 test action"),
		}
		base.update(kw)
		return frappe.get_doc(base)

	def test_valid_create_and_linkage(self):
		t, _, _, e = self._minimal_chain("1")
		er = self._report(
			business_id="_KT_ES066_RPT1",
			evaluation_session=e.name,
			tender=t.name,
		).insert(ignore_permissions=True)
		doc = self._approval_row(
			evaluation_session=e.name,
			evaluation_report=er.name,
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertTrue(doc.display_label)
		self.assertIn("Submit", doc.display_label)

	def test_report_wrong_session_blocked(self):
		t_a, _, _, e_a = self._minimal_chain("2A")
		_, _, _, e_b = self._minimal_chain("2B")
		er = self._report(
			business_id="_KT_ES066_RPT2",
			evaluation_session=e_a.name,
			tender=t_a.name,
		).insert(ignore_permissions=True)
		doc = self._approval_row(
			evaluation_session=e_b.name,
			evaluation_report=er.name,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_append_only_update_blocked(self):
		t, _, _, e = self._minimal_chain("3")
		er = self._report(
			business_id="_KT_ES066_RPT3",
			evaluation_session=e.name,
			tender=t.name,
		).insert(ignore_permissions=True)
		rec = self._approval_row(
			evaluation_session=e.name,
			evaluation_report=er.name,
		).insert(ignore_permissions=True)
		rec.reload()
		rec.comments = "Changed after insert"
		self.assertRaises(frappe.ValidationError, rec.save)

	def test_invalid_evaluation_report_blocked(self):
		t, _, _, e = self._minimal_chain("4")
		doc = self._approval_row(
			evaluation_session=e.name,
			evaluation_report="nonexistent_es066_report_xyz",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
