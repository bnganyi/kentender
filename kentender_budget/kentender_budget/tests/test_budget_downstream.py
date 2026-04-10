# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.services.budget_downstream import (
	get_budget_availability,
	validate_budget_line,
	validate_funds_or_raise,
)
from kentender_budget.services.budget_ledger_posting import reserve_budget
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

BL = "Budget Line"
BUD = "Budget"
BCP = "Budget Control Period"
BLE = "Budget Ledger Entry"


class TestBudgetDownstream(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BDS_PE").insert()
		self.period = _bcp(
			"_KT_BDS_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BDS_BG", self.entity.name, self.period.name, self.currency).insert()
		self.line = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_BDS_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 8000,
			}
		).insert()

	def tearDown(self):
		frappe.db.delete(BLE, {"budget_line": self.line.name})
		frappe.db.delete(BL, {"name": ("like", "_KT_BDS_%")})
		frappe.db.delete(BUD, {"name": ("like", "_KT_BDS_%")})
		frappe.db.delete(BCP, {"name": ("like", "_KT_BDS_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BDS_%")})
		frappe.db.commit()
		super().tearDown()

	def test_get_budget_availability_delegates(self):
		b = get_budget_availability(self.line.name)
		self.assertAlmostEqual(b.allocated, 8000.0)

	def test_validate_budget_line_entity_ok(self):
		validate_budget_line(self.line.name, self.entity.name)

	def test_validate_budget_line_wrong_entity(self):
		ent2 = _make_entity("_KT_BDS_PE2").insert()
		try:
			self.assertRaises(
				frappe.ValidationError,
				validate_budget_line,
				self.line.name,
				ent2.name,
			)
		finally:
			frappe.delete_doc("Procuring Entity", ent2.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_validate_funds_reserve_ok(self):
		validate_funds_or_raise(self.line.name, 100, "reserve", self.entity.name)

	def test_validate_funds_reserve_insufficient(self):
		self.assertRaises(
			frappe.ValidationError,
			validate_funds_or_raise,
			self.line.name,
			999999,
			"reserve",
			self.entity.name,
		)

	def test_validate_funds_commit_from_reserved(self):
		reserve_budget(
			self.line.name,
			500,
			source_doctype="Test",
			source_docname="d",
			source_action="r",
		)
		validate_funds_or_raise(self.line.name, 400, "commit_from_reserved", self.entity.name)
		self.assertRaises(
			frappe.ValidationError,
			validate_funds_or_raise,
			self.line.name,
			600,
			"commit_from_reserved",
			self.entity.name,
		)
