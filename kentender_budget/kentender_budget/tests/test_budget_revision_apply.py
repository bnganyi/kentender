# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.services.budget_revision_apply import apply_budget_revision
from kentender_budget.services.budget_ledger_posting import reserve_budget
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp
from frappe.utils import flt

AUD = "KenTender Audit Event"
BA = "Budget Allocation"
BL = "Budget Line"
BR = "Budget Revision"
BLE = "Budget Ledger Entry"
BUD = "Budget"
BCP = "Budget Control Period"


class TestBudgetRevisionApply(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BRA_PE").insert()
		self.period = _bcp(
			"_KT_BRA_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BRA_BG", self.entity.name, self.period.name, self.currency).insert()
		self.line = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_BRA_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 5000,
			}
		).insert()

	def tearDown(self):
		frappe.db.sql(
			"delete from `tabKenTender Audit Event` where target_docname like '_KT_BRA%%' or (event_type = 'kt.budget.allocation.applied' and target_docname like 'KT-BA-%')"
		)
		frappe.db.delete(BA, {"budget_line": self.line.name})
		frappe.db.delete(BLE, {"budget_line": self.line.name})
		for name in frappe.get_all(BR, filters={"name": ("like", "_KT_BRA_%")}, pluck="name") or []:
			frappe.delete_doc(BR, name, force=True, ignore_permissions=True)
		frappe.db.delete(BL, {"name": ("like", "_KT_BRA_%")})
		frappe.db.delete(BUD, {"name": ("like", "_KT_BRA_%")})
		frappe.db.delete(BCP, {"name": ("like", "_KT_BRA_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BRA_%")})
		frappe.db.commit()
		super().tearDown()

	def _revision(self, business_id: str, status: str, lines: list):
		return frappe.get_doc(
			{
				"doctype": BR,
				"name": business_id,
				"budget": self.budget.name,
				"procuring_entity": self.entity.name,
				"revision_type": "Supplementary",
				"status": status,
				"lines": lines,
			}
		).insert()

	def test_apply_increase_success(self):
		rev = self._revision(
			"_KT_BRA_R1",
			"Approved",
			[
				{
					"change_type": "Increase",
					"change_amount": 200,
					"target_budget_line": self.line.name,
				},
			],
		)
		rev.reload()
		self.assertEqual(len(rev.lines), 1)
		before = flt(frappe.db.get_value(BL, self.line.name, "allocated_amount"))
		apply_budget_revision(rev.name)
		after = flt(frappe.db.get_value(BL, self.line.name, "allocated_amount"))
		self.assertAlmostEqual(after, before + 200)
		self.assertEqual(frappe.db.get_value(BR, rev.name, "status"), "Applied")

	def test_apply_draft_blocked(self):
		rev = self._revision(
			"_KT_BRA_R2",
			"Draft",
			[
				{
					"change_type": "Increase",
					"change_amount": 10,
					"target_budget_line": self.line.name,
				},
			],
		)
		self.assertRaises(frappe.ValidationError, apply_budget_revision, rev.name)

	def test_decrease_below_encumbrance_blocked(self):
		reserve_budget(
			self.line.name,
			4000,
			source_doctype="Test",
			source_docname="X",
			source_action="hold",
		)
		rev = self._revision(
			"_KT_BRA_R3",
			"Approved",
			[
				{
					"change_type": "Decrease",
					"change_amount": 2000,
					"source_budget_line": self.line.name,
				},
			],
		)
		self.assertRaises(frappe.ValidationError, apply_budget_revision, rev.name)

	def test_double_apply_blocked(self):
		rev = self._revision(
			"_KT_BRA_R4",
			"Approved",
			[
				{
					"change_type": "Increase",
					"change_amount": 5,
					"target_budget_line": self.line.name,
				},
			],
		)
		apply_budget_revision(rev.name)
		self.assertRaises(frappe.ValidationError, apply_budget_revision, rev.name)
