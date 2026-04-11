# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-PLAN-001: Procurement Plan workflow via kentender.workflow_engine."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.uat.kt_test_local_users import delete_kt_test_local_user
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.procurement_plan_workflow_actions import (
	PPAR_DOCTYPE,
	PP_DOCTYPE,
	WS_ACTIVE,
	WS_APPROVED,
	WS_SUBMITTED,
	activate_procurement_plan,
	approve_procurement_plan_step,
	submit_procurement_plan_for_approval,
)


def _cleanup_plan_wf(suffix: str):
	pol_code = f"_KT_PPWF_POL_{suffix}"
	tpl_code = f"_KT_PPWF_TPL_{suffix}"
	for name in frappe.get_all(
		"KenTender Approval Route Instance",
		filters={"reference_doctype": PP_DOCTYPE},
		pluck="name",
	):
		try:
			frappe.delete_doc("KenTender Approval Route Instance", name, force=True, ignore_permissions=True)
		except Exception:
			pass
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
		frappe.delete_doc("KenTender Workflow Policy", pol_code, force=True, ignore_permissions=True)
	if frappe.db.exists("KenTender Approval Route Template", {"template_code": tpl_code}):
		frappe.delete_doc("KenTender Approval Route Template", tpl_code, force=True, ignore_permissions=True)


def _ensure_plan_route_policy(suffix: str, *, n_steps: int) -> None:
	pol_code = f"_KT_PPWF_POL_{suffix}"
	tpl_code = f"_KT_PPWF_TPL_{suffix}"
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
		return
	steps = []
	for i in range(n_steps):
		steps.append(
			{
				"doctype": "KenTender Approval Route Template Step",
				"step_order": i + 1,
				"step_name": f"P{i + 1}",
				"actor_type": "Role",
				"role_required": "System Manager",
			}
		)
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": tpl_code,
			"template_name": f"Plan route {n_steps}-step",
			"object_type": PP_DOCTYPE,
			"steps": steps,
		}
	)
	tpl.insert()
	pol = frappe.get_doc(
		{
			"doctype": "KenTender Workflow Policy",
			"policy_code": pol_code,
			"applies_to_doctype": PP_DOCTYPE,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": 1,
		}
	)
	pol.insert()


def _ensure_secondary_user():
	email = "_kt_ppwf_owner@test.local"
	if frappe.db.exists("User", email):
		return email
	u = frappe.new_doc("User")
	u.email = email
	u.first_name = "KT"
	u.send_welcome_email = 0
	u.enabled = 1
	u.user_type = "System User"
	u.insert(ignore_permissions=True)
	u.add_roles("System Manager")
	return email


class TestProcurementPlanWorkflowActions(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self._wf = frappe.generate_hash()[:10]
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(self._teardown_pp_wf)
		self.entity = _make_entity("_KT_PPWF_PE").insert()
		self.period = _bcp("_KT_PPWF_BCP", self.entity.name).insert()
		self.owner_user = _ensure_secondary_user()

	def _teardown_pp_wf(self):
		_cleanup_plan_wf(self._wf)
		for name in frappe.get_all(PP_DOCTYPE, filters={"name": ("like", "_KT_PPWF_%")}, pluck="name") or []:
			frappe.db.delete(PPAR_DOCTYPE, {"procurement_plan": name})
			frappe.delete_doc(PP_DOCTYPE, name, force=True, ignore_permissions=True)
		frappe.db.delete("Budget Control Period", {"name": ("like", "_KT_PPWF_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PPWF_PE"})
		delete_kt_test_local_user("_kt_ppwf_owner@test.local")

	def tearDown(self):
		run_test_db_cleanup(self._teardown_pp_wf)
		super().tearDown()

	def _new_plan(self, suffix: str):
		doc = frappe.get_doc(
			{
				"doctype": PP_DOCTYPE,
				"name": f"_KT_PPWF_{suffix}",
				"plan_title": "PPWF test",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
				"planning_owner_user": self.owner_user,
			}
		)
		doc.insert()
		return doc

	def test_submit_and_single_step_approve_activate(self):
		_ensure_plan_route_policy(self._wf, n_steps=1)
		doc = self._new_plan("A1")
		submit_procurement_plan_for_approval(doc.name)
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_SUBMITTED)
		approve_procurement_plan_step(
			doc.name,
			workflow_step="P1",
			decision_level="L1",
		)
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_APPROVED)
		activate_procurement_plan(doc.name)
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_ACTIVE)

	def test_two_step_approve(self):
		_ensure_plan_route_policy(self._wf, n_steps=2)
		doc = self._new_plan("A2")
		submit_procurement_plan_for_approval(doc.name)
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_SUBMITTED)
		approve_procurement_plan_step(doc.name, workflow_step="P1", decision_level="L1")
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_SUBMITTED)
		approve_procurement_plan_step(doc.name, workflow_step="P2", decision_level="L2")
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_APPROVED)

	def test_field_protection_blocks_direct_publish_of_stage(self):
		_ensure_plan_route_policy(self._wf, n_steps=1)
		doc = self._new_plan("A3")
		submit_procurement_plan_for_approval(doc.name)
		doc.reload()
		doc.workflow_state = WS_APPROVED
		with self.assertRaises(frappe.ValidationError):
			doc.save()
