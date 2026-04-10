# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import (
	_ensure_test_currency,
	_make_entity,
	run_test_db_cleanup,
)

from kentender_strategy.tests.test_entity_strategic_plan import _make_national_framework, _make_plan

SRR = "Strategic Revision Record"
PLAN = "Entity Strategic Plan"
FW = "National Framework"


def _revision(business_id: str, old_plan: str, new_plan: str, **kw):
	d = {
		"doctype": SRR,
		"name": business_id,
		"entity_strategic_plan_old": old_plan,
		"entity_strategic_plan_new": new_plan,
		"revision_reason": kw.pop("revision_reason", "Annual update"),
		"status": kw.pop("status", "Draft"),
	}
	d.update(kw)
	return frappe.get_doc(d)


def _cleanup_srr06_data():
	frappe.db.delete(SRR, {"name": ("like", "_KT_SRR06_%")})
	frappe.db.delete(PLAN, {"name": ("like", "_KT_SRR06_%")})
	frappe.db.delete(FW, {"name": ("like", "_KT_SRR06_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_SRR06_%")})


class TestStrategicRevisionRecord(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		run_test_db_cleanup(_cleanup_srr06_data)
		self.entity = _make_entity("_KT_SRR06_PE").insert()
		self.nf = _make_national_framework("_KT_SRR06_NF", "SRR06-NF").insert()
		self.plan_v1 = _make_plan("_KT_SRR06_P1", self.entity.name, self.nf.name, version_no=1).insert()
		self.plan_v2 = _make_plan("_KT_SRR06_P2", self.entity.name, self.nf.name, version_no=2).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_srr06_data)
		super().tearDown()

	def test_valid_revision_record(self):
		doc = _revision("_KT_SRR06_R1", self.plan_v1.name, self.plan_v2.name).insert()
		self.assertEqual(doc.entity_strategic_plan_old, self.plan_v1.name)
		self.assertEqual(doc.entity_strategic_plan_new, self.plan_v2.name)

	def test_same_plan_blocked(self):
		doc = _revision("_KT_SRR06_R2", self.plan_v1.name, self.plan_v1.name)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_cross_entity_plans_blocked(self):
		ent2 = _make_entity("_KT_SRR06_PE2").insert()
		plan_other = _make_plan("_KT_SRR06_PX", ent2.name, self.nf.name, version_no=1).insert()
		try:
			doc = _revision("_KT_SRR06_R3", self.plan_v1.name, plan_other.name)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc(PLAN, plan_other.name, force=True)
			frappe.delete_doc("Procuring Entity", ent2.name, force=True)
			frappe.db.commit()

	def test_duplicate_business_id_blocked(self):
		_revision("_KT_SRR06_R4", self.plan_v1.name, self.plan_v2.name).insert()
		dup = _revision("_KT_SRR06_R4", self.plan_v1.name, self.plan_v2.name)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)
