# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.business_id_generation import generate_business_id


class TestBusinessIdGeneration(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete("Series", {"name": ("like", "KT-RNP-_KT_M7_%")})
		frappe.db.delete("Reference Number Policy", {"policy_code": ("like", "_KT_M7_%")})
		frappe.db.commit()
		super().tearDown()

	def _policy_a(self):
		return frappe.get_doc(
			{
				"doctype": "Reference Number Policy",
				"policy_code": "_KT_M7_A",
				"target_doctype": "Purchase Order",
				"pattern": "PO-{####}",
				"entity_scoped": 0,
				"fiscal_year_scoped": 0,
				"active": 1,
			}
		)

	def _policy_b(self):
		return frappe.get_doc(
			{
				"doctype": "Reference Number Policy",
				"policy_code": "_KT_M7_B",
				"target_doctype": "Requisition",
				"pattern": "{entity}-FY{fy}-{###}",
				"entity_scoped": 1,
				"fiscal_year_scoped": 1,
				"active": 1,
			}
		)

	def test_scenario_a_global_sequence_increments(self):
		self._policy_a().insert()
		first = generate_business_id("_KT_M7_A")
		second = generate_business_id("_KT_M7_A")
		self.assertEqual(first, "PO-0001")
		self.assertEqual(second, "PO-0002")

	def test_scenario_b_entity_and_fy_independent_sequences(self):
		self._policy_b().insert()
		a = generate_business_id(
			"_KT_M7_B", procuring_entity="MIN001", fiscal_year="2025"
		)
		b = generate_business_id(
			"_KT_M7_B", procuring_entity="MIN002", fiscal_year="2025"
		)
		self.assertEqual(a, "MIN001-FY2025-001")
		self.assertEqual(b, "MIN002-FY2025-001")

	def test_entity_scoped_requires_procuring_entity(self):
		self._policy_b().insert()
		self.assertRaises(
			frappe.ValidationError,
			lambda: generate_business_id("_KT_M7_B", fiscal_year="2025"),
		)
