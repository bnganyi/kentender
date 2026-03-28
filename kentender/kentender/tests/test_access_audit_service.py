# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.access_audit_service import (
	EVENT_ACCESS_DENIED,
	EVENT_SENSITIVE_ACCESS,
	log_access_denied,
	log_sensitive_access,
)
from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE


class TestAccessAuditService(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"target_docname": ("like", "_KT_A017_%")})
		frappe.db.commit()
		super().tearDown()

	def test_log_access_denied_creates_audit_event(self):
		doc = log_access_denied(
			resource_doctype="Procuring Entity",
			resource_name="_KT_A017_DENY",
			action="read",
			denial_reason="Insufficient permission for procurement officer role.",
			actor="Administrator",
		)
		self.assertTrue(doc.name)
		self.assertEqual(doc.event_type, EVENT_ACCESS_DENIED)
		self.assertEqual(doc.target_doctype, "Procuring Entity")
		self.assertEqual(doc.target_docname, "_KT_A017_DENY")
		self.assertTrue(doc.event_hash)
		self.assertIn("Access denied", doc.reason)
		payload = json.loads(doc.new_state)
		self.assertEqual(payload["action"], "read")
		self.assertIn("Insufficient", payload["denial_reason"])

	def test_log_sensitive_access_creates_audit_event(self):
		doc = log_sensitive_access(
			resource_doctype="Exception Record",
			resource_name="_KT_A017_SENS",
			access_action="view",
			actor="Administrator",
			sensitivity_class="Confidential",
			context="Treasurer desk view",
		)
		self.assertEqual(doc.event_type, EVENT_SENSITIVE_ACCESS)
		self.assertEqual(doc.target_docname, "_KT_A017_SENS")
		self.assertTrue(doc.event_hash)
		self.assertIn("Sensitive access", doc.reason)
		payload = json.loads(doc.new_state)
		self.assertEqual(payload["access_action"], "view")
		self.assertEqual(payload["sensitivity_class"], "Confidential")
		self.assertEqual(doc.changed_fields_summary, "Confidential")

	def test_log_access_denied_requires_reason(self):
		self.assertRaises(
			frappe.ValidationError,
			lambda: log_access_denied(
				resource_doctype="User",
				resource_name="u1",
				action="read",
				denial_reason="",
				actor="Administrator",
			),
		)
