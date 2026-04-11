# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.separation_of_duty_service import RULE_DOCTYPE
from kentender.uat.kt_test_local_users import delete_kt_test_local_user
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_procurement.services.requisition_workflow_actions import (
	RAR_DOCTYPE,
	WS_PENDING_FINANCE,
	WS_PENDING_HOD,
	WS_RETURNED,
	approve_requisition_step,
	reject_requisition,
	return_requisition_for_revision,
	submit_requisition,
)

PR = "Purchase Requisition"


def _cleanup_route_and_policy(suffix: str):
	pol_code = f"_KT_PR04_POL_{suffix}"
	tpl_code = f"_KT_PR04_TPL_{suffix}"
	for name in frappe.get_all(
		"KenTender Approval Route Instance",
		filters={"reference_doctype": PR},
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


def _ensure_pr_route_policy(suffix: str, *, n_steps: int) -> None:
	pol_code = f"_KT_PR04_POL_{suffix}"
	tpl_code = f"_KT_PR04_TPL_{suffix}"
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
		return
	steps = []
	for i in range(n_steps):
		steps.append(
			{
				"doctype": "KenTender Approval Route Template Step",
				"step_order": i + 1,
				"step_name": f"S{i + 1}",
				"actor_type": "Role",
				"role_required": "System Manager",
			}
		)
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": tpl_code,
			"template_name": f"Test route {n_steps}-step",
			"object_type": PR,
			"steps": steps,
		}
	)
	tpl.insert()
	pol = frappe.get_doc(
		{
			"doctype": "KenTender Workflow Policy",
			"policy_code": pol_code,
			"applies_to_doctype": PR,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": 1,
		}
	)
	pol.insert()


def _make_pr_kwargs(entity_name: str, currency: str, business_id: str):
	return {
		"doctype": PR,
		"name": business_id,
		"title": "Workflow test",
		"requisition_type": "Goods",
		"status": "Draft",
		"workflow_state": "Draft",
		"approval_status": "Draft",
		"procuring_entity": entity_name,
		"fiscal_year": "2026-2027",
		"currency": currency,
		"request_date": "2026-04-01",
		"priority_level": "Medium",
		"budget_reservation_status": "None",
		"planning_status": "Unplanned",
		"items": [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Line",
				"quantity": 2,
				"estimated_unit_cost": 500,
			}
		],
	}


def _make_sod_rule_recommend_to_approve():
	return frappe.get_doc(
		{
			"doctype": RULE_DOCTYPE,
			"rule_code": "_KT_PR04_SOD_RA",
			"active": 1,
			"source_doctype": PR,
			"source_action": "recommend",
			"source_role": "System Manager",
			"target_doctype": PR,
			"target_action": "approve",
			"target_role": "System Manager",
			"scope_type": "Same Document",
			"severity": "High",
			"exception_policy": "Block",
		}
	)


def _ensure_secondary_user():
	email = "_kt_pr04_approver@test.local"
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


class TestRequisitionWorkflowActions(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self._wf = frappe.generate_hash()[:10]
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(self._teardown_pr04_wf)
		self.entity = _make_entity("_KT_PR04_WF_PE").insert()

	def _teardown_pr04_wf(self):
		_cleanup_route_and_policy(self._wf)
		for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR04_WF_%")}, pluck="name") or []:
			frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": name})
			frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
		frappe.db.delete(RULE_DOCTYPE, {"rule_code": ("like", "_KT_PR04_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PR04_WF_PE"})
		delete_kt_test_local_user("_kt_pr04_approver@test.local")

	def tearDown(self):
		run_test_db_cleanup(self._teardown_pr04_wf)
		super().tearDown()

	def _new_pr(self, suffix: str):
		kw = _make_pr_kwargs(self.entity.name, self.currency, f"_KT_PR04_WF_{suffix}")
		doc = frappe.get_doc(kw)
		doc.insert()
		return doc

	def test_submit(self):
		_ensure_pr_route_policy(self._wf, n_steps=1)
		doc = self._new_pr("S1")
		submit_requisition(doc.name)
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_PENDING_HOD)
		self.assertEqual(doc.status, "Pending")
		self.assertEqual(doc.approval_status, WS_PENDING_HOD)

	def test_approve_creates_rar(self):
		_ensure_pr_route_policy(self._wf, n_steps=1)
		other = _ensure_secondary_user()
		doc = self._new_pr("A1")
		doc.requested_by_user = other
		doc.save()
		submit_requisition(doc.name, user=other)
		approve_requisition_step(
			doc.name,
			workflow_step="Final",
			decision_level="L1",
			comments="Approved",
		)
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")
		self.assertEqual(doc.status, "Approved")
		self.assertEqual(doc.approval_status, "Approved")
		rars = frappe.get_all(
			RAR_DOCTYPE,
			filters={"purchase_requisition": doc.name, "action_type": "Approve"},
		)
		self.assertEqual(len(rars), 1)

	def test_two_step_approve(self):
		_ensure_pr_route_policy(self._wf, n_steps=2)
		other = _ensure_secondary_user()
		doc = self._new_pr("A2")
		doc.requested_by_user = other
		doc.save()
		submit_requisition(doc.name, user=other)
		self.assertEqual(doc.reload().workflow_state, WS_PENDING_HOD)
		approve_requisition_step(
			doc.name,
			workflow_step="S1",
			decision_level="L1",
			comments="Step1",
		)
		self.assertEqual(doc.reload().workflow_state, WS_PENDING_FINANCE)
		approve_requisition_step(
			doc.name,
			workflow_step="S2",
			decision_level="L2",
			comments="Step2",
		)
		self.assertEqual(doc.reload().workflow_state, "Approved")

	def test_reject_creates_rar(self):
		_ensure_pr_route_policy(self._wf, n_steps=1)
		doc = self._new_pr("R1")
		submit_requisition(doc.name)
		reject_requisition(doc.name, workflow_step="HOD", decision_level="L1", comments="No")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Rejected")
		self.assertEqual(doc.status, "Rejected")
		self.assertEqual(doc.approval_status, "Rejected")
		rars = frappe.get_all(
			RAR_DOCTYPE,
			filters={"purchase_requisition": doc.name, "action_type": "Reject"},
		)
		self.assertEqual(len(rars), 1)

	def test_return_for_revision_creates_rar(self):
		_ensure_pr_route_policy(self._wf, n_steps=1)
		doc = self._new_pr("RT1")
		submit_requisition(doc.name)
		return_requisition_for_revision(
			doc.name,
			workflow_step="HOD",
			decision_level="L1",
			comments="Fix scope",
		)
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_RETURNED)
		self.assertEqual(doc.status, "Draft")
		rars = frappe.get_all(
			RAR_DOCTYPE,
			filters={"purchase_requisition": doc.name, "action_type": "Return for Revision"},
		)
		self.assertEqual(len(rars), 1)

	def test_self_approval_blocked(self):
		_ensure_pr_route_policy(self._wf, n_steps=1)
		doc = self._new_pr("SA1")
		submit_requisition(doc.name)
		doc.reload()
		self.assertEqual(doc.requested_by_user, frappe.session.user)
		self.assertRaises(
			frappe.ValidationError,
			lambda: approve_requisition_step(
				doc.name,
				workflow_step="Final",
				decision_level="L1",
			),
		)

	def test_sod_blocks_recommend_then_approve_same_user(self):
		_ensure_pr_route_policy(self._wf, n_steps=1)
		_make_sod_rule_recommend_to_approve().insert()
		other = _ensure_secondary_user()
		doc = self._new_pr("SOD2")
		doc.requested_by_user = other
		doc.save()
		submit_requisition(doc.name, user=other)
		frappe.get_doc(
			{
				"doctype": RAR_DOCTYPE,
				"purchase_requisition": doc.name,
				"workflow_step": "Committee",
				"decision_level": "L0",
				"approver_user": frappe.session.user,
				"approver_role": "System Manager",
				"action_type": "Recommend",
				"action_datetime": "2026-04-03 09:00:00",
			}
		).insert(ignore_permissions=True)
		self.assertRaises(
			frappe.ValidationError,
			lambda: approve_requisition_step(
				doc.name,
				workflow_step="Final",
				decision_level="L1",
			),
		)
