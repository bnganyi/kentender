# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

DOCTYPE = "Notification Template"


class TestNotificationTemplate(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete(DOCTYPE, {"template_code": ("like", "_KT_NT_%")})
		frappe.db.commit()
		super().tearDown()

	def _doc(self, template_code: str = "_KT_NT_001", **kwargs):
		data = {
			"doctype": DOCTYPE,
			"template_code": template_code,
			"template_name": "Test notification template",
			"channel": "Email",
			"event_name": "test.event.created",
			"scope_type": "Global",
			"subject_template": "Hello {{ name }}",
			"body_template": "<p>Body for {{ name }}</p>",
		}
		data.update(kwargs)
		return frappe.get_doc(data)

	def test_valid_create(self):
		doc = self._doc()
		doc.insert()
		self.assertEqual(doc.name, "_KT_NT_001")
		self.assertTrue(doc.active)
		self.assertEqual(doc.channel, "Email")

	def test_duplicate_template_code_blocked(self):
		self._doc().insert()
		dup = self._doc()
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_strip_template_code_on_save(self):
		doc = self._doc(template_code="  _KT_NT_TRIM  ")
		doc.insert()
		self.assertEqual(doc.template_code, "_KT_NT_TRIM")
