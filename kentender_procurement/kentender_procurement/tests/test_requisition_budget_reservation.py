# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-006: budget reservation on final approval."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.services.budget_availability import aggregate_ledger_buckets
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_procurement.services.requisition_workflow_actions import (
	RAR_DOCTYPE,
	approve_requisition_step,
	reject_requisition,
	submit_requisition,
)
from kentender_strategy.tests.test_output_indicator import _indicator
from kentender_strategy.tests.test_strategic_program_and_sub_program import (
	_esp,
	_nf,
	_obj,
	_pillar,
	_program,
	_sub,
)

BLE = "Budget Ledger Entry"
BL = "Budget Line"
BUD = "Budget"
BCP = "Budget Control Period"
PR = "Purchase Requisition"
SUB = "Strategic Sub Program"
PRG = "Strategic Program"
ESP = "Entity Strategic Plan"
FW = "National Framework"
PILLAR = "National Pillar"
OBJ = "National Objective"
IND = "Output Indicator"


def _cleanup_pr06_workflow_artifacts():
	for dn in frappe.get_all(PR, filters={"name": ("like", "_KT_PR06_%")}, pluck="name") or []:
		for inst in frappe.get_all(
			"KenTender Approval Route Instance",
			filters={"reference_doctype": PR, "reference_docname": dn},
			pluck="name",
		):
			try:
				frappe.delete_doc("KenTender Approval Route Instance", inst, force=True, ignore_permissions=True)
			except Exception:
				pass
	for code in ("_KT_PR06_WF", "_KT_PR06_NL_WF", "_KT_PR06_RJ_WF"):
		if frappe.db.exists("KenTender Workflow Policy", {"policy_code": code}):
			frappe.delete_doc("KenTender Workflow Policy", code, force=True, ignore_permissions=True)
		if frappe.db.exists("KenTender Approval Route Template", {"template_code": code}):
			frappe.delete_doc("KenTender Approval Route Template", code, force=True, ignore_permissions=True)


def _ensure_pr06_route_policy(*, policy_code: str = "_KT_PR06_WF") -> None:
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": policy_code}):
		return
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": policy_code,
			"template_name": "PR06 test route",
			"object_type": PR,
			"steps": [
				{
					"doctype": "KenTender Approval Route Template Step",
					"step_order": 1,
					"step_name": "Approve",
					"actor_type": "Role",
					"role_required": "System Manager",
				}
			],
		}
	)
	tpl.insert()
	frappe.get_doc(
		{
			"doctype": "KenTender Workflow Policy",
			"policy_code": policy_code,
			"applies_to_doctype": PR,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": 1,
		}
	).insert()


def _ensure_secondary_user():
	email = "_kt_pr06_approver@test.local"
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


def _pr_kw(entity: str, currency: str, business_id: str, **extra):
	kw = {
		"doctype": PR,
		"name": business_id,
		"title": "Budget reservation test",
		"requisition_type": "Goods",
		"status": "Draft",
		"workflow_state": "Draft",
		"approval_status": "Draft",
		"procuring_entity": entity,
		"fiscal_year": "2026-2027",
		"currency": currency,
		"request_date": "2026-04-01",
		"priority_level": "Medium",
		"budget_reservation_status": "None",
		"planning_status": "Unplanned",
	}
	kw.update(extra)
	return kw


def _tear_down_pr06_strategy_budget():
	_cleanup_pr06_workflow_artifacts()
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR06_%")}, pluck="name") or []:
		frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": name})
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	for ln in frappe.get_all(BL, filters={"name": ("like", "_KT_PR06_%")}, pluck="name") or []:
		frappe.db.delete(BLE, {"budget_line": ln})
	frappe.db.delete(BL, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete(BUD, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete(IND, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete(SUB, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete(PRG, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete(ESP, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete(OBJ, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete(PILLAR, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete(FW, {"name": ("like", "_KT_PR06_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PR06_%")})


def _cleanup_pr06_nl_data():
	_cleanup_pr06_workflow_artifacts()
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR06_NL_%")}, pluck="name") or []:
		frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": name})
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PR06_NL_PE"})


def _cleanup_pr06_rj_data():
	_cleanup_pr06_workflow_artifacts()
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR06_RJ_%")}, pluck="name") or []:
		frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": name})
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PR06_RJ_PE"})


class TestRequisitionBudgetReservationLinked(FrappeTestCase):
	"""PR with budget_line + strategy linkage; reservation on approve."""

	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_tear_down_pr06_strategy_budget)
		self.entity = _make_entity("_KT_PR06_PE").insert()
		self.nf1 = _nf("_KT_PR06_NF1", "PR06-A").insert()
		self.pl1 = _pillar("_KT_PR06_PL1", self.nf1.name).insert()
		self.ob1 = _obj("_KT_PR06_OB1", self.pl1.name, objective_code="O1").insert()
		self.plan = _esp("_KT_PR06_ESP1", self.entity.name, self.nf1.name, version_no=1).insert()
		self.prog = _program(
			"_KT_PR06_PG1",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG1",
		).insert()
		self.sub = _sub("_KT_PR06_SG1", self.prog.name, self.plan.name, sub_program_code="SG1").insert()
		self.indicator = _indicator("_KT_PR06_IND1", self.sub.name, indicator_code="K1").insert()
		self.period = _bcp(
			"_KT_PR06_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_PR06_BG1", self.entity.name, self.period.name, self.currency).insert()
		self.bline_ok = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_PR06_LINE_OK",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 10000,
			}
		).insert()
		self.bline_tight = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_PR06_LINE_TIGHT",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 100,
			}
		).insert()
		_ensure_pr06_route_policy()

	def tearDown(self):
		run_test_db_cleanup(_tear_down_pr06_strategy_budget)
		super().tearDown()

	def _linked_pr_kw(self, business_id: str, budget_line: str, line_qty: float, line_unit: float, **extra):
		kw = _pr_kw(self.entity.name, self.currency, business_id, **extra)
		kw["program"] = self.prog.name
		kw["entity_strategic_plan"] = self.plan.name
		kw["sub_program"] = self.sub.name
		kw["output_indicator"] = self.indicator.name
		kw["national_objective"] = self.ob1.name
		kw["budget"] = self.budget.name
		kw["budget_control_period"] = self.period.name
		kw["budget_line"] = budget_line
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Line",
				"quantity": line_qty,
				"estimated_unit_cost": line_unit,
			}
		]
		return kw

	def test_reserve_on_final_approve_success(self):
		other = _ensure_secondary_user()
		kw = self._linked_pr_kw("_KT_PR06_OK1", self.bline_ok.name, 2, 500)
		doc = frappe.get_doc(kw)
		doc.insert()
		doc.requested_by_user = other
		doc.save()
		submit_requisition(doc.name, user=other)
		approve_requisition_step(doc.name, workflow_step="Final", decision_level="L1")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")
		self.assertEqual(doc.budget_reservation_status, "Reserved")
		self.assertTrue(doc.last_budget_action_ref)
		self.assertAlmostEqual(flt(doc.reserved_amount), 1000.0)
		self.assertGreaterEqual(flt(doc.available_budget_at_check), 1000.0)
		ble = frappe.db.get_value(
			BLE,
			doc.last_budget_action_ref,
			["related_requisition", "budget_line", "amount"],
			as_dict=True,
		)
		self.assertEqual(ble.related_requisition, doc.name)
		self.assertEqual(ble.budget_line, self.bline_ok.name)
		self.assertAlmostEqual(flt(ble.amount), 1000.0)
		r, _, _ = aggregate_ledger_buckets(self.bline_ok.name)
		self.assertGreaterEqual(r, 1000.0)

	def test_insufficient_funds_blocks_approval(self):
		other = _ensure_secondary_user()
		kw = self._linked_pr_kw("_KT_PR06_BAD1", self.bline_tight.name, 10, 500)
		doc = frappe.get_doc(kw)
		doc.insert()
		doc.requested_by_user = other
		doc.save()
		submit_requisition(doc.name, user=other)
		self.assertRaises(
			frappe.ValidationError,
			lambda: approve_requisition_step(doc.name, workflow_step="Final", decision_level="L1"),
		)
		doc.reload()
		self.assertEqual(doc.workflow_state, "Pending HOD Approval")
		self.assertEqual(doc.budget_reservation_status, "None")
		rows = frappe.get_all(BLE, filters={"related_requisition": doc.name}, pluck="name")
		self.assertEqual(len(rows), 0)


class TestRequisitionBudgetReservationNoLine(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pr06_nl_data)
		self.entity = _make_entity("_KT_PR06_NL_PE").insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pr06_nl_data)
		super().tearDown()

	def test_approve_without_budget_line_skips_reservation(self):
		_ensure_pr06_route_policy(policy_code="_KT_PR06_NL_WF")
		other = _ensure_secondary_user()
		kw = _pr_kw(self.entity.name, self.currency, "_KT_PR06_NL_1")
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Line",
				"quantity": 1,
				"estimated_unit_cost": 100,
			}
		]
		doc = frappe.get_doc(kw)
		doc.insert()
		doc.requested_by_user = other
		doc.save()
		submit_requisition(doc.name, user=other)
		approve_requisition_step(doc.name, workflow_step="Final", decision_level="L1")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Approved")
		self.assertEqual(doc.budget_reservation_status, "None")
		self.assertFalse(doc.last_budget_action_ref)
		self.assertAlmostEqual(flt(doc.reserved_amount), 0.0)


class TestRequisitionRejectNoReservation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pr06_rj_data)
		self.entity = _make_entity("_KT_PR06_RJ_PE").insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pr06_rj_data)
		super().tearDown()

	def test_reject_after_submit_does_not_reserve(self):
		_ensure_pr06_route_policy(policy_code="_KT_PR06_RJ_WF")
		kw = _pr_kw(self.entity.name, self.currency, "_KT_PR06_RJ_1")
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Line",
				"quantity": 1,
				"estimated_unit_cost": 50,
			}
		]
		doc = frappe.get_doc(kw)
		doc.insert()
		submit_requisition(doc.name)
		reject_requisition(doc.name, workflow_step="HOD", decision_level="L1", comments="No")
		doc.reload()
		self.assertEqual(doc.workflow_state, "Rejected")
		rows = frappe.get_all(BLE, filters={"related_requisition": doc.name}, pluck="name")
		self.assertEqual(len(rows), 0)
