# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-016: workflow engine smoke and safeguard tests."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender.workflow_engine.actions import emit_post_transition, log_global_approval_action
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.workflow_engine.execution import apply_step_decision, assert_actor_allowed_on_step, get_current_step_row
from kentender.workflow_engine.hooks import clear_side_effect_hooks_for_tests, register_side_effect_hook
from kentender.workflow_engine.routes import get_or_create_active_route, resolve_route_for_object
from kentender.workflow_engine.safeguards import workflow_mutation_context

PR = "Purchase Requisition"
TENDER = "Tender"
PP = "Procurement Plan"
BCP = "Budget Control Period"
WS_PENDING_HOD = "Pending HOD Approval"


class TestWorkflowEngine(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.suffix = frappe.generate_hash()[:12]

	def tearDown(self):
		def _cleanup_wf():
			clear_side_effect_hooks_for_tests()
			pr_names = frappe.get_all(PR, filters={"name": ("like", "_KT_WF_%")}, pluck="name")
			if pr_names:
				frappe.db.delete(
					"KenTender Approval Action",
					{"reference_doctype": PR, "reference_docname": ("in", pr_names)},
				)
			for name in frappe.get_all(
				"KenTender Approval Route Instance",
				filters={"reference_doctype": PR},
				pluck="name",
			):
				try:
					frappe.delete_doc("KenTender Approval Route Instance", name, force=True, ignore_permissions=True)
				except Exception:
					pass
			for name in frappe.get_all(PR, filters={"name": ("like", "_KT_WF_%")}, pluck="name"):
				try:
					frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
				except Exception:
					pass
			for name in frappe.get_all(TENDER, filters={"name": ("like", "_KT_WF_T_%")}, pluck="name"):
				try:
					frappe.delete_doc(TENDER, name, force=True, ignore_permissions=True)
				except Exception:
					pass
			for name in frappe.get_all(PP, filters={"name": ("like", "_KT_WF_P_%")}, pluck="name"):
				try:
					frappe.delete_doc(PP, name, force=True, ignore_permissions=True)
				except Exception:
					pass
			frappe.db.delete(BCP, {"name": ("like", "_KT_WF_B_%")})
			for name in frappe.get_all(
				"KenTender Workflow Policy",
				filters={"policy_code": ("like", "_KT_WF_%")},
				pluck="name",
			):
				try:
					frappe.delete_doc("KenTender Workflow Policy", name, force=True, ignore_permissions=True)
				except Exception:
					pass
			for name in frappe.get_all(
				"KenTender Approval Route Template",
				filters={"template_code": ("like", "_KT_WF_%")},
				pluck="name",
			):
				try:
					frappe.delete_doc("KenTender Approval Route Template", name, force=True, ignore_permissions=True)
				except Exception:
					pass
			frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_WF_%")})

		run_test_db_cleanup(_cleanup_wf)
		super().tearDown()

	def _minimal_pr(self):
		cur = _ensure_test_currency()
		ent_code = f"_KT_WF_{self.suffix}"
		ent = _make_entity(ent_code).insert()
		doc = frappe.get_doc(
			{
				"doctype": PR,
				"name": f"_KT_WF_{self.suffix}",
				"title": "WF test",
				"requisition_type": "Goods",
				"status": "Draft",
				"workflow_state": "Draft",
				"approval_status": "Draft",
				"requested_by_user": frappe.session.user,
				"procuring_entity": ent.name,
				"fiscal_year": "2026-2027",
				"currency": cur,
				"request_date": "2026-04-01",
				"priority_level": "Medium",
				"budget_reservation_status": "None",
				"planning_status": "Unplanned",
				"items": [
					{
						"doctype": "Purchase Requisition Item",
						"item_description": "Line",
						"quantity": 1,
						"estimated_unit_cost": 100,
					}
				],
			}
		)
		doc.insert()
		return doc

	def _minimal_wf_tender(self):
		cur = _ensure_test_currency()
		ent = _make_entity(f"_KT_WF_E_{self.suffix}").insert()
		doc = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"_KT_WF_T_{self.suffix}",
				"business_id": f"WF-T-{self.suffix}",
				"title": "WF tender safeguard",
				"tender_number": f"WF-TN-{self.suffix}",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": ent.name,
				"currency": cur,
				"supplier_eligibility_rule_mode": "Open",
				"procurement_method": "Open National Tender",
				"publication_datetime": "2026-05-01 09:00:00",
				"clarification_deadline": "2026-05-10 17:00:00",
				"submission_deadline": "2026-06-01 17:00:00",
				"opening_datetime": "2026-06-02 10:00:00",
			}
		)
		doc.insert()
		return doc

	def _minimal_wf_procurement_plan(self):
		cur = _ensure_test_currency()
		ent = _make_entity(f"_KT_WF_E_{self.suffix}").insert()
		period = _bcp(f"_KT_WF_B_{self.suffix}", ent.name).insert()
		doc = frappe.get_doc(
			{
				"doctype": PP,
				"name": f"_KT_WF_P_{self.suffix}",
				"plan_title": "WF plan safeguard",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": ent.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": period.name,
				"currency": cur,
				"version_no": 1,
			}
		)
		doc.insert()
		return doc

	def _tpl_and_pol(self, *, threshold_min=None, threshold_max=None, evaluation_order=100):
		tpl = frappe.get_doc(
			{
				"doctype": "KenTender Approval Route Template",
				"template_code": f"_KT_WF_{self.suffix}",
				"template_name": "Test route",
				"object_type": PR,
				"steps": [
					{
						"doctype": "KenTender Approval Route Template Step",
						"step_order": 1,
						"step_name": "Review",
						"actor_type": "Role",
						"role_required": "System Manager",
					}
				],
			}
		)
		tpl.insert()
		pol_fields = {
			"doctype": "KenTender Workflow Policy",
			"policy_code": f"_KT_WF_{self.suffix}",
			"applies_to_doctype": PR,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": evaluation_order,
		}
		if threshold_min is not None:
			pol_fields["threshold_min"] = threshold_min
		if threshold_max is not None:
			pol_fields["threshold_max"] = threshold_max
		pol = frappe.get_doc(pol_fields)
		pol.insert()
		return tpl, pol

	def test_safeguard_blocks_workflow_field_without_context(self):
		doc = self._minimal_pr()
		doc.reload()
		doc.workflow_state = WS_PENDING_HOD
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_workflow_mutation_context_allows_transition_fields(self):
		doc = self._minimal_pr()
		with workflow_mutation_context():
			doc.reload()
			doc.workflow_state = WS_PENDING_HOD
			doc.save()
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_PENDING_HOD)
		self.assertEqual(doc.status, "Pending")
		self.assertEqual(doc.approval_status, WS_PENDING_HOD)

	def test_tender_workflow_state_blocked_without_context(self):
		doc = self._minimal_wf_tender()
		doc.reload()
		doc.workflow_state = "Submitted"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_tender_workflow_mutation_context_allows(self):
		doc = self._minimal_wf_tender()
		with workflow_mutation_context():
			doc.reload()
			doc.workflow_state = "Submitted"
			doc.save()
		doc.reload()
		self.assertEqual(doc.workflow_state, "Submitted")

	def test_procurement_plan_workflow_state_blocked_without_context(self):
		doc = self._minimal_wf_procurement_plan()
		doc.reload()
		doc.workflow_state = "Submitted"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_procurement_plan_workflow_mutation_context_allows(self):
		doc = self._minimal_wf_procurement_plan()
		with workflow_mutation_context():
			doc.reload()
			doc.workflow_state = "Submitted"
			doc.save()
		doc.reload()
		self.assertEqual(doc.workflow_state, "Submitted")
		self.assertEqual(doc.status, "Pending")

	def test_ignore_workflow_field_protection_allows_stage_change(self):
		doc = self._minimal_pr()
		doc.reload()
		frappe.flags.ignore_workflow_field_protection = True
		try:
			doc.workflow_state = WS_PENDING_HOD
			doc.save()
		finally:
			frappe.flags.ignore_workflow_field_protection = False
		doc.reload()
		self.assertEqual(doc.workflow_state, WS_PENDING_HOD)

	def test_global_approval_action_append_only(self):
		doc = self._minimal_pr()
		name = log_global_approval_action(
			reference_doctype=PR,
			reference_docname=doc.name,
			action="test_action",
			actor_user=frappe.session.user,
			previous_state={"a": 1},
			new_state={"a": 2},
		)
		row = frappe.get_doc("KenTender Approval Action", name)
		row.comments = "nope"
		with self.assertRaises(frappe.ValidationError):
			row.save()

	def test_resolve_route_creates_instance(self):
		doc = self._minimal_pr()
		self._tpl_and_pol()
		pol_name = frappe.get_all(
			"KenTender Workflow Policy",
			filters={"policy_code": f"_KT_WF_{self.suffix}"},
			pluck="name",
		)[0]
		rid = resolve_route_for_object(PR, doc.name, policy_name=pol_name)
		self.assertTrue(rid)
		inst = frappe.get_doc("KenTender Approval Route Instance", rid)
		self.assertEqual(inst.reference_docname, doc.name)
		self.assertEqual(len(inst.route_steps), 1)
		self.assertEqual(inst.route_steps[0].status, "Active")

	def test_get_or_create_idempotent(self):
		doc = self._minimal_pr()
		self._tpl_and_pol()
		pol_name = frappe.get_all(
			"KenTender Workflow Policy",
			filters={"policy_code": f"_KT_WF_{self.suffix}"},
			pluck="name",
		)[0]
		a = get_or_create_active_route(PR, doc.name, policy_name=pol_name)
		b = get_or_create_active_route(PR, doc.name, policy_name=pol_name)
		self.assertEqual(a, b)

	def test_threshold_picks_matching_policy(self):
		doc = self._minimal_pr()
		doc.set("requested_amount", 500)
		doc.save()
		tpl_lo = frappe.get_doc(
			{
				"doctype": "KenTender Approval Route Template",
				"template_code": f"_KT_WF_LO_{self.suffix}",
				"template_name": "Lo",
				"object_type": PR,
				"steps": [
					{
						"doctype": "KenTender Approval Route Template Step",
						"step_order": 1,
						"step_name": "A",
						"actor_type": "Role",
						"role_required": "System Manager",
					}
				],
			}
		)
		tpl_lo.insert()
		tpl_hi = frappe.get_doc(
			{
				"doctype": "KenTender Approval Route Template",
				"template_code": f"_KT_WF_HI_{self.suffix}",
				"template_name": "Hi",
				"object_type": PR,
				"steps": [
					{
						"doctype": "KenTender Approval Route Template Step",
						"step_order": 1,
						"step_name": "B",
						"actor_type": "Role",
						"role_required": "System Manager",
					}
				],
			}
		)
		tpl_hi.insert()
		frappe.get_doc(
			{
				"doctype": "KenTender Workflow Policy",
				"policy_code": f"_KT_WF_PLO_{self.suffix}",
				"applies_to_doctype": PR,
				"linked_template": tpl_lo.name,
				"active": 1,
				"threshold_max": 400,
				"evaluation_order": 1,
			}
		).insert()
		p_hi = frappe.get_doc(
			{
				"doctype": "KenTender Workflow Policy",
				"policy_code": f"_KT_WF_PHI_{self.suffix}",
				"applies_to_doctype": PR,
				"linked_template": tpl_hi.name,
				"active": 1,
				"threshold_max": 600,
				"evaluation_order": 1,
			}
		)
		p_hi.insert()
		rid = resolve_route_for_object(PR, doc.name)
		inst = frappe.get_doc("KenTender Approval Route Instance", rid)
		self.assertEqual(inst.template_used, tpl_hi.name)

	def test_evaluation_order_breaks_tie(self):
		doc = self._minimal_pr()
		tpl_a = frappe.get_doc(
			{
				"doctype": "KenTender Approval Route Template",
				"template_code": f"_KT_WF_TA_{self.suffix}",
				"template_name": "TA",
				"object_type": PR,
				"steps": [
					{
						"doctype": "KenTender Approval Route Template Step",
						"step_order": 1,
						"step_name": "A",
						"actor_type": "Role",
						"role_required": "System Manager",
					}
				],
			}
		)
		tpl_a.insert()
		tpl_b = frappe.get_doc(
			{
				"doctype": "KenTender Approval Route Template",
				"template_code": f"_KT_WF_TB_{self.suffix}",
				"template_name": "TB",
				"object_type": PR,
				"steps": [
					{
						"doctype": "KenTender Approval Route Template Step",
						"step_order": 1,
						"step_name": "B",
						"actor_type": "Role",
						"role_required": "System Manager",
					}
				],
			}
		)
		tpl_b.insert()
		frappe.get_doc(
			{
				"doctype": "KenTender Workflow Policy",
				"policy_code": f"_KT_WF_PB_{self.suffix}",
				"applies_to_doctype": PR,
				"linked_template": tpl_b.name,
				"active": 1,
				"evaluation_order": 200,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "KenTender Workflow Policy",
				"policy_code": f"_KT_WF_PA_{self.suffix}",
				"applies_to_doctype": PR,
				"linked_template": tpl_a.name,
				"active": 1,
				"evaluation_order": 10,
			}
		).insert()
		rid = resolve_route_for_object(PR, doc.name)
		inst = frappe.get_doc("KenTender Approval Route Instance", rid)
		self.assertEqual(inst.template_used, tpl_a.name)

	def test_apply_step_decision_completes_single_step_route(self):
		doc = self._minimal_pr()
		with workflow_mutation_context():
			doc.workflow_state = WS_PENDING_HOD
			doc.save()
		self._tpl_and_pol()
		pol_name = frappe.get_all(
			"KenTender Workflow Policy",
			filters={"policy_code": f"_KT_WF_{self.suffix}"},
			pluck="name",
		)[0]
		rid = resolve_route_for_object(PR, doc.name, policy_name=pol_name)
		inst = frappe.get_doc("KenTender Approval Route Instance", rid)
		step_row = get_current_step_row(inst)
		assert_actor_allowed_on_step(frappe.session.user, inst, step_row)
		old = {"workflow_state": doc.workflow_state}
		with workflow_mutation_context():
			doc.workflow_state = "Approved"
			doc.save()
		doc.reload()
		new = {"workflow_state": doc.workflow_state}
		apply_step_decision(
			rid,
			"Approve",
			user=frappe.session.user,
			comments="ok",
			previous_state=old,
			new_state=new,
			log_action="approve",
			hook_action="approve",
		)
		inst.reload()
		self.assertEqual(inst.status, "Completed")

	def test_side_effect_hook_runs(self):
		doc = self._minimal_pr()
		called: list[str] = []

		def _hook(dt, dn, action, actor, ctx):
			called.append(f"{action}:{dn}")

		register_side_effect_hook(PR, _hook, order=10)
		emit_post_transition(
			doctype=PR,
			docname=doc.name,
			action="submit",
			actor="Administrator",
			context={},
		)
		self.assertTrue(any(c.startswith("submit:") for c in called))

	def test_side_effect_hook_action_filter(self):
		doc = self._minimal_pr()
		all_actions: list[str] = []
		approve_only: list[str] = []

		def _hook_all(dt, dn, action, actor, ctx):
			all_actions.append(action)

		def _hook_approve(dt, dn, action, actor, ctx):
			approve_only.append(action)

		register_side_effect_hook(PR, _hook_all, order=5)
		register_side_effect_hook(PR, _hook_approve, order=10, action="approve")
		emit_post_transition(
			doctype=PR,
			docname=doc.name,
			action="submit",
			actor="Administrator",
			context={},
		)
		self.assertEqual(all_actions, ["submit"])
		self.assertEqual(approve_only, [])
		emit_post_transition(
			doctype=PR,
			docname=doc.name,
			action="approve",
			actor="Administrator",
			context={},
		)
		self.assertIn("approve", all_actions)
		self.assertEqual(approve_only, ["approve"])
