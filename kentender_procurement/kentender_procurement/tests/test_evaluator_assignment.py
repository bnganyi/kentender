# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-059: Evaluator Assignment."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EA = "Evaluator Assignment"
BCP = "Budget Control Period"


def _ensure_es059_second_user() -> str:
	email = "_kt_es059_b@test.local"
	if frappe.db.exists("User", email):
		return email
	u = frappe.new_doc("User")
	u.email = email
	u.first_name = "ES059"
	u.send_welcome_email = 0
	u.enabled = 1
	u.user_type = "System User"
	u.insert(ignore_permissions=True)
	u.add_roles("System Manager")
	return email


def _cleanup_es059():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES059_%")}, pluck="name") or []:
		for row in frappe.get_all(EA, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EA, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES059_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES059_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES059_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES059_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES059_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES059_PE"})
	if frappe.db.exists("User", "_kt_es059_b@test.local"):
		frappe.delete_doc("User", "_kt_es059_b@test.local", force=True, ignore_permissions=True)


class TestEvaluatorAssignment059(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es059)
		self.entity = _make_entity("_KT_ES059_PE").insert()
		self.period = _bcp("_KT_ES059_BCP", self.entity.name).insert()
		self.second_user = _ensure_es059_second_user()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es059)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES059 tender",
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
		t = self._tender(f"_KT_ES059_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES059_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES059_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES059_E{suffix}")
		return t, s, r, e

	def _assignment(self, evaluation_session_name: str, evaluator_user: str | None = None, **extra):
		kw = {
			"doctype": EA,
			"evaluation_session": evaluation_session_name,
			"evaluator_user": evaluator_user or frappe.session.user,
			"committee_role": "Member",
			"assignment_status": "Active",
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_valid_assignment_create(self):
		_, _, _, e = self._minimal_chain("1")
		doc = self._assignment(e.name).insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn(frappe.session.user, doc.display_label or "")

	def test_invalid_evaluation_session_blocked(self):
		doc = self._assignment("nonexistent-es-059-xyz")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_duplicate_user_same_session_blocked(self):
		_, _, _, e = self._minimal_chain("2")
		self._assignment(e.name).insert(ignore_permissions=True)
		doc2 = self._assignment(e.name)
		self.assertRaises(frappe.ValidationError, doc2.insert, ignore_permissions=True)

	def test_withdrawn_requires_withdrawn_on(self):
		_, _, _, e = self._minimal_chain("3")
		doc = self._assignment(e.name, assignment_status="Withdrawn")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_replaced_requires_replacement_user(self):
		_, _, _, e = self._minimal_chain("4")
		doc = self._assignment(
			e.name,
			assignment_status="Replaced",
			withdrawn_on="2026-04-10 10:00:00",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_replacement_must_differ_from_evaluator(self):
		_, _, _, e = self._minimal_chain("5")
		doc = self._assignment(
			e.name,
			assignment_status="Replaced",
			withdrawn_on="2026-04-10 10:00:00",
			replacement_user=frappe.session.user,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_replaced_with_valid_replacement_ok(self):
		_, _, _, e = self._minimal_chain("6")
		doc = self._assignment(
			e.name,
			assignment_status="Replaced",
			withdrawn_on="2026-04-10 10:00:00",
			replacement_user=self.second_user,
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)
