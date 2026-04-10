# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-003: Deliberation Attendance."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV003"
DT = "Deliberation Attendance"


class TestDeliberationAttendance003(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		self.pe = make_procuring_entity(f"{PREFIX}_PE")
		self.session = make_deliberation_session(
			business_id=f"{PREFIX}_S1", procuring_entity=self.pe.name
		)

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV003_internal_attendee_with_user(self):
		doc = frappe.get_doc(
			{
				"doctype": DT,
				"deliberation_session": self.session,
				"user": "Administrator",
				"attendee_name": "Administrator",
				"role_type": "Chair",
				"attendance_status": "Confirmed",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.display_label)

	def test_KT_GOV003_external_attendee_without_user(self):
		doc = frappe.get_doc(
			{
				"doctype": DT,
				"deliberation_session": self.session,
				"attendee_name": "External Guest Ltd",
				"role_type": "External",
				"attendance_status": "Invited",
			}
		).insert(ignore_permissions=True)
		self.assertFalse(doc.user)
		self.assertEqual(doc.attendee_name, "External Guest Ltd")

	def test_KT_GOV003_invalid_user_blocked(self):
		row = {
			"doctype": DT,
			"deliberation_session": self.session,
			"user": "nonexistent_user_gov003_xx",
			"attendee_name": "X",
			"role_type": "Member",
			"attendance_status": "Invited",
		}
		self.assertRaises(frappe.ValidationError, frappe.get_doc(row).insert, ignore_permissions=True)
