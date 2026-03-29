# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

BA = "Budget Allocation"
BL = "Budget Line"
BUD = "Budget"
BCP = "Budget Control Period"


class TestBudgetAllocation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BAL_PE").insert()
		self.period = _bcp(
			"_KT_BAL_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BAL_BG", self.entity.name, self.period.name, self.currency).insert()
		self.line = frappe.get_doc(
			{
				"doctype": BL,
				"business_id": "_KT_BAL_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 5000,
			}
		).insert()

	def tearDown(self):
		frappe.db.delete(BA, {"business_id": ("like", "_KT_BAL_%")})
		frappe.db.delete(BL, {"business_id": ("like", "_KT_BAL_%")})
		frappe.db.delete(BUD, {"business_id": ("like", "_KT_BAL_%")})
		frappe.db.delete(BCP, {"business_id": ("like", "_KT_BAL_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BAL_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_create(self):
		doc = frappe.get_doc(
			{
				"doctype": BA,
				"business_id": "_KT_BAL_A1",
				"budget_line": self.line.name,
				"budget": self.budget.name,
				"procuring_entity": self.entity.name,
				"fiscal_year": self.period.fiscal_year,
				"currency": self.currency,
				"allocation_date": today(),
				"allocation_amount": 100,
				"allocation_type": "Increase",
				"status": "Draft",
			}
		).insert()
		self.assertEqual(doc.currency, self.currency)

	def test_auto_fill_from_line(self):
		doc = frappe.get_doc(
			{
				"doctype": BA,
				"business_id": "_KT_BAL_A2",
				"budget_line": self.line.name,
				"allocation_date": today(),
				"allocation_amount": 50,
				"allocation_type": "Revision Apply",
				"status": "Draft",
			}
		).insert()
		self.assertEqual(doc.budget, self.budget.name)
		self.assertEqual(doc.procuring_entity, self.entity.name)

	def test_wrong_budget_blocked(self):
		bud2 = _budget(
			"_KT_BAL_BG2",
			self.entity.name,
			self.period.name,
			self.currency,
			version_no=2,
		).insert()
		try:
			doc = frappe.get_doc(
				{
					"doctype": BA,
					"business_id": "_KT_BAL_A3",
					"budget_line": self.line.name,
					"budget": bud2.name,
					"procuring_entity": self.entity.name,
					"fiscal_year": self.period.fiscal_year,
					"currency": self.currency,
					"allocation_date": today(),
					"allocation_amount": 10,
					"allocation_type": "Increase",
					"status": "Draft",
				}
			)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc(BUD, bud2.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_zero_amount_blocked(self):
		doc = frappe.get_doc(
			{
				"doctype": BA,
				"business_id": "_KT_BAL_A4",
				"budget_line": self.line.name,
				"allocation_date": today(),
				"allocation_amount": 0,
				"allocation_type": "Increase",
				"status": "Draft",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
