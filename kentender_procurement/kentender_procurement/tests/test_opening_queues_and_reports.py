# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-056: opening queue script reports."""

import importlib

from frappe.tests.utils import FrappeTestCase

from kentender_procurement.services.opening_queue_queries import (
	get_completed_opening_sessions,
	get_opening_exclusion_rows,
	get_opening_registers,
	get_ready_for_opening_sessions,
	get_scheduled_opening_sessions,
)

_REPORT_MODULES = (
	"kentender_procurement.kentender_procurement.report.scheduled_opening_sessions.scheduled_opening_sessions",
	"kentender_procurement.kentender_procurement.report.ready_for_opening_sessions.ready_for_opening_sessions",
	"kentender_procurement.kentender_procurement.report.completed_opening_sessions.completed_opening_sessions",
	"kentender_procurement.kentender_procurement.report.opening_registers.opening_registers",
	"kentender_procurement.kentender_procurement.report.opening_exclusions.opening_exclusions",
)


class TestOpeningQueues056(FrappeTestCase):
	def test_each_opening_script_report_execute(self):
		for mod_path in _REPORT_MODULES:
			mod = importlib.import_module(mod_path)
			cols, data = mod.execute({})
			self.assertTrue(isinstance(cols, list) and len(cols) > 0, msg=mod_path)
			self.assertIsInstance(data, list, msg=mod_path)
			filters = mod.get_filters()
			self.assertIsInstance(filters, list)

	def test_queue_helpers_callable(self):
		for fn in (
			get_scheduled_opening_sessions,
			get_ready_for_opening_sessions,
			get_completed_opening_sessions,
			get_opening_registers,
			get_opening_exclusion_rows,
		):
			self.assertIsInstance(fn(procuring_entity=None), list)
