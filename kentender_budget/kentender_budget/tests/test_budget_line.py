# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_budget.tests.test_budget import _budget

from kentender_strategy.tests.test_output_indicator import _indicator
from kentender_strategy.tests.test_strategic_program_and_sub_program import (
	_esp,
	_nf,
	_obj,
	_pillar,
	_program,
	_sub,
)

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


class TestBudgetLine(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BUD04_PE").insert()
		self.nf1 = _nf("_KT_BUD04_NF1", "BUD04-A").insert()
		self.pl1 = _pillar("_KT_BUD04_PL1", self.nf1.name).insert()
		self.ob1 = _obj("_KT_BUD04_OB1", self.pl1.name).insert()
		self.plan = _esp("_KT_BUD04_ESP1", self.entity.name, self.nf1.name, version_no=1).insert()
		self.prog = _program(
			"_KT_BUD04_PG1",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG1",
		).insert()
		self.sub = _sub("_KT_BUD04_SG1", self.prog.name, self.plan.name, sub_program_code="SG1").insert()
		self.indicator = _indicator("_KT_BUD04_IND1", self.sub.name, indicator_code="K1").insert()
		self.period = _bcp(
			"_KT_BUD04_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BUD04_BG1", self.entity.name, self.period.name, self.currency).insert()

	def tearDown(self):
		frappe.db.delete(BL, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete(BUD, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete(BCP, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete(IND, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete(SUB, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete(PRG, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete(ESP, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete(OBJ, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete(PILLAR, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete(FW, {"name": ("like", "_KT_BUD04_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BUD04_%")})
		frappe.db.commit()
		super().tearDown()

	def _line(self, business_id: str, **kw):
		d = {
			"doctype": BL,
			"name": business_id,
			"budget": self.budget.name,
			"budget_line_type": "Operating",
			"status": "Draft",
		}
		d.update(kw)
		return frappe.get_doc(d)

	def test_valid_line_with_strategy_links(self):
		doc = self._line(
			"_KT_BUD04_L1",
			output_indicator=self.indicator.name,
			program=self.prog.name,
			sub_program=self.sub.name,
			entity_strategic_plan=self.plan.name,
		).insert()
		self.assertEqual(doc.procuring_entity, self.entity.name)
		self.assertEqual(doc.fiscal_year, self.period.fiscal_year)
		self.assertEqual(doc.currency, self.currency)

	def test_budget_total_allocated_derived_from_lines(self):
		self._line(
			"_KT_BUD04_LROLL",
			allocated_amount=250000,
			output_indicator=self.indicator.name,
			program=self.prog.name,
			sub_program=self.sub.name,
			entity_strategic_plan=self.plan.name,
			budget_line_type="Operating",
		).insert()
		self.budget.reload()
		self.assertEqual(float(self.budget.total_allocated_amount), 250000.0)
		frappe.db.set_value(BUD, self.budget.name, "total_allocated_amount", 999999)
		b = frappe.get_doc(BUD, self.budget.name)
		b.save()
		self.assertEqual(float(b.total_allocated_amount), 250000.0)

	def test_line_fills_from_budget_and_indicator(self):
		doc = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_BUD04_L2",
				"budget": self.budget.name,
				"output_indicator": self.indicator.name,
				"budget_line_type": "Operating",
				"status": "Draft",
			}
		)
		doc.insert()
		self.assertEqual(doc.program, self.prog.name)
		self.assertEqual(doc.fiscal_year, self.period.fiscal_year)

	def test_wrong_procuring_entity_vs_budget_blocked(self):
		ent2 = _make_entity("_KT_BUD04_PE2").insert()
		try:
			doc = self._line("_KT_BUD04_L3", procuring_entity=ent2.name, budget_line_type="Operating")
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc("Procuring Entity", ent2.name, force=True)
			frappe.db.commit()

	def test_fiscal_year_mismatch_blocked(self):
		doc = self._line(
			"_KT_BUD04_L4",
			fiscal_year="2099-2100",
			budget_line_type="Operating",
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_strategy_sub_mismatch_blocked(self):
		sub2 = _sub("_KT_BUD04_SG2", self.prog.name, self.plan.name, sub_program_code="SG2").insert()
		try:
			doc = self._line(
				"_KT_BUD04_L5",
				output_indicator=self.indicator.name,
				sub_program=sub2.name,
				program=self.prog.name,
				entity_strategic_plan=self.plan.name,
				budget_line_type="Operating",
			)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc(SUB, sub2.name, force=True)
			frappe.db.commit()

	def test_department_scoped_to_entity(self):
		dept = frappe.get_doc(
			{
				"doctype": "Procuring Department",
				"department_code": "_KT_BUD04_D1",
				"department_name": "Test Dept",
				"procuring_entity": self.entity.name,
			}
		).insert()
		try:
			doc = self._line(
				"_KT_BUD04_L6",
				responsible_department=dept.name,
				budget_line_type="Capital",
			).insert()
			self.assertEqual(doc.responsible_department, dept.name)
		finally:
			frappe.delete_doc("Procuring Department", dept.name, force=True)
			frappe.db.commit()

	def test_plan_from_other_procuring_entity_blocked(self):
		"""BUD-005: Entity Strategic Plan must belong to line procuring entity (record_belongs_to_entity)."""
		ent2 = _make_entity("_KT_BUD04_PE_OTH").insert()
		try:
			plan2 = _esp("_KT_BUD04_ESP_OTH", ent2.name, self.nf1.name, version_no=91).insert()
			try:
				doc = self._line(
					"_KT_BUD04_L7",
					entity_strategic_plan=plan2.name,
					budget_line_type="Operating",
				)
				self.assertRaises(frappe.ValidationError, doc.insert)
			finally:
				frappe.delete_doc(ESP, plan2.name, force=True)
				frappe.db.commit()
		finally:
			frappe.delete_doc("Procuring Entity", ent2.name, force=True)
			frappe.db.commit()

	def test_program_from_other_procuring_entity_blocked(self):
		"""BUD-005: validate_strategic_linkage_set rejects program scoped to another entity."""
		ent2 = _make_entity("_KT_BUD04_PE_PRG").insert()
		try:
			plan2 = _esp("_KT_BUD04_ESP_PRG", ent2.name, self.nf1.name, version_no=92).insert()
			prog2 = _program(
				"_KT_BUD04_PG_OTH",
				plan2.name,
				ent2.name,
				self.ob1.name,
				program_code="PGX",
			).insert()
			try:
				doc = self._line(
					"_KT_BUD04_L8",
					program=prog2.name,
					entity_strategic_plan=plan2.name,
					budget_line_type="Operating",
				)
				self.assertRaises(frappe.ValidationError, doc.insert)
			finally:
				frappe.delete_doc(PRG, prog2.name, force=True)
				frappe.delete_doc(ESP, plan2.name, force=True)
				frappe.db.commit()
		finally:
			frappe.delete_doc("Procuring Entity", ent2.name, force=True)
			frappe.db.commit()
