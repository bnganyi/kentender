# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.services.budget_line_derived_totals import (
	compute_available_amount,
	on_budget_ledger_post_recalculate_line,
	recalculate_budget_line_derived_totals,
)
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

BL = "Budget Line"
BUD = "Budget"
BCP = "Budget Control Period"


class TestBudgetLineDerivedTotals(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BUD06_PE").insert()
		self.period = _bcp(
			"_KT_BUD06_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BUD06_BG1", self.entity.name, self.period.name, self.currency).insert()

	def tearDown(self):
		frappe.db.delete(BL, {"business_id": ("like", "_KT_BUD06_%")})
		frappe.db.delete(BUD, {"business_id": ("like", "_KT_BUD06_%")})
		frappe.db.delete(BCP, {"business_id": ("like", "_KT_BUD06_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BUD06_%")})
		frappe.db.commit()
		super().tearDown()

	def _line_doc(self, business_id: str, **kw):
		d = {
			"doctype": BL,
			"business_id": business_id,
			"budget": self.budget.name,
			"budget_line_type": "Operating",
			"status": "Draft",
		}
		d.update(kw)
		return frappe.get_doc(d)

	def test_compute_available_amount(self):
		# 1000 - 100 - 200 - 50 + 25 = 675
		self.assertEqual(compute_available_amount(1000, 100, 200, 25, 50), 675.0)

	def test_insert_recalculates_available_despite_wrong_input(self):
		"""Validate hook overwrites hand-supplied available with derived value."""
		doc = self._line_doc(
			"_KT_BUD06_L1",
			allocated_amount=1000,
			reserved_amount=100,
			committed_amount=200,
			released_amount=25,
			consumed_actual_amount=50,
			available_amount=99999,
		)
		doc.insert()
		self.assertEqual(float(doc.available_amount), 675.0)
		reloaded = frappe.get_doc(BL, doc.name)
		self.assertEqual(float(reloaded.available_amount), 675.0)

	def test_on_budget_ledger_post_recalculate_line(self):
		"""Simulate ledger updating component fields via db_set, then refresh derived total."""
		doc = self._line_doc("_KT_BUD06_L2", allocated_amount=500).insert()
		frappe.db.set_value(
			BL,
			doc.name,
			{
				"reserved_amount": 50,
				"committed_amount": 100,
				"released_amount": 10,
				"consumed_actual_amount": 40,
			},
		)
		on_budget_ledger_post_recalculate_line(doc.name)
		frappe.db.commit()
		reloaded = frappe.get_doc(BL, doc.name)
		# 500 - 50 - 100 - 40 + 10 = 320
		self.assertEqual(float(reloaded.available_amount), 320.0)

	def test_recalculate_budget_line_derived_totals_idempotent(self):
		doc = self._line_doc("_KT_BUD06_L3", allocated_amount=100)
		recalculate_budget_line_derived_totals(doc)
		self.assertEqual(float(doc.available_amount), 100.0)
		doc.reserved_amount = 30
		recalculate_budget_line_derived_totals(doc)
		self.assertEqual(float(doc.available_amount), 70.0)
