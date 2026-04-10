# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-010: resolution and follow-up action services."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.services.deliberation_lifecycle_services import (
	complete_deliberation_session,
	lock_deliberation_session,
	schedule_deliberation_session,
	start_deliberation_session,
)
from kentender_governance.services.resolution_followup_services import (
	complete_follow_up_action,
	create_follow_up_action,
	issue_resolution,
)
from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV010"
DAI = "Deliberation Agenda Item"
DSE = "Deliberation Status Event"


class TestResolutionFollowupServices010(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		self.pe = make_procuring_entity(f"{PREFIX}_PE")
		self.session = make_deliberation_session(
			business_id=f"{PREFIX}_S1", procuring_entity=self.pe.name
		)
		self.agenda1 = frappe.get_doc(
			{
				"doctype": DAI,
				"deliberation_session": self.session,
				"item_no": 1,
				"title": "Topic A",
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		self.agenda2 = frappe.get_doc(
			{
				"doctype": DAI,
				"deliberation_session": self.session,
				"item_no": 2,
				"title": "Topic B",
				"status": "Open",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		super().tearDown()

	def _events(self):
		return frappe.get_all(
			DSE,
			filters={"deliberation_session": self.session},
			fields=["event_type"],
			order_by="creation asc",
		)

	def test_KT_GOV010_issue_create_complete_emits_events(self):
		res = issue_resolution(
			self.session,
			self.agenda1.name,
			"Resolved in favour of proceeding.",
			resolution_date=today(),
			actor_user="Administrator",
		)
		self.assertEqual(res.effective_status, "Effective")
		types = [r.event_type for r in self._events()]
		self.assertIn("ResolutionIssued", types)

		fua = create_follow_up_action(
			self.session,
			res.name,
			"Publish minutes",
			"Administrator",
			due_date=add_days(today(), 3),
			action_description="Board portal",
			actor_user="Administrator",
		)
		self.assertEqual(fua.status, "Open")
		types = [r.event_type for r in self._events()]
		self.assertEqual(types.count("Other"), 1)

		done = complete_follow_up_action(fua.name, completion_notes="Uploaded.", actor_user="Administrator")
		self.assertEqual(done.status, "Completed")
		types = [r.event_type for r in self._events()]
		self.assertEqual(types.count("Other"), 2)

	def test_KT_GOV010_issue_blocked_when_session_locked(self):
		issue_resolution(
			self.session,
			self.agenda1.name,
			"First resolution.",
			actor_user="Administrator",
		)
		schedule_deliberation_session(self.session)
		start_deliberation_session(self.session)
		complete_deliberation_session(self.session)
		lock_deliberation_session(self.session)

		self.assertRaises(
			frappe.ValidationError,
			issue_resolution,
			self.session,
			self.agenda2.name,
			"Should fail.",
			actor_user="Administrator",
		)

	def test_KT_GOV010_complete_follow_up_idempotent(self):
		res = issue_resolution(self.session, self.agenda1.name, "R.", actor_user="Administrator")
		fua = create_follow_up_action(
			self.session,
			res.name,
			"Task",
			"Administrator",
			due_date=today(),
			actor_user="Administrator",
		)
		a = complete_follow_up_action(fua.name, completion_notes="Done", actor_user="Administrator")
		b = complete_follow_up_action(fua.name, actor_user="Administrator")
		self.assertEqual(a.name, b.name)
		self.assertEqual(b.status, "Completed")
