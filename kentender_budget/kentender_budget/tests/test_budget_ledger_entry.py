# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

BLE = "Budget Ledger Entry"
BL = "Budget Line"
BUD = "Budget"
BCP = "Budget Control Period"


class TestBudgetLedgerEntry(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BLE_PE").insert()
		self.period = _bcp(
			"_KT_BLE_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BLE_BG", self.entity.name, self.period.name, self.currency).insert()
		self.line = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_BLE_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 10000,
			}
		).insert()

	def tearDown(self):
		frappe.db.delete(BLE, {"name": ("like", "_KT_BLE_%")})
		frappe.db.delete(BL, {"name": ("like", "_KT_BLE_%")})
		frappe.db.delete(BUD, {"name": ("like", "_KT_BLE_%")})
		frappe.db.delete(BCP, {"name": ("like", "_KT_BLE_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BLE_%")})
		frappe.db.commit()
		super().tearDown()

	def _entry(self, business_id: str, **kw):
		d = {
			"doctype": BLE,
			"name": business_id,
			"budget_line": self.line.name,
			"budget": self.budget.name,
			"procuring_entity": self.entity.name,
			"fiscal_year": self.period.fiscal_year,
			"currency": self.currency,
			"entry_type": "Reserve",
			"entry_direction": "In",
			"amount": 100,
			"posting_datetime": now_datetime(),
			"status": "Posted",
			"source_doctype": "Test",
			"source_docname": "DOC-1",
			"source_action": "test_reserve",
		}
		d.update(kw)
		return frappe.get_doc(d)

	def test_valid_posted_insert(self):
		doc = self._entry("_KT_BLE_E1").insert()
		self.assertTrue(doc.event_hash)
		self.assertEqual(doc.status, "Posted")

	def test_update_blocked(self):
		doc = self._entry("_KT_BLE_E2").insert()
		doc.remarks = "changed"
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_delete_blocked(self):
		doc = self._entry("_KT_BLE_E3").insert()
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, BLE, doc.name)

	def test_negative_amount_blocked(self):
		doc = self._entry("_KT_BLE_E4", amount=-1)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_missing_source_blocked(self):
		doc = self._entry("_KT_BLE_E5", source_docname="")
		self.assertRaises(frappe.ValidationError, doc.insert)
