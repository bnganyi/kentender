# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-008: apply_requisition_amendment."""

import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender.uat.kt_test_local_users import delete_kt_test_local_user
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.services.budget_availability import aggregate_ledger_buckets
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_procurement.services.requisition_amendment_apply import apply_requisition_amendment
from kentender_procurement.services.requisition_workflow_actions import (
	RAR_DOCTYPE,
	approve_requisition_step,
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
RAM = "Requisition Amendment Record"
SUB = "Strategic Sub Program"
PRG = "Strategic Program"
ESP = "Entity Strategic Plan"
FW = "National Framework"
PILLAR = "National Pillar"
OBJ = "National Objective"
IND = "Output Indicator"


def _cleanup_pr08_routes_policies():
	for dn in frappe.get_all(PR, filters={"name": ("like", "_KT_PR08_%")}, pluck="name") or []:
		for inst in frappe.get_all(
			"KenTender Approval Route Instance",
			filters={"reference_doctype": PR, "reference_docname": dn},
			pluck="name",
		):
			try:
				frappe.delete_doc("KenTender Approval Route Instance", inst, force=True, ignore_permissions=True)
			except Exception:
				pass
	code = "_KT_PR08_WF"
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": code}):
		frappe.delete_doc("KenTender Workflow Policy", code, force=True, ignore_permissions=True)
	if frappe.db.exists("KenTender Approval Route Template", {"template_code": code}):
		frappe.delete_doc("KenTender Approval Route Template", code, force=True, ignore_permissions=True)


def _ensure_pr08_route_policy() -> None:
	code = "_KT_PR08_WF"
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": code}):
		return
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": code,
			"template_name": "PR08 test route",
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
			"policy_code": code,
			"applies_to_doctype": PR,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": 1,
		}
	).insert()


def _ensure_secondary_user():
	email = "_kt_pr08_approver@test.local"
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
		"title": "Amendment apply test",
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


def _tear_down_pr08():
	_cleanup_pr08_routes_policies()
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR08_%")}, pluck="name") or []:
		frappe.db.delete(RAM, {"purchase_requisition": name})
		frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": name})
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	for ln in frappe.get_all(BL, filters={"name": ("like", "_KT_PR08_%")}, pluck="name") or []:
		frappe.db.delete(BLE, {"budget_line": ln})
	frappe.db.delete(BL, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete(BUD, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete(IND, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete(SUB, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete(PRG, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete(ESP, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete(OBJ, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete(PILLAR, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete(FW, {"name": ("like", "_KT_PR08_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PR08_%")})
	delete_kt_test_local_user("_kt_pr08_approver@test.local")


class TestRequisitionAmendmentApply(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_tear_down_pr08)
		self.entity = _make_entity("_KT_PR08_PE").insert()
		self.nf1 = _nf("_KT_PR08_NF1", "PR08-A").insert()
		self.pl1 = _pillar("_KT_PR08_PL1", self.nf1.name).insert()
		self.ob1 = _obj("_KT_PR08_OB1", self.pl1.name, objective_code="O1").insert()
		self.plan = _esp("_KT_PR08_ESP1", self.entity.name, self.nf1.name, version_no=1).insert()
		self.prog = _program(
			"_KT_PR08_PG1",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG1",
		).insert()
		self.sub = _sub("_KT_PR08_SG1", self.prog.name, self.plan.name, sub_program_code="SG1").insert()
		self.indicator = _indicator("_KT_PR08_IND1", self.sub.name, indicator_code="K1").insert()
		self.period = _bcp(
			"_KT_PR08_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_PR08_BG1", self.entity.name, self.period.name, self.currency).insert()
		self.bline = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_PR08_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 10000,
			}
		).insert()
		_ensure_pr08_route_policy()

	def tearDown(self):
		run_test_db_cleanup(_tear_down_pr08)
		super().tearDown()

	def _linked_pr_kw(self, business_id: str, line_qty: float, line_unit: float):
		kw = _pr_kw(self.entity.name, self.currency, business_id)
		kw["program"] = self.prog.name
		kw["entity_strategic_plan"] = self.plan.name
		kw["sub_program"] = self.sub.name
		kw["output_indicator"] = self.indicator.name
		kw["national_objective"] = self.ob1.name
		kw["budget"] = self.budget.name
		kw["budget_control_period"] = self.period.name
		kw["budget_line"] = self.bline.name
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Line",
				"quantity": line_qty,
				"estimated_unit_cost": line_unit,
			}
		]
		return kw

	def _approve_reserved_pr(self, business_id: str, qty: float, unit: float):
		other = _ensure_secondary_user()
		doc = frappe.get_doc(self._linked_pr_kw(business_id, qty, unit))
		doc.insert()
		doc.requested_by_user = other
		doc.save()
		submit_requisition(doc.name, user=other)
		approve_requisition_step(doc.name, workflow_step="Final", decision_level="L1")
		doc.reload()
		return doc

	def _approved_amendment(self, pr_name: str, atype: str, after: dict, reason: str = "Apply test"):
		return frappe.get_doc(
			{
				"doctype": RAM,
				"purchase_requisition": pr_name,
				"amendment_type": atype,
				"requested_by": "Administrator",
				"requested_on": "2026-04-03 08:00:00",
				"approved_by": "Administrator",
				"approved_on": "2026-04-03 09:00:00",
				"reason": reason,
				"before_summary": "{}",
				"after_summary": json.dumps(after),
				"budget_adjustment_required": 1,
				"status": "Approved",
			}
		).insert(ignore_permissions=True)

	def test_apply_draft_blocked(self):
		doc = self._approve_reserved_pr("_KT_PR08_AP1", 2, 500)
		am = frappe.get_doc(
			{
				"doctype": RAM,
				"purchase_requisition": doc.name,
				"amendment_type": "Cost Estimate Change",
				"requested_by": "Administrator",
				"requested_on": "2026-04-03 08:00:00",
				"reason": "Draft",
				"after_summary": json.dumps({"items": [{"idx": 1, "estimated_unit_cost": 600}]}),
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, lambda: apply_requisition_amendment(am.name))

	def test_apply_cost_change_adjusts_reservation(self):
		doc = self._approve_reserved_pr("_KT_PR08_AP2", 2, 500)
		self.assertAlmostEqual(flt(doc.reserved_amount), 1000.0)
		am = self._approved_amendment(
			doc.name,
			"Cost Estimate Change",
			{"items": [{"idx": 1, "estimated_unit_cost": 1500}]},
		)
		apply_requisition_amendment(am.name)
		doc.reload()
		am.reload()
		self.assertEqual(am.status, "Applied")
		self.assertAlmostEqual(flt(doc.requested_amount), 3000.0)
		self.assertAlmostEqual(flt(doc.reserved_amount), 3000.0)
		r, _, _ = aggregate_ledger_buckets(self.bline.name)
		self.assertAlmostEqual(r, 3000.0)

	def test_cancellation_releases_and_cancels_pr(self):
		doc = self._approve_reserved_pr("_KT_PR08_AP3", 1, 200)
		am = self._approved_amendment(doc.name, "Cancellation", {}, reason="No longer needed")
		apply_requisition_amendment(am.name)
		doc.reload()
		self.assertEqual(doc.workflow_state, "Cancelled")
		self.assertEqual(doc.status, "Cancelled")
		self.assertEqual(doc.budget_reservation_status, "Released")
		self.assertAlmostEqual(flt(doc.reserved_amount), 0.0)
		r, _, _ = aggregate_ledger_buckets(self.bline.name)
		self.assertAlmostEqual(r, 0.0)

	def test_direct_save_approved_blocked(self):
		doc = self._approve_reserved_pr("_KT_PR08_AP4", 1, 100)
		doc.reload()
		doc.title = "Illegal change"
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_strategic_not_implemented(self):
		doc = self._approve_reserved_pr("_KT_PR08_AP5", 1, 50)
		am = self._approved_amendment(
			doc.name,
			"Strategic Linkage Correction",
			{},
			reason="Test",
		)
		self.assertRaises(frappe.ValidationError, lambda: apply_requisition_amendment(am.name))
