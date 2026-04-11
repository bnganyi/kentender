# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-030: trace_procurement_chain service."""

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_governance.services.trace_procurement_chain import (
	resolve_procurement_contract,
	trace_procurement_chain,
)
from kentender_stores.tests.test_grn_doctypes_003_004 import cleanup_procurement_chain, minimal_procurement_contract

PREFIX = "_KT_GOV030"
PC = "Procurement Contract"
TENDER = "Tender"


def _cleanup():
	cleanup_procurement_chain(PREFIX)


class TestTraceProcurementChain030(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup)

	def tearDown(self):
		run_test_db_cleanup(_cleanup)
		super().tearDown()

	def test_KT_GOV030_resolve_and_trace_from_contract(self):
		if not frappe.db.exists("DocType", PC):
			raise unittest.SkipTest("Procurement Contract not available.")
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE").insert()
		_bcp(f"{PREFIX}_BCP", entity.name).insert()
		pc = minimal_procurement_contract(PREFIX, "T", entity.name, currency)

		self.assertEqual(resolve_procurement_contract(PC, pc.name), pc.name)

		out = trace_procurement_chain(PC, pc.name)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("anchor_contract"), pc.name)
		nodes = out["nodes"]
		self.assertIsNotNone(nodes.get("procurement_contract"))
		self.assertEqual(nodes["procurement_contract"]["name"], pc.name)
		self.assertIsNotNone(nodes.get("tender"))
		self.assertEqual(nodes["tender"]["name"], pc.tender)
		self.assertIsNotNone(nodes.get("evaluation_session"))
		self.assertIsNotNone(nodes.get("award_decision"))
		self.assertIsNotNone(nodes.get("bid_submission"))

	def test_KT_GOV030_trace_from_tender_entry(self):
		if not frappe.db.exists("DocType", PC):
			raise unittest.SkipTest("Procurement Contract not available.")
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE2").insert()
		_bcp(f"{PREFIX}_BCP2", entity.name).insert()
		pc = minimal_procurement_contract(PREFIX, "U", entity.name, currency)

		out = trace_procurement_chain(TENDER, pc.tender)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out["anchor_contract"], pc.name)

	def test_KT_GOV030_unsupported_type_raises(self):
		self.assertRaises(frappe.ValidationError, lambda: trace_procurement_chain("User", "Administrator"))
