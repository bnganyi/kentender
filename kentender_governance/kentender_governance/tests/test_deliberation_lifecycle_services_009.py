# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-009: deliberation lifecycle services."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.services.deliberation_lifecycle_services import (
	complete_deliberation_session,
	lock_deliberation_session,
	schedule_deliberation_session,
	start_deliberation_session,
)
from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV009"
DS = "Deliberation Session"
DSE = "Deliberation Status Event"


class TestDeliberationLifecycleServices009(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		self.pe = make_procuring_entity(f"{PREFIX}_PE")
		self.session_name = make_deliberation_session(
			business_id=f"{PREFIX}_S1", procuring_entity=self.pe.name
		)

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		super().tearDown()

	def _events(self):
		return frappe.get_all(
			DSE,
			filters={"deliberation_session": self.session_name},
			fields=["event_type"],
			order_by="creation asc",
		)

	def test_KT_GOV009_happy_path_lifecycle_and_events(self):
		schedule_deliberation_session(self.session_name, actor_user="Administrator")
		self.assertEqual(frappe.db.get_value(DS, self.session_name, "status"), "Scheduled")
		types = [r.event_type for r in self._events()]
		self.assertEqual(types, ["Scheduled"])

		start_deliberation_session(self.session_name, actor_user="Administrator")
		self.assertEqual(frappe.db.get_value(DS, self.session_name, "status"), "In Progress")
		types = [r.event_type for r in self._events()]
		self.assertEqual(types, ["Scheduled", "Started"])

		complete_deliberation_session(self.session_name, actor_user="Administrator")
		self.assertEqual(frappe.db.get_value(DS, self.session_name, "status"), "Completed")
		types = [r.event_type for r in self._events()]
		self.assertEqual(types, ["Scheduled", "Started", "Completed"])

		lock_deliberation_session(self.session_name, actor_user="Administrator")
		self.assertEqual(int(frappe.db.get_value(DS, self.session_name, "session_locked") or 0), 1)
		types = [r.event_type for r in self._events()]
		self.assertEqual(types, ["Scheduled", "Started", "Completed", "Locked"])

	def test_KT_GOV009_start_from_draft_fails(self):
		self.assertRaises(frappe.ValidationError, start_deliberation_session, self.session_name)

	def test_KT_GOV009_complete_from_scheduled_fails(self):
		schedule_deliberation_session(self.session_name)
		self.assertRaises(frappe.ValidationError, complete_deliberation_session, self.session_name)

	def test_KT_GOV009_schedule_when_locked_fails(self):
		schedule_deliberation_session(self.session_name)
		start_deliberation_session(self.session_name)
		complete_deliberation_session(self.session_name)
		lock_deliberation_session(self.session_name)
		self.assertRaises(frappe.ValidationError, schedule_deliberation_session, self.session_name)

	def test_KT_GOV009_lock_idempotent(self):
		schedule_deliberation_session(self.session_name)
		start_deliberation_session(self.session_name)
		complete_deliberation_session(self.session_name)
		lock_deliberation_session(self.session_name)
		lock_deliberation_session(self.session_name)
		self.assertEqual(len(self._events()), 4)

	def test_KT_GOV009_reschedule_updates_datetime(self):
		new_dt = add_to_date(now_datetime(), days=3)
		schedule_deliberation_session(self.session_name, scheduled_datetime=new_dt)
		got = frappe.db.get_value(DS, self.session_name, "scheduled_datetime")
		self.assertEqual(str(got)[:16], str(new_dt)[:16])
