# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

FW = "National Framework"
PILLAR = "National Pillar"
OBJECTIVE = "National Objective"


def _make_framework(business_id: str, framework_code: str, **kwargs):
	data = {
		"doctype": FW,
		"name": business_id,
		"framework_code": framework_code,
		"framework_name": f"Framework {framework_code}",
		"framework_type": "National Development Plan",
		"version_label": "v1",
		"status": "Draft",
		"is_locked_reference": 0,
		"start_date": "2026-01-01",
		"end_date": "2026-12-31",
	}
	data.update(kwargs)
	return frappe.get_doc(data)


def _make_pillar(business_id: str, national_framework: str, pillar_code: str = "P1", **kwargs):
	data = {
		"doctype": PILLAR,
		"name": business_id,
		"national_framework": national_framework,
		"pillar_code": pillar_code,
		"pillar_name": f"Pillar {pillar_code}",
		"status": "Draft",
		"display_order": 0,
	}
	data.update(kwargs)
	return frappe.get_doc(data)


def _make_objective(business_id: str, national_pillar: str, objective_code: str = "O1", **kwargs):
	data = {
		"doctype": OBJECTIVE,
		"name": business_id,
		"national_pillar": national_pillar,
		"objective_code": objective_code,
		"objective_name": f"Objective {objective_code}",
		"status": "Draft",
		"display_order": 0,
	}
	data.update(kwargs)
	return frappe.get_doc(data)


class TestNationalPillarAndObjective(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete(OBJECTIVE, {"name": ("like", "_KT_STRAT2_%")})
		frappe.db.delete(PILLAR, {"name": ("like", "_KT_STRAT2_%")})
		frappe.db.delete(FW, {"name": ("like", "_KT_STRAT2_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_hierarchy(self):
		fw = _make_framework("_KT_STRAT2_FW", "STRAT2-FW").insert()
		pl = _make_pillar("_KT_STRAT2_PL", fw.name, pillar_code="ECON").insert()
		obj = _make_objective("_KT_STRAT2_OB", pl.name, objective_code="OBJ1").insert()
		self.assertEqual(obj.name, "_KT_STRAT2_OB")
		self.assertEqual(obj.national_framework, fw.name)
		self.assertEqual(pl.national_framework, fw.name)

	def test_duplicate_pillar_code_same_framework(self):
		fw = _make_framework("_KT_STRAT2_FWD", "STRAT2-DUPF").insert()
		_make_pillar("_KT_STRAT2_P1", fw.name, pillar_code="SAME").insert()
		dup = _make_pillar("_KT_STRAT2_P2", fw.name, pillar_code="SAME")
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_same_pillar_code_different_framework(self):
		fw1 = _make_framework("_KT_STRAT2_FA", "STRAT2-FA", version_label="va").insert()
		fw2 = _make_framework("_KT_STRAT2_FB", "STRAT2-FB", version_label="vb").insert()
		_make_pillar("_KT_STRAT2_PA", fw1.name, pillar_code="SHARED").insert()
		pb = _make_pillar("_KT_STRAT2_PB", fw2.name, pillar_code="SHARED")
		pb.insert()
		self.assertEqual(pb.pillar_code, "SHARED")

	def test_duplicate_objective_code_same_pillar(self):
		fw = _make_framework("_KT_STRAT2_FWO", "STRAT2-FO").insert()
		pl = _make_pillar("_KT_STRAT2_PLO", fw.name).insert()
		_make_objective("_KT_STRAT2_O1", pl.name, objective_code="X").insert()
		dup = _make_objective("_KT_STRAT2_O2", pl.name, objective_code="X")
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_objective_framework_mismatch_blocked(self):
		fw1 = _make_framework("_KT_STRAT2_FM1", "STRAT2-M1").insert()
		fw2 = _make_framework("_KT_STRAT2_FM2", "STRAT2-M2", version_label="m2").insert()
		pl = _make_pillar("_KT_STRAT2_PFM", fw1.name).insert()
		doc = _make_objective("_KT_STRAT2_OFM", pl.name)
		doc.national_framework = fw2.name
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_framework_matches_pillar_after_insert(self):
		fw = _make_framework("_KT_STRAT2_FMS", "STRAT2-SYNC").insert()
		pl = _make_pillar("_KT_STRAT2_PMS", fw.name).insert()
		obj = _make_objective("_KT_STRAT2_OMS", pl.name).insert()
		self.assertEqual(obj.national_framework, pl.national_framework)

	def test_pillar_display_label_and_link_title(self):
		from frappe.desk.search import get_link_title

		fw = _make_framework("_KT_STRAT2_FWL", "STRAT2-FWL").insert()
		pl = _make_pillar(
			"_KT_STRAT2_PLL",
			fw.name,
			pillar_code="SOC",
			pillar_name="Social Development",
		).insert()
		pl.reload()
		self.assertEqual(pl.display_label, "SOC — Social Development")
		self.assertEqual(get_link_title(PILLAR, pl.name), "SOC — Social Development")
