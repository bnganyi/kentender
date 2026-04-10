# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.services.budget_availability import get_budget_availability
from kentender_budget.services.budget_ledger_posting import (
	commit_budget,
	release_reservation,
	reserve_budget,
)
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

BL = "Budget Line"
BUD = "Budget"
BCP = "Budget Control Period"
BLE = "Budget Ledger Entry"
AUD = "KenTender Audit Event"


class TestBudgetAvailability(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BAV_PE").insert()
		self.period = _bcp(
			"_KT_BAV_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BAV_BG", self.entity.name, self.period.name, self.currency).insert()
		self.line = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_BAV_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 5000,
			}
		).insert()

	def tearDown(self):
		frappe.db.delete(AUD, {"target_docname": self.line.name, "target_doctype": BL})
		frappe.db.delete(BLE, {"budget_line": self.line.name})
		frappe.db.delete(BL, {"name": ("like", "_KT_BAV_%")})
		frappe.db.delete(BUD, {"name": ("like", "_KT_BAV_%")})
		frappe.db.delete(BCP, {"name": ("like", "_KT_BAV_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BAV_%")})
		frappe.db.commit()
		super().tearDown()

	def _src(self, action: str):
		return {"source_doctype": "Test", "source_docname": "X", "source_action": action}

	def test_initial_empty_ledger(self):
		b = get_budget_availability(self.line.name)
		self.assertAlmostEqual(b.allocated, 5000.0)
		self.assertAlmostEqual(b.reserved, 0.0)
		self.assertAlmostEqual(b.committed, 0.0)
		self.assertAlmostEqual(b.released, 0.0)
		self.assertAlmostEqual(b.available, 5000.0)

	def test_after_reservation(self):
		reserve_budget(self.line.name, 300, **self._src("r"))
		b = get_budget_availability(self.line.name)
		self.assertAlmostEqual(b.reserved, 300.0)
		self.assertAlmostEqual(b.available, 4700.0)

	def test_release_reservation_effect(self):
		reserve_budget(self.line.name, 400, **self._src("r"))
		release_reservation(self.line.name, 100, **self._src("rr"))
		b = get_budget_availability(self.line.name)
		self.assertAlmostEqual(b.reserved, 300.0)
		self.assertAlmostEqual(b.released, 100.0)
		self.assertAlmostEqual(b.available, 4800.0)

	def test_mixed_sequence(self):
		reserve_budget(self.line.name, 1000, **self._src("r"))
		release_reservation(self.line.name, 200, **self._src("rr"))
		commit_budget(self.line.name, 300, from_reservation=True, **self._src("c"))
		b = get_budget_availability(self.line.name)
		self.assertAlmostEqual(b.reserved, 500.0)
		self.assertAlmostEqual(b.committed, 300.0)
		self.assertAlmostEqual(b.released, 200.0)

	def test_as_of_datetime_excludes_later_rows(self):
		t0 = add_to_date(now_datetime(), days=-2)
		t1 = add_to_date(now_datetime(), days=-1)
		line = frappe.get_doc(BL, self.line.name)
		frappe.get_doc(
			{
				"doctype": BLE,
				"name": "_KT_BAV_E1",
				"budget_line": line.name,
				"budget": line.budget,
				"procuring_entity": line.procuring_entity,
				"fiscal_year": line.fiscal_year,
				"currency": line.currency,
				"entry_type": "Reserve",
				"entry_direction": "In",
				"amount": 100,
				"posting_datetime": t0,
				"status": "Posted",
				"source_doctype": "Test",
				"source_docname": "A",
				"source_action": "a",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": BLE,
				"name": "_KT_BAV_E2",
				"budget_line": line.name,
				"budget": line.budget,
				"procuring_entity": line.procuring_entity,
				"fiscal_year": line.fiscal_year,
				"currency": line.currency,
				"entry_type": "Reserve",
				"entry_direction": "In",
				"amount": 50,
				"posting_datetime": t1,
				"status": "Posted",
				"source_doctype": "Test",
				"source_docname": "B",
				"source_action": "b",
			}
		).insert(ignore_permissions=True)
		mid = add_to_date(t0, hours=12)
		b_mid = get_budget_availability(self.line.name, as_of_datetime=mid)
		self.assertAlmostEqual(b_mid.reserved, 100.0)
		b_all = get_budget_availability(self.line.name)
		self.assertAlmostEqual(b_all.reserved, 150.0)
