# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

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
		"business_id": bid,
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


class TestOutputIndicator(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
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
		frappe.db.delete(IND, {"business_id": ("like", "_KT_OI07_%")})
		frappe.db.delete(SUB, {"business_id": ("like", "_KT_OI07_%")})
		frappe.db.delete(PRG, {"business_id": ("like", "_KT_OI07_%")})
		frappe.db.delete(ESP, {"business_id": ("like", "_KT_OI07_%")})
		frappe.db.delete(OBJ, {"business_id": ("like", "_KT_OI07_%")})
		frappe.db.delete(PILLAR, {"business_id": ("like", "_KT_OI07_%")})
		frappe.db.delete(FW, {"business_id": ("like", "_KT_OI07_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_OI07_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_creation(self):
		doc = _indicator("_KT_OI07_I1", self.sub.name).insert()
		self.assertEqual(doc.program, self.prog.name)
		self.assertEqual(doc.entity_strategic_plan, self.plan.name)

	def test_omitted_program_and_plan_filled_from_sub_program(self):
		doc = frappe.get_doc(
			{
				"doctype": IND,
				"business_id": "_KT_OI07_I2",
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

	def test_wrong_program_blocked(self):
		prog2 = _program(
			"_KT_OI07_PG2",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG2",
		).insert()
		doc = _indicator("_KT_OI07_I3", self.sub.name, program=prog2.name, entity_strategic_plan=self.plan.name)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_wrong_plan_blocked(self):
		plan2 = _esp("_KT_OI07_ESP2", self.entity.name, self.nf1.name, version_no=2).insert()
		doc = _indicator(
			"_KT_OI07_I4",
			self.sub.name,
			program=self.prog.name,
			entity_strategic_plan=plan2.name,
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_duplicate_indicator_code_same_sub_program_blocked(self):
		_indicator("_KT_OI07_I5", self.sub.name, indicator_code="DUP").insert()
		dup = _indicator("_KT_OI07_I6", self.sub.name, indicator_code="DUP")
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)
