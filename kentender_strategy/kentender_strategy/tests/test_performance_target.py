# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_strategy.tests.test_output_indicator import _indicator
from kentender_strategy.tests.test_strategic_program_and_sub_program import (
	_esp,
	_nf,
	_obj,
	_pillar,
	_program,
	_sub,
)

PT = "Performance Target"
IND = "Output Indicator"
PRG = "Strategic Program"
SUB = "Strategic Sub Program"
ESP = "Entity Strategic Plan"
FW = "National Framework"
PILLAR = "National Pillar"
OBJ = "National Objective"


def _target(bid: str, indicator_name: str, **kw):
	d = {
		"doctype": PT,
		"business_id": bid,
		"target_title": "Target",
		"output_indicator": indicator_name,
		"target_period_type": "Quarterly",
		"period_label": "2026 Q1",
		"period_start_date": "2026-01-01",
		"period_end_date": "2026-03-31",
		"target_measurement_type": "Numeric",
		"target_value_numeric": 100.0,
		"status": "Draft",
	}
	d.update(kw)
	return frappe.get_doc(d)


class TestPerformanceTarget(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity("_KT_PT08_PE").insert()
		self.nf1 = _nf("_KT_PT08_NF1", "PT08-A").insert()
		self.pl1 = _pillar("_KT_PT08_PL1", self.nf1.name).insert()
		self.ob1 = _obj("_KT_PT08_OB1", self.pl1.name).insert()
		self.plan = _esp("_KT_PT08_ESP1", self.entity.name, self.nf1.name, version_no=1).insert()
		self.prog = _program(
			"_KT_PT08_PG1",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG1",
		).insert()
		self.sub = _sub("_KT_PT08_SG1", self.prog.name, self.plan.name, sub_program_code="SG1").insert()
		self.indicator = _indicator("_KT_PT08_IND1", self.sub.name, indicator_code="K1").insert()

	def tearDown(self):
		frappe.db.delete(PT, {"business_id": ("like", "_KT_PT08_%")})
		frappe.db.delete(IND, {"business_id": ("like", "_KT_PT08_%")})
		frappe.db.delete(SUB, {"business_id": ("like", "_KT_PT08_%")})
		frappe.db.delete(PRG, {"business_id": ("like", "_KT_PT08_%")})
		frappe.db.delete(ESP, {"business_id": ("like", "_KT_PT08_%")})
		frappe.db.delete(OBJ, {"business_id": ("like", "_KT_PT08_%")})
		frappe.db.delete(PILLAR, {"business_id": ("like", "_KT_PT08_%")})
		frappe.db.delete(FW, {"business_id": ("like", "_KT_PT08_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PT08_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_create_numeric(self):
		doc = _target("_KT_PT08_T1", self.indicator.name).insert()
		self.assertEqual(doc.sub_program, self.sub.name)
		self.assertEqual(doc.program, self.prog.name)
		self.assertEqual(doc.entity_strategic_plan, self.plan.name)

	def test_numeric_zero_allowed(self):
		doc = _target("_KT_PT08_T1Z", self.indicator.name, target_value_numeric=0)
		doc.insert()
		self.assertEqual(doc.target_value_numeric, 0)

	def test_hierarchy_filled_when_omitted(self):
		doc = frappe.get_doc(
			{
				"doctype": PT,
				"business_id": "_KT_PT08_T2",
				"target_title": "Auto hierarchy",
				"output_indicator": self.indicator.name,
				"target_period_type": "Monthly",
				"period_label": "2026-03",
				"period_start_date": "2026-03-01",
				"period_end_date": "2026-03-31",
				"target_measurement_type": "Percent",
				"target_value_percent": 75.0,
				"status": "Draft",
			}
		)
		doc.insert()
		self.assertEqual(doc.sub_program, self.sub.name)
		self.assertEqual(doc.program, self.prog.name)

	def test_wrong_sub_program_blocked(self):
		sub2 = _sub("_KT_PT08_SG2", self.prog.name, self.plan.name, sub_program_code="SG2").insert()
		doc = _target(
			"_KT_PT08_T3",
			self.indicator.name,
			sub_program=sub2.name,
			program=self.prog.name,
			entity_strategic_plan=self.plan.name,
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_wrong_plan_blocked(self):
		plan2 = _esp("_KT_PT08_ESP2", self.entity.name, self.nf1.name, version_no=2).insert()
		doc = _target(
			"_KT_PT08_T4",
			self.indicator.name,
			entity_strategic_plan=plan2.name,
			program=self.prog.name,
			sub_program=self.sub.name,
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_invalid_period_dates_blocked(self):
		doc = _target(
			"_KT_PT08_T5",
			self.indicator.name,
			period_start_date="2026-06-01",
			period_end_date="2026-01-01",
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_numeric_requires_value_not_text_or_percent(self):
		doc = _target(
			"_KT_PT08_T6",
			self.indicator.name,
			target_value_text="N/A",
			target_value_numeric=1,
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_text_requires_text_empty_numeric(self):
		doc = frappe.get_doc(
			{
				"doctype": PT,
				"business_id": "_KT_PT08_T7",
				"target_title": "Qual",
				"output_indicator": self.indicator.name,
				"entity_strategic_plan": self.plan.name,
				"program": self.prog.name,
				"sub_program": self.sub.name,
				"target_period_type": "Annual",
				"period_label": "FY2026",
				"period_start_date": "2026-01-01",
				"period_end_date": "2026-12-31",
				"target_measurement_type": "Text",
				"target_value_numeric": 5,
				"target_value_text": "Complete rollout",
				"status": "Draft",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_text_measurement_valid(self):
		doc = frappe.get_doc(
			{
				"doctype": PT,
				"business_id": "_KT_PT08_T7B",
				"target_title": "Qual OK",
				"output_indicator": self.indicator.name,
				"entity_strategic_plan": self.plan.name,
				"program": self.prog.name,
				"sub_program": self.sub.name,
				"target_period_type": "Annual",
				"period_label": "FY2026",
				"period_start_date": "2026-01-01",
				"period_end_date": "2026-12-31",
				"target_measurement_type": "Text",
				"target_value_text": "Complete rollout",
				"status": "Draft",
			}
		)
		doc.insert()
		self.assertEqual(doc.target_value_text, "Complete rollout")

	def test_percent_out_of_range_blocked(self):
		doc = _target(
			"_KT_PT08_T8",
			self.indicator.name,
			target_measurement_type="Percent",
			target_value_numeric=None,
			target_value_percent=101.0,
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
