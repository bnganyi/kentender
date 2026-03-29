# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cint

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

PLAN = "Entity Strategic Plan"
FW = "National Framework"


def _make_national_framework(business_id: str, code: str, **kwargs):
	data = {
		"doctype": FW,
		"business_id": business_id,
		"framework_code": code,
		"framework_name": f"NF {code}",
		"framework_type": "National Development Plan",
		"version_label": "v1",
		"status": "Draft",
		"is_locked_reference": 0,
		"start_date": "2026-01-01",
		"end_date": "2026-12-31",
	}
	data.update(kwargs)
	return frappe.get_doc(data)


def _make_plan(business_id: str, entity_name: str, fw_name: str, **kwargs):
	data = {
		"doctype": PLAN,
		"business_id": business_id,
		"plan_title": kwargs.pop("plan_title", "Strategic Plan"),
		"procuring_entity": entity_name,
		"plan_period_label": kwargs.pop("plan_period_label", "2026-2027"),
		"version_no": kwargs.pop("version_no", 1),
		"status": kwargs.pop("status", "Draft"),
		"is_current_active_version": kwargs.pop("is_current_active_version", 0),
		"start_date": kwargs.pop("start_date", "2026-01-01"),
		"end_date": kwargs.pop("end_date", "2026-12-31"),
		"primary_national_framework": fw_name,
		"approval_status": kwargs.pop("approval_status", "Draft"),
	}
	data.update(kwargs)
	return frappe.get_doc(data)


class TestEntityStrategicPlan(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity("_KT_ESP_PE")
		self.entity.insert()
		self.nf = _make_national_framework("_KT_ESP_NF", "ESP-NF").insert()

	def tearDown(self):
		frappe.db.delete(PLAN, {"business_id": ("like", "_KT_ESP_%")})
		frappe.db.delete(FW, {"business_id": ("like", "_KT_ESP_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_ESP_PE%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_create(self):
		doc = _make_plan("_KT_ESP_001", self.entity.name, self.nf.name)
		doc.insert()
		self.assertEqual(doc.name, "_KT_ESP_001")

	def test_invalid_date_range_blocked(self):
		doc = _make_plan(
			"_KT_ESP_DAT",
			self.entity.name,
			self.nf.name,
			start_date="2026-12-31",
			end_date="2026-01-01",
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_duplicate_version_per_entity_blocked(self):
		_make_plan("_KT_ESP_V1", self.entity.name, self.nf.name, version_no=3).insert()
		dup = _make_plan("_KT_ESP_V2", self.entity.name, self.nf.name, version_no=3)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_supersedes_plan_wrong_entity_blocked(self):
		ent2 = _make_entity("_KT_ESP_PE2")
		ent2.insert()
		first = _make_plan("_KT_ESP_S1", self.entity.name, self.nf.name, version_no=1).insert()
		bad = _make_plan(
			"_KT_ESP_S2",
			ent2.name,
			self.nf.name,
			version_no=1,
			supersedes_plan=first.name,
		)
		self.assertRaises(frappe.ValidationError, bad.insert)

	def test_supersedes_plan_same_entity_allowed(self):
		first = _make_plan("_KT_ESP_OK1", self.entity.name, self.nf.name, version_no=1).insert()
		second = _make_plan(
			"_KT_ESP_OK2",
			self.entity.name,
			self.nf.name,
			version_no=2,
			supersedes_plan=first.name,
		)
		second.insert()
		self.assertEqual(second.supersedes_plan, first.name)

	def test_only_one_current_active_version_per_entity(self):
		a = _make_plan(
			"_KT_ESP_CA",
			self.entity.name,
			self.nf.name,
			version_no=10,
			is_current_active_version=1,
		).insert()
		b = _make_plan(
			"_KT_ESP_CB",
			self.entity.name,
			self.nf.name,
			version_no=11,
			is_current_active_version=1,
		).insert()
		frappe.db.commit()
		self.assertEqual(cint(frappe.db.get_value(PLAN, a.name, "is_current_active_version")), 0)
		self.assertEqual(cint(frappe.db.get_value(PLAN, b.name, "is_current_active_version")), 1)
