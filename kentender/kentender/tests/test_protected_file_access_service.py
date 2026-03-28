# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.access_audit_service import EVENT_ACCESS_DENIED, EVENT_SENSITIVE_ACCESS
from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE
from kentender.services.protected_file_access_service import (
	TYPED_ATTACHMENT_DOCTYPE,
	get_bytes_for_typed_attachment,
)
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity

_AUDIT_PE = "_KT_C020_PE"


class TestProtectedFileAccessService(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity(_AUDIT_PE)
		self.entity.insert()
		self.dt = frappe.get_doc(
			{
				"doctype": "Document Type Registry",
				"document_type_code": "_KT_C020_DT",
				"document_type_name": "Protected access test",
			}
		)
		self.dt.insert()
		self.file_content = b"protected-file-access-secret"
		self.file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "_kt_c020.txt",
				"content": self.file_content,
				"attached_to_doctype": "Procuring Entity",
				"attached_to_name": self.entity.name,
			}
		)
		self.file_doc.insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"procuring_entity": _AUDIT_PE})
		frappe.db.delete(
			TYPED_ATTACHMENT_DOCTYPE,
			{"owning_docname": self.entity.name},
		)
		frappe.db.delete(
			"File",
			{
				"attached_to_doctype": "Procuring Entity",
				"attached_to_name": self.entity.name,
			},
		)
		frappe.db.delete("Document Type Registry", {"document_type_code": "_KT_C020_DT"})
		frappe.db.delete("Procuring Entity", {"entity_code": _AUDIT_PE})
		frappe.db.commit()
		super().tearDown()

	def _make_ta(self, sensitivity_class: str):
		doc = frappe.get_doc(
			{
				"doctype": TYPED_ATTACHMENT_DOCTYPE,
				"document_type": self.dt.name,
				"attached_file": self.file_doc.name,
				"sensitivity_class": sensitivity_class,
				"owning_doctype": "Procuring Entity",
				"owning_docname": self.entity.name,
			}
		)
		doc.insert()
		return doc

	def test_allowed_path_returns_bytes_and_logs_sensitive_access(self):
		ta = self._make_ta("Internal")
		before = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_SENSITIVE_ACCESS,
				"target_doctype": TYPED_ATTACHMENT_DOCTYPE,
				"target_docname": ta.name,
			},
		)
		data = get_bytes_for_typed_attachment(
			ta.name,
			access_action="read",
			permission_check=lambda _d: True,
			actor="Administrator",
			procuring_entity=_AUDIT_PE,
		)
		self.assertEqual(data, self.file_content)
		after = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_SENSITIVE_ACCESS,
				"target_doctype": TYPED_ATTACHMENT_DOCTYPE,
				"target_docname": ta.name,
			},
		)
		self.assertEqual(after, before + 1)

	def test_denied_path_logs_access_denied(self):
		ta = self._make_ta("Confidential")
		before = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_ACCESS_DENIED,
				"target_doctype": TYPED_ATTACHMENT_DOCTYPE,
				"target_docname": ta.name,
			},
		)
		self.assertRaises(
			frappe.PermissionError,
			lambda: get_bytes_for_typed_attachment(
				ta.name,
				permission_check=lambda _d: False,
				actor="Administrator",
				procuring_entity=_AUDIT_PE,
			),
		)
		after = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_ACCESS_DENIED,
				"target_doctype": TYPED_ATTACHMENT_DOCTYPE,
				"target_docname": ta.name,
			},
		)
		self.assertEqual(after, before + 1)

	def test_public_does_not_emit_sensitive_access(self):
		ta = self._make_ta("Public")
		before = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_SENSITIVE_ACCESS,
				"target_doctype": TYPED_ATTACHMENT_DOCTYPE,
				"target_docname": ta.name,
			},
		)
		data = get_bytes_for_typed_attachment(
			ta.name,
			permission_check=lambda _d: True,
			actor="Administrator",
			procuring_entity=_AUDIT_PE,
		)
		self.assertEqual(data, self.file_content)
		after = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_SENSITIVE_ACCESS,
				"target_doctype": TYPED_ATTACHMENT_DOCTYPE,
				"target_docname": ta.name,
			},
		)
		self.assertEqual(after, before)

	def test_missing_typed_attachment_logs_denial(self):
		missing = "nonexistenttypedattachment000"
		self.assertFalse(frappe.db.exists(TYPED_ATTACHMENT_DOCTYPE, missing))
		before = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_ACCESS_DENIED,
				"target_doctype": TYPED_ATTACHMENT_DOCTYPE,
				"target_docname": missing,
			},
		)
		self.assertRaises(
			frappe.PermissionError,
			lambda: get_bytes_for_typed_attachment(
				missing,
				permission_check=lambda _d: True,
				actor="Administrator",
				procuring_entity=_AUDIT_PE,
			),
		)
		after = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_ACCESS_DENIED,
				"target_doctype": TYPED_ATTACHMENT_DOCTYPE,
				"target_docname": missing,
			},
		)
		self.assertEqual(after, before + 1)
