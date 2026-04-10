# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-003: header totals + submission/items + budget/strategy boundary validation."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup

from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_strategy.tests.test_output_indicator import _indicator
from kentender_strategy.tests.test_strategic_program_and_sub_program import (
	_esp,
	_nf,
	_obj,
	_pillar,
	_program,
	_sub,
)

PR = "Purchase Requisition"
BL = "Budget Line"
BUD = "Budget"
BCP = "Budget Control Period"
SUB = "Strategic Sub Program"
PRG = "Strategic Program"
ESP = "Entity Strategic Plan"
FW = "National Framework"
PILLAR = "National Pillar"
OBJ = "National Objective"
IND = "Output Indicator"


def _pr_kw(entity: str, currency: str, business_id: str, **extra):
	kw = {
		"doctype": PR,
		"name": business_id,
		"title": "Test requisition",
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


def _cleanup_pr03_data():
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR03_%")}, pluck="name") or []:
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PR03_%")})


def _cleanup_pr03b_data():
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_PR03B_%")}, pluck="name") or []:
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	frappe.db.delete(BL, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete(BUD, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete(IND, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete(SUB, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete(PRG, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete(ESP, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete(OBJ, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete(PILLAR, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete(FW, {"name": ("like", "_KT_PR03B_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PR03B_%")})


class TestPurchaseRequisitionTotalsProc003(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pr03_data)
		self.entity = _make_entity("_KT_PR03_PE").insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pr03_data)
		super().tearDown()

	def test_requested_amount_is_sum_of_line_totals(self):
		kw = _pr_kw(self.entity.name, self.currency, "_KT_PR03_SUM")
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "A",
				"quantity": 3,
				"estimated_unit_cost": 100,
			},
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "B",
				"quantity": 2,
				"estimated_unit_cost": 50,
			},
		]
		doc = frappe.get_doc(kw)
		doc.insert()
		doc.reload()
		self.assertAlmostEqual(flt(doc.requested_amount), 400.0)

	def test_submitted_without_items_blocked(self):
		kw = _pr_kw(self.entity.name, self.currency, "_KT_PR03_SUB")
		kw["workflow_state"] = "Pending HOD Approval"
		doc = frappe.get_doc(kw)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_submitted_with_items_ok(self):
		kw = _pr_kw(self.entity.name, self.currency, "_KT_PR03_SUBOK")
		kw["workflow_state"] = "Pending HOD Approval"
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "One line",
				"quantity": 1,
				"estimated_unit_cost": 1,
			}
		]
		doc = frappe.get_doc(kw)
		doc.insert()
		self.assertTrue(doc.name)


class TestPurchaseRequisitionLinkageProc003(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pr03b_data)
		self.entity = _make_entity("_KT_PR03B_PE").insert()
		self.nf1 = _nf("_KT_PR03B_NF1", "PR03B-A").insert()
		self.pl1 = _pillar("_KT_PR03B_PL1", self.nf1.name).insert()
		self.ob1 = _obj("_KT_PR03B_OB1", self.pl1.name, objective_code="O1").insert()
		self.ob2 = _obj("_KT_PR03B_OB2", self.pl1.name, objective_code="O2").insert()
		self.plan = _esp("_KT_PR03B_ESP1", self.entity.name, self.nf1.name, version_no=1).insert()
		self.prog = _program(
			"_KT_PR03B_PG1",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG1",
		).insert()
		self.sub = _sub("_KT_PR03B_SG1", self.prog.name, self.plan.name, sub_program_code="SG1").insert()
		self.indicator = _indicator("_KT_PR03B_IND1", self.sub.name, indicator_code="K1").insert()
		self.period = _bcp(
			"_KT_PR03B_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_PR03B_BG1", self.entity.name, self.period.name, self.currency).insert()
		self.bline = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_PR03B_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
			}
		).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pr03b_data)
		super().tearDown()

	def _base_pr(self, business_id: str, **extra):
		kw = _pr_kw(self.entity.name, self.currency, business_id, **extra)
		kw["items"] = [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Line",
				"quantity": 1,
				"estimated_unit_cost": 1,
			}
		]
		return kw

	def test_budget_line_wrong_entity_blocked(self):
		ent2 = _make_entity("_KT_PR03B_PE2").insert()
		try:
			kw = self._base_pr(
				"_KT_PR03B_BL1",
				procuring_entity=ent2.name,
				budget_line=self.bline.name,
				budget=self.budget.name,
				budget_control_period=self.period.name,
			)
			doc = frappe.get_doc(kw)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc("Procuring Entity", ent2.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_program_wrong_entity_blocked(self):
		ent2 = _make_entity("_KT_PR03B_PE3").insert()
		try:
			kw = self._base_pr(
				"_KT_PR03B_PG1",
				procuring_entity=ent2.name,
				program=self.prog.name,
				entity_strategic_plan=self.plan.name,
			)
			doc = frappe.get_doc(kw)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc("Procuring Entity", ent2.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_national_objective_mismatch_blocked(self):
		kw = self._base_pr(
			"_KT_PR03B_NO1",
			program=self.prog.name,
			entity_strategic_plan=self.plan.name,
			sub_program=self.sub.name,
			output_indicator=self.indicator.name,
			national_objective=self.ob2.name,
		)
		doc = frappe.get_doc(kw)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_valid_strategy_and_budget_links(self):
		kw = self._base_pr(
			"_KT_PR03B_OK1",
			program=self.prog.name,
			entity_strategic_plan=self.plan.name,
			sub_program=self.sub.name,
			output_indicator=self.indicator.name,
			national_objective=self.ob1.name,
			budget=self.budget.name,
			budget_control_period=self.period.name,
			budget_line=self.bline.name,
		)
		doc = frappe.get_doc(kw)
		doc.insert()
		self.assertEqual(doc.budget_line, self.bline.name)
