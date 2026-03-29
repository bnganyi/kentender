# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.services.budget_ledger_posting import reserve_budget
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

AUD = "KenTender Audit Event"
BLE = "Budget Ledger Entry"
BL = "Budget Line"
BUD = "Budget"
BCP = "Budget Control Period"


class TestBudgetLedgerIdempotency(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BID_PE").insert()
		self.period = _bcp(
			"_KT_BID_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BID_BG", self.entity.name, self.period.name, self.currency).insert()
		self.line = frappe.get_doc(
			{
				"doctype": BL,
				"business_id": "_KT_BID_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 10000,
			}
		).insert()

	def tearDown(self):
		frappe.db.delete(AUD, {"target_docname": self.line.name, "target_doctype": BL})
		frappe.db.delete(BLE, {"budget_line": self.line.name})
		frappe.db.delete(BL, {"business_id": ("like", "_KT_BID_%")})
		frappe.db.delete(BUD, {"business_id": ("like", "_KT_BID_%")})
		frappe.db.delete(BCP, {"business_id": ("like", "_KT_BID_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BID_%")})
		frappe.db.commit()
		super().tearDown()

	def _src(self, action: str):
		return {"source_doctype": "Test", "source_docname": "IDM", "source_action": action}

	def test_duplicate_idempotency_key_returns_same_entry(self):
		key = "_KT_BID_IDEM_001"
		a = reserve_budget(
			self.line.name,
			120,
			idempotency_key=key,
			**self._src("r1"),
		)
		b = reserve_budget(
			self.line.name,
			120,
			idempotency_key=key,
			**self._src("r1_retry"),
		)
		self.assertEqual(a, b)
		self.assertEqual(frappe.db.count(BLE, {"budget_line": self.line.name}), 1)

	def test_second_idempotent_call_does_not_duplicate_audit(self):
		key = "_KT_BID_IDEM_002"
		reserve_budget(self.line.name, 40, idempotency_key=key, **self._src("r"))
		before = frappe.db.count(AUD, {"event_type": "kt.budget.ledger.reserve", "target_docname": self.line.name})
		reserve_budget(self.line.name, 40, idempotency_key=key, **self._src("r_retry"))
		after = frappe.db.count(AUD, {"event_type": "kt.budget.ledger.reserve", "target_docname": self.line.name})
		self.assertEqual(after, before)
