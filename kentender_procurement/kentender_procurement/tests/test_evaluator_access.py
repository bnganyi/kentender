# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-068: Evaluator access and conflict declaration service."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_procurement.services.evaluator_access import (
	submit_conflict_declaration,
	validate_evaluator_access,
)

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EA = "Evaluator Assignment"
COI = "Conflict of Interest Declaration"
BCP = "Budget Control Period"


def _cleanup_es068():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES068_%")}, pluck="name") or []:
		for row in frappe.get_all(COI, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(COI, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(EA, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EA, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES068_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES068_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES068_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES068_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES068_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES068_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES068_PE"})


class TestEvaluatorAccess068(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es068)
		self.entity = _make_entity("_KT_ES068_PE").insert()
		self.period = _bcp("_KT_ES068_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es068)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES068 tender",
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
		t = self._tender(f"_KT_ES068_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES068_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES068_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES068_E{suffix}")
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
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def test_validate_access_allowed_no_conflict(self):
		_, _, _, e = self._minimal_chain("1")
		self._assignment(e.name)
		submit_conflict_declaration(
			e.name,
			frappe.session.user,
			declaration_status="Declared No Conflict",
		)
		out = validate_evaluator_access(e.name, frappe.session.user)
		self.assertTrue(out.get("ok"))
		self.assertIn("evaluator_assignment", out)
		self.assertIn("conflict_declaration", out)

	def test_validate_access_denied_not_assigned(self):
		_, _, _, e = self._minimal_chain("2")
		frappe.get_doc(
			{
				"doctype": COI,
				"evaluation_session": e.name,
				"evaluator_user": frappe.session.user,
				"declaration_status": "Declared No Conflict",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError) as ctx:
			validate_evaluator_access(e.name, frappe.session.user)
		self.assertIn("actively assigned", str(ctx.exception).lower())

	def test_validate_access_denied_pending_declaration(self):
		_, _, _, e = self._minimal_chain("3")
		self._assignment(e.name)
		frappe.get_doc(
			{
				"doctype": COI,
				"evaluation_session": e.name,
				"evaluator_user": frappe.session.user,
				"declaration_status": "Pending",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError) as ctx:
			validate_evaluator_access(e.name, frappe.session.user)
		self.assertIn("access", str(ctx.exception).lower())

	def test_validate_access_denied_rejected(self):
		_, _, _, e = self._minimal_chain("4")
		self._assignment(e.name)
		frappe.get_doc(
			{
				"doctype": COI,
				"evaluation_session": e.name,
				"evaluator_user": frappe.session.user,
				"declaration_status": "Rejected from Participation",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			validate_evaluator_access(e.name, frappe.session.user)

	def test_submit_conflict_declaration_upserts(self):
		_, _, _, e = self._minimal_chain("5")
		self._assignment(e.name)
		r1 = submit_conflict_declaration(
			e.name,
			frappe.session.user,
			declaration_status="Pending",
		)
		r2 = submit_conflict_declaration(
			e.name,
			frappe.session.user,
			declaration_status="Declared No Conflict",
			conflict_summary="updated",
		)
		self.assertEqual(r1["name"], r2["name"])
		rows = frappe.get_all(
			COI,
			filters={"evaluation_session": e.name, "evaluator_user": frappe.session.user},
			pluck="name",
		)
		self.assertEqual(len(rows), 1)
		self.assertEqual(frappe.db.get_value(COI, r2["name"], "declaration_status"), "Declared No Conflict")
