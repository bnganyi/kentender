# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.services.budget_availability import aggregate_ledger_buckets, availability_headroom
from kentender_budget.services.budget_ledger_posting import (
	commit_budget,
	release_commitment,
	release_reservation,
	reserve_budget,
)
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

AUD = "KenTender Audit Event"
BLE = "Budget Ledger Entry"
BL = "Budget Line"
BUD = "Budget"
BCP = "Budget Control Period"


class TestBudgetLedgerPosting(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BLP_PE").insert()
		self.period = _bcp(
			"_KT_BLP_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BLP_BG", self.entity.name, self.period.name, self.currency).insert()
		self.line = frappe.get_doc(
			{
				"doctype": BL,
				"business_id": "_KT_BLP_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 10000,
			}
		).insert()

	def tearDown(self):
		frappe.db.delete(AUD, {"target_docname": self.line.name, "target_doctype": BL})
		frappe.db.delete(BLE, {"budget_line": self.line.name})
		frappe.db.delete(BL, {"business_id": ("like", "_KT_BLP_%")})
		frappe.db.delete(BUD, {"business_id": ("like", "_KT_BLP_%")})
		frappe.db.delete(BCP, {"business_id": ("like", "_KT_BLP_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BLP_%")})
		frappe.db.commit()
		super().tearDown()

	def _src(self, action: str):
		return {
			"source_doctype": "Test",
			"source_docname": "SRC-1",
			"source_action": action,
		}

	def test_reserve_success_and_totals(self):
		reserve_budget(self.line.name, 500, **self._src("r1"))
		r, c, rel = aggregate_ledger_buckets(self.line.name)
		self.assertAlmostEqual(r, 500.0)
		self.assertAlmostEqual(c, 0.0)
		line = frappe.get_doc(BL, self.line.name)
		self.assertAlmostEqual(float(line.reserved_amount), 500.0)
		self.assertAlmostEqual(float(line.available_amount), 9500.0)

	def test_reserve_insufficient_blocked(self):
		self.assertRaises(
			frappe.ValidationError,
			lambda: reserve_budget(self.line.name, 20000, **self._src("r_big")),
		)

	def test_release_reservation(self):
		reserve_budget(self.line.name, 800, **self._src("r1"))
		release_reservation(self.line.name, 300, **self._src("relr"))
		r, c, rel = aggregate_ledger_buckets(self.line.name)
		self.assertAlmostEqual(r, 500.0)
		self.assertAlmostEqual(rel, 300.0)

	def test_commit_from_reserved(self):
		reserve_budget(self.line.name, 1000, **self._src("r1"))
		commit_budget(self.line.name, 400, from_reservation=True, **self._src("c1"))
		r, c, _ = aggregate_ledger_buckets(self.line.name)
		self.assertAlmostEqual(r, 600.0)
		self.assertAlmostEqual(c, 400.0)

	def test_commit_from_available(self):
		commit_budget(self.line.name, 250, from_reservation=False, **self._src("cfa"))
		_, c, _ = aggregate_ledger_buckets(self.line.name)
		self.assertAlmostEqual(c, 250.0)
		self.assertAlmostEqual(availability_headroom(self.line.name), 9750.0)

	def test_release_commitment(self):
		commit_budget(self.line.name, 600, from_reservation=False, **self._src("cfa"))
		release_commitment(self.line.name, 200, **self._src("relc"))
		_, c, rel = aggregate_ledger_buckets(self.line.name)
		self.assertAlmostEqual(c, 400.0)
		self.assertAlmostEqual(rel, 200.0)

	def test_ledger_row_not_mutable_after_post(self):
		name = reserve_budget(self.line.name, 50, **self._src("r1"))
		doc = frappe.get_doc(BLE, name)
		doc.remarks = "x"
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_audit_event_emitted_on_reserve(self):
		before = frappe.db.count(AUD, {"event_type": "kt.budget.ledger.reserve", "target_docname": self.line.name})
		reserve_budget(self.line.name, 10, **self._src("aud"))
		after = frappe.db.count(AUD, {"event_type": "kt.budget.ledger.reserve", "target_docname": self.line.name})
		self.assertEqual(after, before + 1)
