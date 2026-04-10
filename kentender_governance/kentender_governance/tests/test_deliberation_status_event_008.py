# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-008: Deliberation Status Event (append-only)."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV008"
DSE = "Deliberation Status Event"


class TestDeliberationStatusEvent008(FrappeTestCase):
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

	def test_KT_GOV008_create_sets_hash(self):
		doc = frappe.get_doc(
			{
				"doctype": DSE,
				"deliberation_session": self.session,
				"event_type": "Started",
				"event_datetime": now_datetime(),
				"actor_user": "Administrator",
				"summary": "Session opened.",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.event_hash)
		self.assertTrue(doc.display_label)

	def test_KT_GOV008_update_blocked_without_flag(self):
		doc = frappe.get_doc(
			{
				"doctype": DSE,
				"deliberation_session": self.session,
				"event_type": "Other",
				"event_datetime": now_datetime(),
				"summary": "Note",
			}
		).insert(ignore_permissions=True)
		doc.summary = "Changed"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_KT_GOV008_update_allowed_with_flag(self):
		doc = frappe.get_doc(
			{
				"doctype": DSE,
				"deliberation_session": self.session,
				"event_type": "Completed",
				"event_datetime": now_datetime(),
				"summary": "End",
			}
		).insert(ignore_permissions=True)
		frappe.flags.allow_deliberation_status_event_mutate = True
		try:
			doc.summary = "Adjusted under test flag"
			doc.save(ignore_permissions=True)
		finally:
			frappe.flags.allow_deliberation_status_event_mutate = False

	def test_KT_GOV008_delete_blocked_without_flag(self):
		doc = frappe.get_doc(
			{
				"doctype": DSE,
				"deliberation_session": self.session,
				"event_type": "Scheduled",
				"event_datetime": now_datetime(),
				"summary": "Planned",
			}
		).insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, DSE, doc.name, ignore_permissions=True)
