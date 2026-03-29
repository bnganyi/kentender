# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

ESP = "Entity Strategic Plan"
PRG = "Strategic Program"
SUB = "Strategic Sub Program"
FW = "National Framework"
PILLAR = "National Pillar"
OBJ = "National Objective"


def _nf(bid: str, code: str, **kw):
	d = {
		"doctype": FW,
		"business_id": bid,
		"framework_code": code,
		"framework_name": code,
		"framework_type": "National Development Plan",
		"version_label": "v1",
		"status": "Draft",
		"is_locked_reference": 0,
		"start_date": "2026-01-01",
		"end_date": "2026-12-31",
	}
	d.update(kw)
	return frappe.get_doc(d)


def _pillar(bid: str, fw_name: str, code: str = "P1", **kw):
	d = {
		"doctype": PILLAR,
		"business_id": bid,
		"national_framework": fw_name,
		"pillar_code": code,
		"pillar_name": "Pillar",
		"status": "Draft",
		"is_locked_reference": 0,
		"display_order": 0,
	}
	d.update(kw)
	return frappe.get_doc(d)


def _obj(bid: str, pillar_name: str, code: str = "O1", **kw):
	d = {
		"doctype": OBJ,
		"business_id": bid,
		"national_pillar": pillar_name,
		"objective_code": code,
		"objective_name": "Objective",
		"status": "Draft",
		"is_locked_reference": 0,
		"display_order": 0,
	}
	d.update(kw)
	return frappe.get_doc(d)


def _esp(bid: str, entity_name: str, fw_name: str, ver: int = 1, **kw):
	d = {
		"doctype": ESP,
		"business_id": bid,
		"plan_title": "Plan",
		"procuring_entity": entity_name,
		"plan_period_label": "2026",
		"version_no": ver,
		"status": "Draft",
		"is_current_active_version": 0,
		"start_date": "2026-01-01",
		"end_date": "2026-12-31",
		"primary_national_framework": fw_name,
		"approval_status": "Draft",
	}
	d.update(kw)
	return frappe.get_doc(d)


def _program(bid: str, plan_name: str, entity_name: str, obj_name: str, **kw):
	d = {
		"doctype": PRG,
		"business_id": bid,
		"entity_strategic_plan": plan_name,
		"procuring_entity": entity_name,
		"program_code": kw.pop("program_code", "PG1"),
		"program_name": "Program",
		"national_objective": obj_name,
		"priority_level": "Medium",
		"status": "Draft",
	}
	d.update(kw)
	return frappe.get_doc(d)


def _sub(bid: str, program_name: str, plan_name: str, **kw):
	d = {
		"doctype": SUB,
		"business_id": bid,
		"program": program_name,
		"entity_strategic_plan": plan_name,
		"sub_program_code": kw.pop("sub_program_code", "SG1"),
		"sub_program_name": "Sub",
		"status": "Draft",
	}
	d.update(kw)
	return frappe.get_doc(d)


class TestStrategicProgramAndSubProgram(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity("_KT_SP05_PE").insert()
		self.nf1 = _nf("_KT_SP05_NF1", "SP05-A").insert()
		self.pl1 = _pillar("_KT_SP05_PL1", self.nf1.name).insert()
		self.ob1 = _obj("_KT_SP05_OB1", self.pl1.name).insert()
		self.plan = _esp("_KT_SP05_ESP1", self.entity.name, self.nf1.name, version_no=1).insert()

	def tearDown(self):
		frappe.db.delete(SUB, {"business_id": ("like", "_KT_SP05_%")})
		frappe.db.delete(PRG, {"business_id": ("like", "_KT_SP05_%")})
		frappe.db.delete(ESP, {"business_id": ("like", "_KT_SP05_%")})
		frappe.db.delete(OBJ, {"business_id": ("like", "_KT_SP05_%")})
		frappe.db.delete(PILLAR, {"business_id": ("like", "_KT_SP05_%")})
		frappe.db.delete(FW, {"business_id": ("like", "_KT_SP05_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_SP05_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_hierarchy(self):
		p = _program("_KT_SP05_P1", self.plan.name, self.entity.name, self.ob1.name).insert()
		s = _sub("_KT_SP05_S1", p.name, self.plan.name).insert()
		self.assertEqual(s.entity_strategic_plan, self.plan.name)
		self.assertEqual(p.procuring_entity, self.entity.name)

	def test_program_procuring_entity_filled_from_plan_when_omitted(self):
		doc = frappe.get_doc(
			{
				"doctype": PRG,
				"business_id": "_KT_SP05_P0",
				"entity_strategic_plan": self.plan.name,
				"program_code": "PG0",
				"program_name": "No entity on save",
				"national_objective": self.ob1.name,
				"priority_level": "Medium",
				"status": "Draft",
			}
		)
		doc.insert()
		self.assertEqual(doc.procuring_entity, self.entity.name)

	def test_program_procuring_entity_mismatch_blocked(self):
		ent2 = _make_entity("_KT_SP05_PE2").insert()
		doc = _program("_KT_SP05_P2", self.plan.name, ent2.name, self.ob1.name)
		self.assertRaises(frappe.ValidationError, doc.insert)
		frappe.delete_doc("Procuring Entity", ent2.name, force=True)
		frappe.db.commit()

	def test_program_objective_framework_mismatch_blocked(self):
		nf2 = _nf("_KT_SP05_NF2", "SP05-B", version_label="vb").insert()
		pl2 = _pillar("_KT_SP05_PL2", nf2.name, pillar_code="P2").insert()
		ob2 = _obj("_KT_SP05_OB2", pl2.name, objective_code="O2").insert()
		doc = _program("_KT_SP05_P3", self.plan.name, self.entity.name, ob2.name)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_sub_program_plan_mismatch_blocked(self):
		plan2 = _esp("_KT_SP05_ESP2", self.entity.name, self.nf1.name, version_no=2).insert()
		p = _program("_KT_SP05_P4", self.plan.name, self.entity.name, self.ob1.name).insert()
		doc = _sub("_KT_SP05_S2", p.name, plan2.name)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_sub_program_omitted_plan_filled_from_program(self):
		p = _program("_KT_SP05_P5", self.plan.name, self.entity.name, self.ob1.name).insert()
		doc = frappe.get_doc(
			{
				"doctype": SUB,
				"business_id": "_KT_SP05_S3",
				"program": p.name,
				"sub_program_code": "AUTO",
				"sub_program_name": "Auto plan",
				"status": "Draft",
			}
		)
		doc.insert()
		self.assertEqual(doc.entity_strategic_plan, self.plan.name)
