# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""BUD-016 — Budget module integration tests.

Granular rules live in ``test_budget_*.py`` modules. This file stitches **critical paths**
across Budget Control Period, Budget header, Budget Line, ledger posting, availability,
revision apply, and downstream validation APIs.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cint, flt

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

from kentender_budget.services.budget_downstream import (
	get_budget_availability,
	validate_budget_line,
	validate_funds_or_raise,
)
from kentender_budget.services.budget_revision_apply import apply_budget_revision
from kentender_budget.services.budget_ledger_posting import (
	commit_budget,
	release_commitment,
	reserve_budget,
)
from kentender_budget.tests.test_budget import _budget
from kentender_budget.tests.test_budget_control_period import _bcp

AUD = "KenTender Audit Event"
BA = "Budget Allocation"
BL = "Budget Line"
BR = "Budget Revision"
BLE = "Budget Ledger Entry"
BUD = "Budget"
BCP = "Budget Control Period"


def _cleanup_b016():
	line_names = frappe.get_all(BL, filters={"name": ("like", "_KT_B016%")}, pluck="name") or []
	for ln in line_names:
		frappe.db.delete(AUD, {"target_docname": ln})
	if line_names:
		alloc_names = frappe.get_all(BA, filters={"budget_line": ("in", line_names)}, pluck="name") or []
		for an in alloc_names:
			frappe.db.delete(AUD, {"target_docname": an})
		frappe.db.delete(BA, {"budget_line": ("in", line_names)})
		frappe.db.delete(BLE, {"budget_line": ("in", line_names)})
	rev_names = frappe.get_all(BR, filters={"name": ("like", "_KT_B016%")}, pluck="name") or []
	for rn in rev_names:
		frappe.db.delete(AUD, {"target_docname": rn})
	frappe.db.sql("delete from `tabKenTender Audit Event` where target_docname like '_KT_B016%%'")
	frappe.db.sql(
		"delete from `tabKenTender Audit Event` where target_docname like 'KT-BA-%%' and event_type = 'kt.budget.allocation.applied'"
	)
	for rn in rev_names:
		frappe.delete_doc(BR, rn, force=True, ignore_permissions=True)
	frappe.db.delete(BL, {"name": ("like", "_KT_B016%")})
	frappe.db.delete(BUD, {"name": ("like", "_KT_B016%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_B016%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_B016%")})
	frappe.db.commit()


class TestBudgetIntegrationBase(FrappeTestCase):
	"""Shared fixture: entity, open period, budget v1, one budget line."""

	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		self.entity = _make_entity("_KT_B016_PE").insert()
		self.period = _bcp(
			"_KT_B016_BCP",
			self.entity.name,
			fiscal_year="2027-2028",
			start_date="2027-07-01",
			end_date="2028-06-30",
			status="Open",
		).insert()
		self.budget = _budget("_KT_B016_BG1", self.entity.name, self.period.name, self.currency).insert()
		self.line = frappe.get_doc(
			{
				"doctype": BL,
				"name": "_KT_B016_LINE",
				"budget": self.budget.name,
				"budget_line_type": "Operating",
				"status": "Draft",
				"allocated_amount": 100_000,
			}
		).insert()

	def tearDown(self):
		_cleanup_b016()
		super().tearDown()


class TestBudgetEncumbranceAndDownstreamIntegration(TestBudgetIntegrationBase):
	def test_reserve_commit_release_matches_availability_and_downstream(self):
		validate_budget_line(self.line.name, self.entity.name)
		validate_funds_or_raise(self.line.name, 10_000, "reserve", self.entity.name)
		reserve_budget(
			self.line.name,
			10_000,
			source_doctype="Integration",
			source_docname="E2E-1",
			source_action="reserve",
		)
		av = get_budget_availability(self.line.name)
		self.assertAlmostEqual(av.reserved, 10_000.0)
		self.assertAlmostEqual(av.available, 90_000.0)
		validate_funds_or_raise(self.line.name, 10_000, "commit_from_reserved", self.entity.name)
		commit_budget(
			self.line.name,
			4_000,
			from_reservation=True,
			source_doctype="Integration",
			source_docname="E2E-1",
			source_action="commit",
		)
		av2 = get_budget_availability(self.line.name)
		self.assertAlmostEqual(av2.reserved, 6_000.0)
		self.assertAlmostEqual(av2.committed, 4_000.0)
		release_commitment(
			self.line.name,
			1_500,
			source_doctype="Integration",
			source_docname="E2E-1",
			source_action="relc",
		)
		av3 = get_budget_availability(self.line.name)
		self.assertAlmostEqual(av3.committed, 2_500.0)
		self.assertAlmostEqual(av3.released, 1_500.0)

	def test_downstream_blocks_oversized_reserve(self):
		self.assertRaises(
			frappe.ValidationError,
			validate_funds_or_raise,
			self.line.name,
			200_000,
			"reserve",
			self.entity.name,
		)


class TestBudgetRevisionWithLedgerIntegration(TestBudgetIntegrationBase):
	def test_revision_increase_after_reservation_keeps_encumbrance_consistent(self):
		reserve_budget(
			self.line.name,
			25_000,
			source_doctype="Integration",
			source_docname="REV-1",
			source_action="r",
		)
		rev = frappe.get_doc(
			{
				"doctype": BR,
				"name": "_KT_B016_REV1",
				"budget": self.budget.name,
				"procuring_entity": self.entity.name,
				"revision_type": "Supplementary",
				"status": "Approved",
				"lines": [
					{
						"change_type": "Increase",
						"change_amount": 20_000,
						"target_budget_line": self.line.name,
					},
				],
			}
		).insert()
		apply_budget_revision(rev.name)
		self.assertEqual(frappe.db.get_value(BR, rev.name, "status"), "Applied")
		new_alloc = flt(frappe.db.get_value(BL, self.line.name, "allocated_amount"))
		self.assertAlmostEqual(new_alloc, 120_000.0)
		av = get_budget_availability(self.line.name)
		self.assertAlmostEqual(av.reserved, 25_000.0)
		self.assertAlmostEqual(av.available, 95_000.0)


class TestBudgetHeaderVersionIntegration(FrappeTestCase):
	def tearDown(self):
		_cleanup_b016()
		super().tearDown()

	def test_only_one_current_active_budget_per_period(self):
		currency = _ensure_test_currency()
		entity = _make_entity("_KT_B016_PEV").insert()
		period = _bcp(
			"_KT_B016_BCPV",
			entity.name,
			fiscal_year="2028-2029",
			start_date="2028-07-01",
			end_date="2029-06-30",
		).insert()
		b1 = _budget(
			"_KT_B016_V1",
			entity.name,
			period.name,
			currency,
			version_no=1,
			is_current_active_version=1,
		).insert()
		b2 = _budget(
			"_KT_B016_V2",
			entity.name,
			period.name,
			currency,
			version_no=2,
			is_current_active_version=1,
		).insert()
		self.assertEqual(cint(frappe.db.get_value(BUD, b1.name, "is_current_active_version")), 0)
		self.assertEqual(cint(frappe.db.get_value(BUD, b2.name, "is_current_active_version")), 1)


class TestBudgetLineDownstreamEntityIntegration(TestBudgetIntegrationBase):
	def test_validate_budget_line_rejects_wrong_entity(self):
		ent2 = _make_entity("_KT_B016_PE2").insert()
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
