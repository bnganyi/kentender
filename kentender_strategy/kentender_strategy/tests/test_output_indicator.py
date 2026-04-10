# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import (
	_ensure_test_currency,
	_make_entity,
	run_test_db_cleanup,
)

from kentender_strategy.tests.test_strategic_program_and_sub_program import (
	_esp,
	_nf,
	_obj,
	_pillar,
	_program,
	_sub,
)

IND = "Output Indicator"
PRG = "Strategic Program"
SUB = "Strategic Sub Program"
ESP = "Entity Strategic Plan"
FW = "National Framework"
PILLAR = "National Pillar"
OBJ = "National Objective"


def _indicator(bid: str, sub_name: str, **kw):
	d = {
		"doctype": IND,
		"name": bid,
		"indicator_code": kw.pop("indicator_code", "IND1"),
		"indicator_name": "Indicator",
		"sub_program": sub_name,
		"unit_of_measure": "Nos",
		"indicator_type": "Quantitative",
		"baseline_date": "2026-01-15",
		"status": "Draft",
	}
	d.update(kw)
	return frappe.get_doc(d)


def _cleanup_oi07_data():
	frappe.db.delete(IND, {"name": ("like", "_KT_OI07_%")})
	frappe.db.delete(SUB, {"name": ("like", "_KT_OI07_%")})
	frappe.db.delete(PRG, {"name": ("like", "_KT_OI07_%")})
	frappe.db.delete(ESP, {"name": ("like", "_KT_OI07_%")})
	frappe.db.delete(OBJ, {"name": ("like", "_KT_OI07_%")})
	frappe.db.delete(PILLAR, {"name": ("like", "_KT_OI07_%")})
	frappe.db.delete(FW, {"name": ("like", "_KT_OI07_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_OI07_%")})


class TestOutputIndicator(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		run_test_db_cleanup(_cleanup_oi07_data)
		self.entity = _make_entity("_KT_OI07_PE").insert()
		self.nf1 = _nf("_KT_OI07_NF1", "OI07-A").insert()
		self.pl1 = _pillar("_KT_OI07_PL1", self.nf1.name).insert()
		self.ob1 = _obj("_KT_OI07_OB1", self.pl1.name).insert()
		self.plan = _esp("_KT_OI07_ESP1", self.entity.name, self.nf1.name, version_no=1).insert()
		self.prog = _program(
			"_KT_OI07_PG1",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG1",
		).insert()
		self.sub = _sub("_KT_OI07_SG1", self.prog.name, self.plan.name, sub_program_code="SG1").insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_oi07_data)
		super().tearDown()

	def test_valid_creation(self):
		doc = _indicator("_KT_OI07_I1", self.sub.name).insert()
		self.assertEqual(doc.program, self.prog.name)
		self.assertEqual(doc.entity_strategic_plan, self.plan.name)

	def test_omitted_program_and_plan_filled_from_sub_program(self):
		doc = frappe.get_doc(
			{
				"doctype": IND,
				"name": "_KT_OI07_I2",
				"indicator_code": "IND2",
				"indicator_name": "Filled",
				"sub_program": self.sub.name,
				"unit_of_measure": "%",
				"indicator_type": "Qualitative",
				"baseline_date": "2026-02-01",
				"status": "Draft",
			}
		)
		doc.insert()
		self.assertEqual(doc.program, self.prog.name)
		self.assertEqual(doc.entity_strategic_plan, self.plan.name)

	def test_wrong_program_corrected_from_sub_program(self):
		prog2 = _program(
			"_KT_OI07_PG2",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG2",
		).insert()
		doc = _indicator("_KT_OI07_I3", self.sub.name, program=prog2.name, entity_strategic_plan=self.plan.name)
		doc.insert()
		self.assertEqual(doc.program, self.prog.name)
		self.assertEqual(doc.entity_strategic_plan, self.plan.name)

	def test_wrong_plan_corrected_from_sub_program(self):
		plan2 = _esp("_KT_OI07_ESP2", self.entity.name, self.nf1.name, version_no=2).insert()
		doc = _indicator(
			"_KT_OI07_I4",
			self.sub.name,
			program=self.prog.name,
			entity_strategic_plan=plan2.name,
		)
		doc.insert()
		self.assertEqual(doc.entity_strategic_plan, self.plan.name)

	def test_duplicate_indicator_code_same_sub_program_blocked(self):
		_indicator("_KT_OI07_I5", self.sub.name, indicator_code="DUP").insert()
		dup = _indicator("_KT_OI07_I6", self.sub.name, indicator_code="DUP")
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_stale_derived_hierarchy_realigned_on_save(self):
		doc = _indicator("_KT_OI07_I7", self.sub.name, indicator_code="STALE").insert()
		prog2 = _program(
			"_KT_OI07_PG3",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG3",
		).insert()
		frappe.db.set_value(IND, doc.name, "program", prog2.name, update_modified=False)
		frappe.db.commit()
		reloaded = frappe.get_doc(IND, doc.name)
		reloaded.save()
		self.assertEqual(reloaded.program, self.prog.name)
		self.assertEqual(reloaded.entity_strategic_plan, self.plan.name)
