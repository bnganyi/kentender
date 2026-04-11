# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-009: :func:`kentender.workflow_engine.policies.assert_no_blocking_sod`."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.separation_of_duty_service import RULE_DOCTYPE, ParticipationRecord
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender.tests.test_separation_of_duty_service import _make_rule
from kentender.workflow_engine.policies import assert_no_blocking_sod


def _cleanup_wfsod():
	frappe.db.delete(RULE_DOCTYPE, {"rule_code": ("like", "_KT_WFSOD_%")})
	frappe.db.delete("Exception Record", {"name": ("like", "_KT_WFSOD_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_WFSOD_PE"})


class TestAssertNoBlockingSod(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		run_test_db_cleanup(_cleanup_wfsod)
		self.entity = _make_entity("_KT_WFSOD_PE")
		self.entity.insert()
		self.ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"name": "_KT_WFSOD_EX",
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "WF-009 assert_no_blocking_sod test justification.",
			}
		)
		self.ex.insert()
		self.rule = _make_rule(
			rule_code="_KT_WFSOD_R1",
			source_doctype="Exception Record",
			source_action="submit",
			source_role="System Manager",
			target_doctype="Exception Record",
			target_action="approve",
			target_role="System Manager",
			scope_type="Same Document",
		)
		self.rule.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_wfsod)
		super().tearDown()

	def _history_submit(self):
		return [
			ParticipationRecord(
				user="Administrator",
				doctype="Exception Record",
				docname=self.ex.name,
				action="submit",
				role="System Manager",
			),
		]

	def test_raises_when_blocking_rule_matches(self):
		with self.assertRaises(frappe.ValidationError) as ctx:
			assert_no_blocking_sod(
				target_doctype="Exception Record",
				target_docname=self.ex.name,
				proposed_user="Administrator",
				proposed_action="approve",
				participation_history=self._history_submit(),
				proposed_role="System Manager",
			)
		self.assertIn("Separation of duty policy blocks", str(ctx.exception))

	def test_passes_when_no_prior_participation_conflict(self):
		assert_no_blocking_sod(
			target_doctype="Exception Record",
			target_docname=self.ex.name,
			proposed_user="Administrator",
			proposed_action="approve",
			participation_history=[],
			proposed_role="System Manager",
		)
