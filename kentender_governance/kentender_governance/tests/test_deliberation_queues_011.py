# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-011: deliberation queue queries and script reports."""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from kentender.tests.test_procuring_entity import run_test_db_cleanup

from kentender_governance.services.deliberation_lifecycle_services import schedule_deliberation_session
from kentender_governance.services.deliberation_queue_queries import (
	get_deliberations_by_linked_object,
	get_open_follow_up_actions,
	get_resolution_register_rows,
	get_scheduled_deliberations,
)
from kentender_governance.services.resolution_followup_services import (
	create_follow_up_action,
	issue_resolution,
)
from kentender_governance.tests.gov_test_utils import cleanup_gov_chain, make_deliberation_session, make_procuring_entity

PREFIX = "_KT_GOV011"
DAI = "Deliberation Agenda Item"
DS = "Deliberation Session"

_REPORT_MODULES = (
	"kentender_governance.kentender_governance.report.scheduled_deliberations.scheduled_deliberations",
	"kentender_governance.kentender_governance.report.open_follow_up_actions.open_follow_up_actions",
	"kentender_governance.kentender_governance.report.resolution_register.resolution_register",
	"kentender_governance.kentender_governance.report.deliberations_by_linked_object.deliberations_by_linked_object",
)


def _exec_report(module_path: str, filters: dict):
	mod = importlib.import_module(module_path)
	return mod.execute(filters)


class TestDeliberationQueues011(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		self.pe = make_procuring_entity(f"{PREFIX}_PE")
		self.session = make_deliberation_session(
			business_id=f"{PREFIX}_S1", procuring_entity=self.pe.name
		)
		schedule_deliberation_session(self.session)
		self.agenda = frappe.get_doc(
			{
				"doctype": DAI,
				"deliberation_session": self.session,
				"item_no": 1,
				"title": "Item",
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		self.res = issue_resolution(
			self.session,
			self.agenda.name,
			"Resolved.",
			resolution_date=today(),
			actor_user="Administrator",
		)
		self.fua = create_follow_up_action(
			self.session,
			self.res.name,
			"Publish",
			"Administrator",
			due_date=add_days(today(), 5),
			actor_user="Administrator",
		)
		self.linked_session = make_deliberation_session(
			business_id=f"{PREFIX}_S2", procuring_entity=self.pe.name
		)
		frappe.db.set_value(
			DS,
			self.linked_session,
			{"linked_doctype": "User", "linked_docname": "Administrator"},
			update_modified=False,
		)

	def tearDown(self):
		run_test_db_cleanup(lambda: cleanup_gov_chain(PREFIX))
		super().tearDown()

	def test_KT_GOV011_query_scheduled_and_open_and_register(self):
		sd = get_scheduled_deliberations(procuring_entity=self.pe.name)
		self.assertTrue(any(r["name"] == self.session for r in sd))

		op = get_open_follow_up_actions(procuring_entity=self.pe.name)
		self.assertTrue(any(r["name"] == self.fua.name for r in op))

		rr = get_resolution_register_rows(procuring_entity=self.pe.name)
		self.assertTrue(any(r["name"] == self.res.name for r in rr))

	def test_KT_GOV011_query_linked_object(self):
		rows = get_deliberations_by_linked_object(
			linked_doctype="User",
			linked_docname="Administrator",
			procuring_entity=self.pe.name,
		)
		self.assertTrue(any(r["name"] == self.linked_session for r in rows))

	def test_KT_GOV011_script_reports_execute(self):
		cols, data = _exec_report(_REPORT_MODULES[0], {"procuring_entity": self.pe.name})
		self.assertTrue(len(cols) >= 3)
		self.assertTrue(any(self.session in row for row in data))

		cols2, data2 = _exec_report(_REPORT_MODULES[1], {"procuring_entity": self.pe.name})
		self.assertTrue(any(self.fua.name in row for row in data2))

		cols3, data3 = _exec_report(_REPORT_MODULES[2], {"procuring_entity": self.pe.name})
		self.assertTrue(any(self.res.name in row for row in data3))

		cols4, data4 = _exec_report(
			_REPORT_MODULES[3],
			{
				"linked_doctype": "User",
				"linked_docname": "Administrator",
				"procuring_entity": self.pe.name,
			},
		)
		self.assertTrue(any(self.linked_session in row for row in data4))
