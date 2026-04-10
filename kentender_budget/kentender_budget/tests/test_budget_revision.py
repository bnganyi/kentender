# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

BL = "Budget Line"
BR = "Budget Revision"
BUD = "Budget"
BCP = "Budget Control Period"


class TestBudgetRevision(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BRV_PE").insert()
		self.period = _bcp(
			"_KT_BRV_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BRV_BG", self.entity.name, self.period.name, self.currency).insert()
		self.line_a = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_BRV_LA",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 3000,
			}
		).insert()
		self.line_b = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_BRV_LB",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 2000,
			}
		).insert()

	def tearDown(self):
		for name in frappe.get_all(BR, filters={"name": ("like", "_KT_BRV_%")}, pluck="name") or []:
			frappe.delete_doc(BR, name, force=True, ignore_permissions=True)
		frappe.db.delete(BL, {"name": ("like", "_KT_BRV_%")})
		frappe.db.delete(BUD, {"name": ("like", "_KT_BRV_%")})
		frappe.db.delete(BCP, {"name": ("like", "_KT_BRV_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BRV_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_increase_and_transfer(self):
		doc = frappe.get_doc(
			{
				"doctype": BR,
				"name": "_KT_BRV_R1",
				"budget": self.budget.name,
				"procuring_entity": self.entity.name,
				"revision_type": "Supplementary",
				"status": "Draft",
				"lines": [
					{
						"change_type": "Increase",
						"change_amount": 100,
						"target_budget_line": self.line_a.name,
					},
					{
						"change_type": "Transfer",
						"change_amount": 50,
						"source_budget_line": self.line_a.name,
						"target_budget_line": self.line_b.name,
					},
				],
			}
		).insert()
		self.assertEqual(len(doc.lines), 2)

	def test_transfer_same_line_blocked(self):
		doc = frappe.get_doc(
			{
				"doctype": BR,
				"name": "_KT_BRV_R2",
				"budget": self.budget.name,
				"procuring_entity": self.entity.name,
				"revision_type": "Virement",
				"status": "Draft",
				"lines": [
					{
						"change_type": "Transfer",
						"change_amount": 10,
						"source_budget_line": self.line_a.name,
						"target_budget_line": self.line_a.name,
					},
				],
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_increase_with_source_blocked(self):
		doc = frappe.get_doc(
			{
				"doctype": BR,
				"name": "_KT_BRV_R3",
				"budget": self.budget.name,
				"procuring_entity": self.entity.name,
				"revision_type": "Adjustment",
				"status": "Draft",
				"lines": [
					{
						"change_type": "Increase",
						"change_amount": 10,
						"source_budget_line": self.line_a.name,
						"target_budget_line": self.line_b.name,
					},
				],
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_line_wrong_budget_blocked(self):
		bud2 = _budget(
			"_KT_BRV_BG2",
			self.entity.name,
			self.period.name,
			self.currency,
			version_no=3,
		).insert()
		line_other = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_BRV_LO",
				"budget": bud2.name,
				"budget_line_type": "Operating",
				"status": "Draft",
			}
		).insert()
		try:
			doc = frappe.get_doc(
				{
					"doctype": BR,
					"name": "_KT_BRV_R4",
					"budget": self.budget.name,
					"procuring_entity": self.entity.name,
					"revision_type": "Adjustment",
					"status": "Draft",
					"lines": [
						{
							"change_type": "Increase",
							"change_amount": 10,
							"target_budget_line": line_other.name,
						},
					],
				}
			)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			frappe.delete_doc(BL, line_other.name, force=True, ignore_permissions=True)
			frappe.delete_doc(BUD, bud2.name, force=True, ignore_permissions=True)
			frappe.db.commit()
