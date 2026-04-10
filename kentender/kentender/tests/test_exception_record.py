# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup


def _cleanup_exc_data():
	frappe.db.delete("Exception Record", {"name": ("like", "_KT_EXC_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_EXC_PE"})


def _make_exception(business_id: str, entity_name: str, **kwargs):
	return frappe.get_doc(
		{
			"doctype": "Exception Record",
			"name": business_id,
			"exception_type": kwargs.pop("exception_type", "Other"),
			"procuring_entity": entity_name,
			"triggered_by": kwargs.pop("triggered_by", "Administrator"),
			"justification": kwargs.pop(
				"justification",
				"This is a valid justification text for the exception record.",
			),
			**kwargs,
		}
	)


class TestExceptionRecord(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		run_test_db_cleanup(_cleanup_exc_data)
		self.entity = _make_entity("_KT_EXC_PE")
		self.entity.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_exc_data)
		super().tearDown()

	def test_valid_create_with_related_link(self):
		doc = _make_exception(
			"_KT_EXC_001",
			self.entity.name,
			related_doctype="Procuring Entity",
			related_docname=self.entity.name,
		)
		doc.insert()
		self.assertEqual(doc.name, "_KT_EXC_001")
		self.assertEqual(doc.approval_status, "Draft")

	def test_invalid_related_doc_missing(self):
		doc = _make_exception(
			"_KT_EXC_002",
			self.entity.name,
			related_doctype="Procuring Entity",
			related_docname="NONEXISTENT-ENTITY-XYZ",
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_related_pair_must_be_complete(self):
		doc = _make_exception(
			"_KT_EXC_003",
			self.entity.name,
			related_doctype="Procuring Entity",
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_short_justification_blocked(self):
		doc = _make_exception(
			"_KT_EXC_004",
			self.entity.name,
			justification="short",
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_duplicate_business_id_blocked(self):
		_make_exception("_KT_EXC_005", self.entity.name).insert()
		dup = _make_exception("_KT_EXC_005", self.entity.name)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_effective_period_order(self):
		doc = _make_exception(
			"_KT_EXC_006",
			self.entity.name,
			effective_from="2026-12-31",
			effective_to="2026-01-01",
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
