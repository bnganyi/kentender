# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.sensitivity_classification import (
	CANONICAL_SENSITIVITY_CLASSES,
	is_publicly_disclosable,
	is_sealed,
	is_sensitive,
	normalize_sensitivity_class,
)
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup


def _cleanup_sc_data():
	frappe.db.delete(
		"KenTender Typed Attachment",
		{"owning_docname": "_KT_SC_PE"},
	)
	frappe.db.delete(
		"File",
		{
			"attached_to_doctype": "Procuring Entity",
			"attached_to_name": "_KT_SC_PE",
		},
	)
	frappe.db.delete("Document Type Registry", {"document_type_code": "_KT_SC_DT1"})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_SC_PE"})


class TestSensitivityClassificationHelpers(FrappeTestCase):
	def test_normalize_valid_and_whitespace(self):
		self.assertEqual(normalize_sensitivity_class(" Internal "), "Internal")
		self.assertEqual(normalize_sensitivity_class("Sealed Procurement"), "Sealed Procurement")

	def test_normalize_invalid(self):
		self.assertIsNone(normalize_sensitivity_class("Top Secret"))
		self.assertIsNone(normalize_sensitivity_class(""))
		self.assertIsNone(normalize_sensitivity_class("  "))
		self.assertIsNone(normalize_sensitivity_class(None))

	def test_is_sensitive(self):
		self.assertFalse(is_sensitive("Public"))
		for cls in ("Internal", "Confidential", "Restricted", "Sealed Procurement"):
			self.assertTrue(is_sensitive(cls), cls)
		self.assertTrue(is_sensitive("bogus"))
		self.assertTrue(is_sensitive(None))

	def test_is_sealed(self):
		self.assertTrue(is_sealed("Sealed Procurement"))
		self.assertFalse(is_sealed("Confidential"))
		self.assertFalse(is_sealed(None))

	def test_is_publicly_disclosable(self):
		self.assertTrue(is_publicly_disclosable("Public"))
		self.assertFalse(is_publicly_disclosable("Internal"))
		self.assertTrue(is_publicly_disclosable("Internal", public_disclosure_eligibility=True))
		self.assertFalse(is_publicly_disclosable("nope"))
		self.assertFalse(is_publicly_disclosable("Internal", public_disclosure_eligibility=False))

	def test_canonical_tuple_order_stable(self):
		self.assertEqual(
			CANONICAL_SENSITIVITY_CLASSES,
			("Public", "Internal", "Confidential", "Restricted", "Sealed Procurement"),
		)


class TestKenTenderTypedAttachmentSensitivityValidation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		run_test_db_cleanup(_cleanup_sc_data)
		self.entity = _make_entity("_KT_SC_PE")
		self.entity.insert()
		self.dt = frappe.get_doc(
			{
				"doctype": "Document Type Registry",
				"document_type_code": "_KT_SC_DT1",
				"document_type_name": "Sensitivity Test Doc Type",
			}
		)
		self.dt.insert()
		self.file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "_kt_sc_test.txt",
				"content": b"x",
				"attached_to_doctype": "Procuring Entity",
				"attached_to_name": self.entity.name,
			}
		)
		self.file_doc.insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_sc_data)
		super().tearDown()

	def test_invalid_sensitivity_class_rejected(self):
		doc = frappe.get_doc(
			{
				"doctype": "KenTender Typed Attachment",
				"document_type": self.dt.name,
				"attached_file": self.file_doc.name,
				"sensitivity_class": "Ultra Secret",
				"owning_doctype": "Procuring Entity",
				"owning_docname": self.entity.name,
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
