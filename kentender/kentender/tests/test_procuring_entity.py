# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase


def _ensure_test_currency() -> str:
	code = "_KT_TEST_CURRENCY"
	if not frappe.db.exists("Currency", code):
		frappe.get_doc(
			{
				"doctype": "Currency",
				"currency_name": code,
				"enabled": 1,
				"symbol": "T",
			}
		).insert(ignore_permissions=True)
	return code


def _make_entity(entity_code: str, **kwargs):
	curr = kwargs.pop("default_currency", None) or _ensure_test_currency()
	doc = frappe.get_doc(
		{
			"doctype": "Procuring Entity",
			"entity_code": entity_code,
			"entity_name": kwargs.pop("entity_name", f"Entity {entity_code}"),
			"entity_type": kwargs.pop("entity_type", "Other"),
			"default_currency": curr,
			**kwargs,
		}
	)
	return doc


class TestProcuringEntity(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()

	def tearDown(self):
		frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PE_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_create(self):
		doc = _make_entity("_KT_PE_ROOT")
		doc.insert()
		self.assertEqual(doc.name, "_KT_PE_ROOT")
		self.assertFalse(doc.parent_entity)

	def test_duplicate_entity_code_blocked(self):
		_make_entity("_KT_PE_DUP").insert()
		dup = _make_entity("_KT_PE_DUP")
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_self_parent_blocked(self):
		doc = _make_entity("_KT_PE_SELF", parent_entity="_KT_PE_SELF")
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_circular_hierarchy_blocked(self):
		a = _make_entity("_KT_PE_A")
		a.insert()
		b = _make_entity("_KT_PE_B", parent_entity="_KT_PE_A")
		b.insert()
		a.parent_entity = "_KT_PE_B"
		self.assertRaises(frappe.ValidationError, a.save)
