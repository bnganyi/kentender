# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.services.budget_revision_apply import apply_budget_revision
from kentender_budget.services.budget_ledger_posting import reserve_budget
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

AUD = "KenTender Audit Event"
BA = "Budget Allocation"
BL = "Budget Line"
BR = "Budget Revision"
BLE = "Budget Ledger Entry"
BUD = "Budget"
BCP = "Budget Control Period"


class TestBudgetAuditIntegration(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_BAU_PE").insert()
		self.period = _bcp(
			"_KT_BAU_BCP",
			self.entity.name,
			fiscal_year="2026-2027",
			start_date="2026-07-01",
			end_date="2027-06-30",
		).insert()
		self.budget = _budget("_KT_BAU_BG", self.entity.name, self.period.name, self.currency).insert()
		self.line = frappe.get_doc(
			{
				"doctype": BL,
				"business_id": "_KT_BAU_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 6000,
			}
		).insert()

	def tearDown(self):
		frappe.db.sql(
			"delete from `tabKenTender Audit Event` where business_id like '_KT_BAU%%' or business_id like 'KT-BA-%%'"
		)
		frappe.db.delete(BA, {"budget_line": self.line.name})
		frappe.db.delete(BLE, {"budget_line": self.line.name})
		for name in frappe.get_all(BR, filters={"business_id": ("like", "_KT_BAU_%")}, pluck="name") or []:
			frappe.delete_doc(BR, name, force=True, ignore_permissions=True)
		frappe.db.delete(BL, {"business_id": ("like", "_KT_BAU_%")})
		frappe.db.delete(BUD, {"business_id": ("like", "_KT_BAU_%")})
		frappe.db.delete(BCP, {"business_id": ("like", "_KT_BAU_%")})
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_BAU_%")})
		frappe.db.commit()
		super().tearDown()

	def test_ledger_reserve_emits_audit(self):
		before = frappe.db.count(AUD, {"event_type": "kt.budget.ledger.reserve"})
		reserve_budget(
			self.line.name,
			20,
			source_doctype="Test",
			source_docname="aud",
			source_action="r",
		)
		after = frappe.db.count(AUD, {"event_type": "kt.budget.ledger.reserve"})
		self.assertEqual(after, before + 1)

	def test_revision_apply_emits_revision_and_allocation_audits(self):
		rev = frappe.get_doc(
			{
				"doctype": BR,
				"business_id": "_KT_BAU_R1",
				"budget": self.budget.name,
				"procuring_entity": self.entity.name,
				"revision_type": "Adjustment",
				"status": "Approved",
				"lines": [
					{
						"change_type": "Increase",
						"change_amount": 50,
						"target_budget_line": self.line.name,
					},
				],
			}
		).insert()
		br_before = frappe.db.count(AUD, {"event_type": "kt.budget.revision.applied"})
		ba_before = frappe.db.count(AUD, {"event_type": "kt.budget.allocation.applied"})
		apply_budget_revision(rev.name)
		self.assertEqual(
			frappe.db.count(AUD, {"event_type": "kt.budget.revision.applied"}),
			br_before + 1,
		)
		self.assertEqual(
			frappe.db.count(AUD, {"event_type": "kt.budget.allocation.applied"}),
			ba_before + 1,
		)
