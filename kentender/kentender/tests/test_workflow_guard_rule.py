# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

DOCTYPE = "Workflow Guard Rule"


class TestWorkflowGuardRule(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete(DOCTYPE, {"rule_code": ("like", "_KT_WGR_%")})
		frappe.db.commit()
		super().tearDown()

	def _doc(self, rule_code: str = "_KT_WGR_001", **kwargs):
		data = {
			"doctype": DOCTYPE,
			"rule_code": rule_code,
			"rule_name": "Test workflow guard",
			"applies_to_doctype": "Exception Record",
			"event_name": "pre_submit",
			"rule_type": "Validate",
			"severity": "Medium",
			"evaluation_order": 100,
			"exception_policy": "Block",
			"active": 1,
		}
		data.update(kwargs)
		return frappe.get_doc(data)

	def test_valid_create(self):
		doc = self._doc()
		doc.insert()
		self.assertEqual(doc.name, "_KT_WGR_001")

	def test_duplicate_rule_code_blocked(self):
		self._doc().insert()
		dup = self._doc()
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_negative_evaluation_order_blocked(self):
		doc = self._doc(rule_code="_KT_WGR_NEG", evaluation_order=-1)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_duplicate_evaluation_order_same_scope_blocked(self):
		self._doc(rule_code="_KT_WGR_A", evaluation_order=50).insert()
		dup = self._doc(rule_code="_KT_WGR_B", evaluation_order=50)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_same_order_allowed_different_event(self):
		self._doc(rule_code="_KT_WGR_E1", event_name="pre_submit", evaluation_order=10).insert()
		doc2 = self._doc(rule_code="_KT_WGR_E2", event_name="pre_approve", evaluation_order=10)
		doc2.insert()
		self.assertEqual(doc2.evaluation_order, 10)

	def test_same_order_allowed_different_doctype(self):
		self._doc(
			rule_code="_KT_WGR_D1",
			applies_to_doctype="Procuring Entity",
			evaluation_order=20,
		).insert()
		doc2 = self._doc(rule_code="_KT_WGR_D2", evaluation_order=20)
		doc2.insert()
