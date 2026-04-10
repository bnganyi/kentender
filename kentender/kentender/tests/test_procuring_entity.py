# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import time
from collections.abc import Callable

import frappe
from frappe.exceptions import QueryDeadlockError
from frappe.tests.utils import FrappeTestCase


def run_test_db_cleanup(cleanup: Callable[[], None], max_attempts: int = 8) -> None:
	"""Run cleanup (typically frappe.db.delete calls) then commit; retry on MariaDB deadlock.

	Shared-site integration tests can leave rows if a prior test errors, and bulk deletes
	can occasionally deadlock; repeating the whole cleanup after rollback is safe.
	"""
	for attempt in range(max_attempts):
		try:
			cleanup()
			frappe.db.commit()
			return
		except QueryDeadlockError:
			frappe.db.rollback()
			if attempt + 1 >= max_attempts:
				raise
			time.sleep(0.03 * (2**attempt))


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
		run_test_db_cleanup(lambda: frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PE_%")}))

	def tearDown(self):
		run_test_db_cleanup(lambda: frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PE_%")}))
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
