# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_strategy.services.strategic_linkage_validation import (
	validate_indicator,
	validate_program,
	validate_strategic_linkage_set,
	validate_sub_program,
	validate_target,
)
from kentender_strategy.tests.test_output_indicator import _indicator
from kentender_strategy.tests.test_performance_target import _target
from kentender_strategy.tests.test_strategic_program_and_sub_program import (
	_esp,
	_nf,
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


class TestStrategicLinkageValidation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity("_KT_SL09_PE").insert()
		self.nf1 = _nf("_KT_SL09_NF1", "SL09-A").insert()
		self.pl1 = _pillar("_KT_SL09_PL1", self.nf1.name).insert()
		self.ob1 = _obj("_KT_SL09_OB1", self.pl1.name).insert()
		self.plan = _esp("_KT_SL09_ESP1", self.entity.name, self.nf1.name, version_no=1).insert()
		self.prog = _program(
			"_KT_SL09_PG1",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG1",
		).insert()
		self.sub = _sub("_KT_SL09_SG1", self.prog.name, self.plan.name, sub_program_code="SG1").insert()
		self.indicator = _indicator("_KT_SL09_IND1", self.sub.name, indicator_code="K1").insert()
		self.target = _target("_KT_SL09_T1", self.indicator.name).insert()

	def tearDown(self):
		frappe.db.delete(PT, {"business_id": ("like", "_KT_SL09_%")})
		frappe.db.delete(IND, {"business_id": ("like", "_KT_SL09_%")})
		frappe.db.delete(SUB, {"business_id": ("like", "_KT_SL09_%")})
		frappe.db.delete(PRG, {"business_id": ("like", "_KT_SL09_%")})
		frappe.db.delete(ESP, {"business_id": ("like", "_KT_SL09_%")})
		frappe.db.delete(OBJ, {"business_id": ("like", "_KT_SL09_%")})
		frappe.db.delete(PILLAR, {"business_id": ("like", "_KT_SL09_%")})
		frappe.db.delete(FW, {"business_id": ("like", "_KT_SL09_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_SL09_%")})
		frappe.db.commit()
		super().tearDown()

	def test_validate_program_ok(self):
		validate_program(self.prog.name, self.entity.name)

	def test_validate_program_wrong_entity(self):
		ent2 = _make_entity("_KT_SL09_PE2").insert()
		try:
			self.assertRaises(
				frappe.ValidationError,
				validate_program,
				self.prog.name,
				ent2.name,
			)
		finally:
			frappe.delete_doc("Procuring Entity", ent2.name, force=True)
			frappe.db.commit()

	def test_validate_sub_program_ok(self):
		validate_sub_program(self.sub.name, self.entity.name)

	def test_validate_indicator_ok(self):
		validate_indicator(self.indicator.name, self.entity.name)

	def test_validate_target_ok(self):
		validate_target(self.target.name, self.entity.name)
		validate_target(self.target.name, self.entity.name, as_of_date="2026-02-15")

	def test_validate_target_as_of_outside_period(self):
		self.assertRaises(
			frappe.ValidationError,
			validate_target,
			self.target.name,
			self.entity.name,
			"2026-06-01",
		)

	def test_validate_strategic_linkage_set_full_chain(self):
		validate_strategic_linkage_set(
			program=self.prog.name,
			sub_program=self.sub.name,
			output_indicator=self.indicator.name,
			performance_target=self.target.name,
			entity=self.entity.name,
		)

	def test_validate_strategic_linkage_set_sub_program_program_mismatch(self):
		prog2 = _program(
			"_KT_SL09_PG2",
			self.plan.name,
			self.entity.name,
			self.ob1.name,
			program_code="PG2",
		).insert()
		try:
			self.assertRaises(
				frappe.ValidationError,
				validate_strategic_linkage_set,
				program=prog2.name,
				sub_program=self.sub.name,
				entity=self.entity.name,
			)
		finally:
			frappe.delete_doc(PRG, prog2.name, force=True)
			frappe.db.commit()

	def test_validate_strategic_linkage_set_indicator_sub_mismatch(self):
		sub2 = _sub("_KT_SL09_SG2", self.prog.name, self.plan.name, sub_program_code="SG2").insert()
		try:
			self.assertRaises(
				frappe.ValidationError,
				validate_strategic_linkage_set,
				sub_program=sub2.name,
				output_indicator=self.indicator.name,
				entity=self.entity.name,
			)
		finally:
			frappe.delete_doc(SUB, sub2.name, force=True)
			frappe.db.commit()

	def test_validate_strategic_linkage_set_entity_only_no_op(self):
		validate_strategic_linkage_set(entity=self.entity.name)
