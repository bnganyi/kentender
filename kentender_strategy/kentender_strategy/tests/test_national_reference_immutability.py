# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.services.national_reference_immutability import (
	IGNORE_NATIONAL_REFERENCE_IMMUTABILITY,
)

FW = "National Framework"
PILLAR = "National Pillar"
OBJECTIVE = "National Objective"


def _fw(business_id: str, code: str, **kwargs):
	data = {
		"doctype": FW,
		"name": business_id,
		"framework_code": code,
		"framework_name": f"FW {code}",
		"framework_type": "National Development Plan",
		"version_label": "v1",
		"status": "Draft",
		"is_locked_reference": 0,
		"start_date": "2026-01-01",
		"end_date": "2026-12-31",
	}
	data.update(kwargs)
	return frappe.get_doc(data)


def _pillar(business_id: str, fw_name: str, **kwargs):
	data = {
		"doctype": PILLAR,
		"name": business_id,
		"national_framework": fw_name,
		"pillar_code": kwargs.pop("pillar_code", "P1"),
		"pillar_name": "Pillar",
		"status": "Draft",
		"is_locked_reference": 0,
		"display_order": 0,
	}
	data.update(kwargs)
	return frappe.get_doc(data)


def _objective(business_id: str, pillar_name: str, **kwargs):
	data = {
		"doctype": OBJECTIVE,
		"name": business_id,
		"national_pillar": pillar_name,
		"objective_code": kwargs.pop("objective_code", "O1"),
		"objective_name": "Objective",
		"status": "Draft",
		"is_locked_reference": 0,
		"display_order": 0,
	}
	data.update(kwargs)
	return frappe.get_doc(data)


class TestNationalReferenceImmutability(FrappeTestCase):
	def tearDown(self):
		frappe.flags.pop(IGNORE_NATIONAL_REFERENCE_IMMUTABILITY, None)
		frappe.db.delete(OBJECTIVE, {"name": ("like", "_KT_STRAT3_%")})
		frappe.db.delete(PILLAR, {"name": ("like", "_KT_STRAT3_%")})
		frappe.db.delete(FW, {"name": ("like", "_KT_STRAT3_%")})
		frappe.db.commit()
		super().tearDown()

	def test_pillar_active_locked_cannot_edit(self):
		fw = _fw("_KT_STRAT3_FW", "STRAT3-FW").insert()
		pl = _pillar("_KT_STRAT3_PL", fw.name, status="Active", is_locked_reference=1).insert()
		pl.pillar_name = "Changed"
		self.assertRaises(frappe.ValidationError, pl.save)

	def test_objective_active_locked_cannot_edit(self):
		fw = _fw("_KT_STRAT3_FW2", "STRAT3-FW2").insert()
		pl = _pillar("_KT_STRAT3_PL2", fw.name).insert()
		obj = _objective("_KT_STRAT3_OB", pl.name, status="Active", is_locked_reference=1).insert()
		obj.objective_name = "Changed"
		self.assertRaises(frappe.ValidationError, obj.save)

	def test_pillar_active_unlocked_can_edit(self):
		fw = _fw("_KT_STRAT3_FW3", "STRAT3-FW3").insert()
		pl = _pillar("_KT_STRAT3_PL3", fw.name, status="Active", is_locked_reference=0).insert()
		pl.pillar_name = "Renamed pillar"
		pl.save()
		self.assertEqual(frappe.db.get_value(PILLAR, pl.name, "pillar_name"), "Renamed pillar")

	def test_bypass_flag_allows_locked_framework_edit(self):
		doc = _fw(
			"_KT_STRAT3_BP",
			"STRAT3-BP",
			status="Active",
			is_locked_reference=1,
		).insert()
		doc.framework_name = "Patched title"
		try:
			frappe.flags[IGNORE_NATIONAL_REFERENCE_IMMUTABILITY] = True
			doc.save()
		finally:
			frappe.flags.pop(IGNORE_NATIONAL_REFERENCE_IMMUTABILITY, None)
		self.assertEqual(frappe.db.get_value(FW, doc.name, "framework_name"), "Patched title")
