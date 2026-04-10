# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE, log_audit_event


class TestAuditEventService(FrappeTestCase):
	def tearDown(self):
		# Append-only DocType blocks API delete; tests clean up via SQL.
		frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"event_type": ("like", "_KT_AUD_%")})
		frappe.db.commit()
		super().tearDown()

	def test_log_creates_row_with_hash(self):
		doc = log_audit_event(
			event_type="_KT_AUD_log",
			actor="Administrator",
			source_module="kentender",
			target_doctype="Procuring Entity",
			target_docname="TEST",
			actor_role="System Manager",
			changed_fields_summary="status",
			reason="integration test",
		)
		self.assertTrue(doc.name)
		self.assertEqual(doc.event_type, "_KT_AUD_log")
		self.assertTrue(doc.event_hash)
		self.assertEqual(len(doc.event_hash), 64)

	def test_update_blocked(self):
		doc = log_audit_event(event_type="_KT_AUD_upd", actor="Administrator")
		reloaded = frappe.get_doc(AUDIT_EVENT_DOCTYPE, doc.name)
		reloaded.event_type = "_KT_AUD_mutated"
		self.assertRaises(frappe.ValidationError, reloaded.save)

	def test_delete_blocked(self):
		doc = log_audit_event(event_type="_KT_AUD_del", actor="Administrator")
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, AUDIT_EVENT_DOCTYPE, doc.name)
