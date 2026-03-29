# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cint

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.tests.test_budget_control_period import _bcp

BCP = "Budget Control Period"
BUD = "Budget"


def _budget(business_id: str, entity_name: str, period_name: str, currency: str, **kw):
	d = {
		"doctype": BUD,
		"business_id": business_id,
		"budget_title": kw.pop("budget_title", "Test Budget"),
		"procuring_entity": entity_name,
		"budget_control_period": period_name,
		"version_no": kw.pop("version_no", 1),
		"currency": currency,
	}
	d.update(kw)
	return frappe.get_doc(d)


class TestBudget(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BUD02_PE").insert()
		self.period = _bcp("_KT_BUD02_BCP", self.entity.name).insert()

	def tearDown(self):
		frappe.db.delete(BUD, {"business_id": ("like", "_KT_BUD02_%")})
		frappe.db.delete(BCP, {"business_id": ("like", "_KT_BUD02_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BUD02_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_create(self):
		doc = _budget("_KT_BUD02_001", self.entity.name, self.period.name, self.currency).insert()
		self.assertEqual(doc.name, "_KT_BUD02_001")

	def test_period_entity_mismatch_blocked(self):
		ent2 = _make_entity("_KT_BUD02_PE2").insert()
		try:
			doc = _budget("_KT_BUD02_X", ent2.name, self.period.name, self.currency)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc("Procuring Entity", ent2.name, force=True)
			frappe.db.commit()

	def test_duplicate_version_blocked(self):
		_budget("_KT_BUD02_V1", self.entity.name, self.period.name, self.currency, version_no=3).insert()
		dup = _budget("_KT_BUD02_V2", self.entity.name, self.period.name, self.currency, version_no=3)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_supersedes_same_period_and_entity_ok(self):
		first = _budget("_KT_BUD02_S1", self.entity.name, self.period.name, self.currency, version_no=1).insert()
		second = _budget(
			"_KT_BUD02_S2",
			self.entity.name,
			self.period.name,
			self.currency,
			version_no=2,
			supersedes_budget=first.name,
		)
		second.insert()
		self.assertEqual(second.supersedes_budget, first.name)

	def test_supersedes_wrong_period_blocked(self):
		p2 = _bcp("_KT_BUD02_BCP2", self.entity.name, fiscal_year="2028-2029").insert()
		first = _budget("_KT_BUD02_T1", self.entity.name, self.period.name, self.currency, version_no=1).insert()
		bad = _budget(
			"_KT_BUD02_T2",
			self.entity.name,
			p2.name,
			self.currency,
			version_no=1,
			supersedes_budget=first.name,
		)
		self.assertRaises(frappe.ValidationError, bad.insert)

	def test_only_one_current_active_per_period(self):
		a = _budget(
			"_KT_BUD02_CA",
			self.entity.name,
			self.period.name,
			self.currency,
			version_no=10,
			is_current_active_version=1,
		).insert()
		b = _budget(
			"_KT_BUD02_CB",
			self.entity.name,
			self.period.name,
			self.currency,
			version_no=11,
			is_current_active_version=1,
		).insert()
		frappe.db.commit()
		a.reload()
		b.reload()
		self.assertEqual(cint(b.is_current_active_version), 1)
		self.assertEqual(cint(a.is_current_active_version), 0)
