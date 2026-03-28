# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import hashlib

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity


class TestKenTenderTypedAttachment(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity("_KT_TA_PE")
		self.entity.insert()
		self.dt = frappe.get_doc(
			{
				"doctype": "Document Type Registry",
				"document_type_code": "_KT_TA_DT1",
				"document_type_name": "Typed Attachment Test Doc",
			}
		)
		self.dt.insert()
		self.file_content = b"ken tender typed attachment test bytes"
		self.file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "_kt_ta_test.txt",
				"content": self.file_content,
				"attached_to_doctype": "Procuring Entity",
				"attached_to_name": self.entity.name,
			}
		)
		self.file_doc.insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.delete(
			"KenTender Typed Attachment",
			{"owning_docname": self.entity.name},
		)
		frappe.db.delete(
			"File",
			{
				"attached_to_doctype": "Procuring Entity",
				"attached_to_name": self.entity.name,
			},
		)
		frappe.db.delete("Document Type Registry", {"document_type_code": "_KT_TA_DT1"})
		frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TA_PE"})
		frappe.db.commit()
		super().tearDown()

	def test_valid_create(self):
		doc = frappe.get_doc(
			{
				"doctype": "KenTender Typed Attachment",
				"document_type": self.dt.name,
				"attached_file": self.file_doc.name,
				"sensitivity_class": "Internal",
				"owning_doctype": "Procuring Entity",
				"owning_docname": self.entity.name,
			}
		)
		doc.insert()
		self.assertTrue(doc.name)
		self.assertEqual(doc.owning_doctype, "Procuring Entity")
		self.assertEqual(doc.owning_docname, self.entity.name)
		self.assertEqual(doc.attached_file, self.file_doc.name)
		self.assertTrue(doc.uploaded_at)
		self.assertTrue(doc.uploaded_by)
		expected_hash = hashlib.sha256(self.file_content).hexdigest()
		self.assertEqual(doc.file_hash, expected_hash)

	def test_invalid_owning_docname(self):
		doc = frappe.get_doc(
			{
				"doctype": "KenTender Typed Attachment",
				"document_type": self.dt.name,
				"attached_file": self.file_doc.name,
				"sensitivity_class": "Internal",
				"owning_doctype": "Procuring Entity",
				"owning_docname": "NONEXISTENT-ENTITY-XYZ",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
