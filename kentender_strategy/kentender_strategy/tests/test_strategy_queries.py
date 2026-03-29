# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_strategy.services.strategy_queries import (
	get_active_strategic_plans_for_entity,
	get_indicators_and_targets_for_entity,
	get_output_indicators_for_entity,
	get_performance_targets_for_entity,
	get_programs_for_national_objective,
)
from kentender_strategy.tests.test_entity_strategic_plan import _make_national_framework, _make_plan
from kentender_strategy.tests.test_output_indicator import _indicator
from kentender_strategy.tests.test_performance_target import _target
from kentender_strategy.tests.test_strategic_program_and_sub_program import (
	_obj,
	_pillar,
	_program,
	_sub,
)

IND = "Output Indicator"
PT = "Performance Target"
PRG = "Strategic Program"
SUB = "Strategic Sub Program"
ESP = "Entity Strategic Plan"
FW = "National Framework"
PILLAR = "National Pillar"
OBJ = "National Objective"


class TestStrategyQueries(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity("_KT_SQ10_PE").insert()
		self.nf1 = _make_national_framework("_KT_SQ10_NF", "SQ10-NF").insert()
		self.pl1 = _pillar("_KT_SQ10_PL1", self.nf1.name).insert()
		self.ob1 = _obj("_KT_SQ10_OB1", self.pl1.name).insert()
		self.plan_inactive = _make_plan(
			"_KT_SQ10_P0",
			self.entity.name,
			self.nf1.name,
			version_no=1,
			is_current_active_version=0,
		).insert()
		self.plan_active = _make_plan(
			"_KT_SQ10_P1",
			self.entity.name,
			self.nf1.name,
			version_no=2,
			is_current_active_version=1,
		).insert()
		self.prog = _program(
			"_KT_SQ10_PG1",
			self.plan_active.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG1",
		).insert()
		self.sub = _sub("_KT_SQ10_SG1", self.prog.name, self.plan_active.name, sub_program_code="SG1").insert()
		self.indicator = _indicator("_KT_SQ10_IND1", self.sub.name, indicator_code="K1").insert()
		self.perf_target = _target("_KT_SQ10_T1", self.indicator.name).insert()

	def tearDown(self):
		frappe.db.delete(PT, {"business_id": ("like", "_KT_SQ10_%")})
		frappe.db.delete(IND, {"business_id": ("like", "_KT_SQ10_%")})
		frappe.db.delete(SUB, {"business_id": ("like", "_KT_SQ10_%")})
		frappe.db.delete(PRG, {"business_id": ("like", "_KT_SQ10_%")})
		frappe.db.delete(ESP, {"business_id": ("like", "_KT_SQ10_%")})
		frappe.db.delete(OBJ, {"business_id": ("like", "_KT_SQ10_%")})
		frappe.db.delete(PILLAR, {"business_id": ("like", "_KT_SQ10_%")})
		frappe.db.delete(FW, {"business_id": ("like", "_KT_SQ10_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_SQ10_%")})
		frappe.db.commit()
		super().tearDown()

	def test_active_plans_respects_current_flag(self):
		rows = get_active_strategic_plans_for_entity(self.entity.name)
		names = {r["name"] for r in rows}
		self.assertIn(self.plan_active.name, names)
		self.assertNotIn(self.plan_inactive.name, names)

	def test_active_plans_empty_entity(self):
		self.assertEqual(get_active_strategic_plans_for_entity(""), [])

	def test_programs_by_national_objective(self):
		rows = get_programs_for_national_objective(self.ob1.name)
		self.assertTrue(any(r["name"] == self.prog.name for r in rows))

	def test_indicators_and_targets_by_entity(self):
		inds = get_output_indicators_for_entity(self.entity.name)
		self.assertTrue(any(r["name"] == self.indicator.name for r in inds))
		tgts = get_performance_targets_for_entity(self.entity.name)
		self.assertTrue(any(r["name"] == self.perf_target.name for r in tgts))
		i2, t2 = get_indicators_and_targets_for_entity(self.entity.name)
		self.assertEqual(len(i2), len(inds))
		self.assertEqual(len(t2), len(tgts))

	def test_script_report_active_plans_execute(self):
		mod = importlib.import_module(
			"kentender_strategy.kentender_strategy.report.strategy_active_plans_by_entity.strategy_active_plans_by_entity"
		)
		columns, data = mod.execute({"procuring_entity": self.entity.name})
		self.assertTrue(len(columns) >= 1)
		self.assertTrue(any(self.plan_active.name in row for row in data))

	def test_script_report_programs_by_objective_execute(self):
		mod = importlib.import_module(
			"kentender_strategy.kentender_strategy.report.strategy_programs_by_objective.strategy_programs_by_objective"
		)
		columns, data = mod.execute({"national_objective": self.ob1.name})
		self.assertTrue(any(self.prog.name in row for row in data))

	def test_script_report_indicators_targets_execute(self):
		mod = importlib.import_module(
			"kentender_strategy.kentender_strategy.report.strategy_indicators_and_targets_by_entity.strategy_indicators_and_targets_by_entity"
		)
		columns, data = mod.execute({"procuring_entity": self.entity.name})
		types = [row[0] for row in data]
		self.assertIn("Indicator", types)
		self.assertIn("Target", types)
