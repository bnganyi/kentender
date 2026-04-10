# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-015: Procurement Plan Approval Record."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

PP = "Procurement Plan"
PPAR = "Procurement Plan Approval Record"
BCP = "Budget Control Period"


def _cleanup_ppar():
	for pp in frappe.get_all(PP, filters={"name": ("like", "_KT_PPAR_%")}, pluck="name") or []:
		frappe.db.delete(PPAR, {"procurement_plan": pp})
		frappe.delete_doc(PP, pp, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PPAR_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PPAR_PE"})


class TestProcurementPlanApprovalRecord(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_ppar)
		self.entity = _make_entity("_KT_PPAR_PE").insert()
		self.period = _bcp("_KT_PPAR_BCP", self.entity.name).insert()
		self.plan = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PPAR_PP",
				"plan_title": "PPAR test plan",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ppar)
		super().tearDown()

	def test_valid_create_and_linkage(self):
		rec = frappe.get_doc(
			{
				"doctype": PPAR,
				"procurement_plan": self.plan.name,
				"workflow_step": "Planning Authority",
				"decision_level": "L1",
				"approver_user": frappe.session.user,
				"action_type": "Approve",
				"action_datetime": "2026-04-02 10:00:00",
				"comments": "OK",
			}
		)
		rec.insert(ignore_permissions=True)
		self.assertTrue(rec.name)
		self.assertEqual(rec.procurement_plan, self.plan.name)
		self.assertIn(self.plan.name, rec.display_label or "")
		self.assertIn("Planning Authority", rec.display_label or "")
		rec.reload()
		self.assertEqual(rec.action_type, "Approve")

	def test_append_only_update_blocked(self):
		rec = frappe.get_doc(
			{
				"doctype": PPAR,
				"procurement_plan": self.plan.name,
				"workflow_step": "Finance",
				"decision_level": "L2",
				"approver_user": frappe.session.user,
				"action_type": "Reject",
				"action_datetime": "2026-04-02 11:00:00",
			}
		)
		rec.insert(ignore_permissions=True)
		rec.comments = "changed"
		self.assertRaises(frappe.ValidationError, rec.save)

	def test_append_only_delete_blocked(self):
		rec = frappe.get_doc(
			{
				"doctype": PPAR,
				"procurement_plan": self.plan.name,
				"workflow_step": "HOD",
				"decision_level": "L1",
				"approver_user": frappe.session.user,
				"action_type": "Recommend",
				"action_datetime": "2026-04-02 12:00:00",
			}
		)
		rec.insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, PPAR, rec.name, force=True)
