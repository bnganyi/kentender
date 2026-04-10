# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-072: evaluation queue helpers and script reports."""

import importlib

from frappe.tests.utils import FrappeTestCase

from kentender_procurement.services.evaluation_queue_queries import (
	get_conflict_declarations_pending,
	get_disqualification_summary,
	get_evaluation_reports_awaiting_submission,
	get_evaluation_sessions_in_progress,
	get_my_assigned_evaluations,
	get_ranked_bid_summary,
)

_REPORT_MODULES = (
	"kentender_procurement.kentender_procurement.report.my_assigned_evaluations.my_assigned_evaluations",
	"kentender_procurement.kentender_procurement.report.conflict_declarations_pending.conflict_declarations_pending",
	"kentender_procurement.kentender_procurement.report.evaluation_sessions_in_progress.evaluation_sessions_in_progress",
	"kentender_procurement.kentender_procurement.report.evaluation_reports_awaiting_submission.evaluation_reports_awaiting_submission",
	"kentender_procurement.kentender_procurement.report.disqualification_summary.disqualification_summary",
	"kentender_procurement.kentender_procurement.report.ranked_bid_summary.ranked_bid_summary",
)


class TestEvaluationQueues072(FrappeTestCase):
	def test_each_evaluation_script_report_execute(self):
		for mod_path in _REPORT_MODULES:
			mod = importlib.import_module(mod_path)
			cols, data = mod.execute({})
			self.assertTrue(isinstance(cols, list) and len(cols) > 0, msg=mod_path)
			self.assertIsInstance(data, list, msg=mod_path)
			filters = mod.get_filters()
			self.assertIsInstance(filters, list)

	def test_queue_helpers_return_lists(self):
		for fn in (
			get_my_assigned_evaluations,
			get_conflict_declarations_pending,
			get_evaluation_sessions_in_progress,
			get_evaluation_reports_awaiting_submission,
			get_disqualification_summary,
			get_ranked_bid_summary,
		):
			self.assertIsInstance(fn(procuring_entity=None), list)
