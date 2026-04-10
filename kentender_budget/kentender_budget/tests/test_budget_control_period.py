# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

BCP = "Budget Control Period"
OPEN_STATUS = "Open"


def _bcp(business_id: str, entity_name: str, **kw):
	d = {
		"doctype": BCP,
		"name": business_id,
		"procuring_entity": entity_name,
		"fiscal_year": kw.pop("fiscal_year", "2026-2027"),
		"period_label": kw.pop("period_label", "FY26/27"),
		"start_date": kw.pop("start_date", "2026-07-01"),
		"end_date": kw.pop("end_date", "2027-06-30"),
		"status": kw.pop("status", "Draft"),
		"budget_source_type": kw.pop("budget_source_type", "Internal"),
	}
	d.update(kw)
	return frappe.get_doc(d)


class TestBudgetControlPeriod(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity("_KT_BCP01_PE").insert()

	def tearDown(self):
		frappe.db.delete(BCP, {"name": ("like", "_KT_BCP01_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BCP01_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_create(self):
		doc = _bcp("_KT_BCP01_001", self.entity.name).insert()
		self.assertEqual(doc.name, "_KT_BCP01_001")

	def test_invalid_date_range_blocked(self):
		doc = _bcp(
			"_KT_BCP01_DAT",
			self.entity.name,
			start_date="2027-06-30",
			end_date="2026-07-01",
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_second_open_same_entity_fy_blocked(self):
		_bcp("_KT_BCP01_A", self.entity.name, status=OPEN_STATUS).insert()
		dup = _bcp("_KT_BCP01_B", self.entity.name, status=OPEN_STATUS)
		self.assertRaises(frappe.ValidationError, dup.insert)

	def test_two_open_different_fy_allowed(self):
		_bcp("_KT_BCP01_C", self.entity.name, fiscal_year="2025-2026", status=OPEN_STATUS).insert()
		_bcp("_KT_BCP01_D", self.entity.name, fiscal_year="2026-2027", status=OPEN_STATUS).insert()

	def test_duplicate_business_id_blocked(self):
		_bcp("_KT_BCP01_E", self.entity.name).insert()
		dup = _bcp("_KT_BCP01_E", self.entity.name)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)
