# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.workflow_guard_service import (
	EVENT_PRE_SUBMIT,
	GuardEvalOutcome,
	WORKFLOW_GUARD_RULE_DOCTYPE,
	evaluate_workflow_guards,
	get_active_workflow_guard_rules,
	workflow_guard_result_summary,
)
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup


def _cleanup_wg_data():
	frappe.db.delete(WORKFLOW_GUARD_RULE_DOCTYPE, {"rule_code": ("like", "_KT_WG_%")})
	frappe.db.delete("Exception Record", {"name": "_KT_WG_EX"})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_WG_PE"})


class TestWorkflowGuardService(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		run_test_db_cleanup(_cleanup_wg_data)
		self.entity = _make_entity("_KT_WG_PE")
		self.entity.insert()
		self.ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"name": "_KT_WG_EX",
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "Workflow guard service test justification text.",
			}
		)
		self.ex.insert()
		self._insert_rule(
			"_KT_WG_R10",
			evaluation_order=10,
			exception_policy="Block",
		)
		self._insert_rule(
			"_KT_WG_R20",
			evaluation_order=20,
			exception_policy="Warn Only",
		)

	def _insert_rule(self, code: str, **kwargs):
		data = {
			"doctype": WORKFLOW_GUARD_RULE_DOCTYPE,
			"rule_code": code,
			"rule_name": f"Rule {code}",
			"applies_to_doctype": "Exception Record",
			"event_name": EVENT_PRE_SUBMIT,
			"rule_type": "Validate",
			"severity": "Medium",
			"evaluation_order": 100,
			"exception_policy": "Block",
			"active": 1,
		}
		data.update(kwargs)
		frappe.get_doc(data).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_wg_data)
		super().tearDown()

	def test_get_active_rules_ordered(self):
		rows = get_active_workflow_guard_rules("Exception Record", EVENT_PRE_SUBMIT)
		codes = [r["rule_code"] for r in rows]
		self.assertEqual(codes, ["_KT_WG_R10", "_KT_WG_R20"])

	def test_no_evaluator_all_pass(self):
		res = evaluate_workflow_guards(
			applies_to_doctype="Exception Record",
			event_name=EVENT_PRE_SUBMIT,
			target_docname=self.ex.name,
			evaluator=None,
		)
		self.assertTrue(res.passed)
		self.assertEqual(res.blocking_issues, [])
		self.assertEqual(res.warning_issues, [])
		self.assertEqual(res.evaluated_rule_codes, ["_KT_WG_R10", "_KT_WG_R20"])

	def test_evaluator_order_and_blocking(self):
		seen: list[str] = []

		def ev(rule, _doc, _ctx):
			seen.append(rule["rule_code"])
			if rule["rule_code"] == "_KT_WG_R10":
				return GuardEvalOutcome(passed=False, message="hard stop")
			return GuardEvalOutcome(passed=True)

		res = evaluate_workflow_guards(
			applies_to_doctype="Exception Record",
			event_name=EVENT_PRE_SUBMIT,
			target_docname=self.ex.name,
			evaluator=ev,
		)
		self.assertEqual(seen, ["_KT_WG_R10", "_KT_WG_R20"])
		self.assertFalse(res.passed)
		self.assertEqual(len(res.blocking_issues), 1)
		self.assertEqual(res.blocking_issues[0].rule_code, "_KT_WG_R10")
		self.assertEqual(res.blocking_issues[0].message, "hard stop")

	def test_warn_only_non_blocking(self):
		def ev(rule, _doc, _ctx):
			if rule["rule_code"] == "_KT_WG_R20":
				return GuardEvalOutcome(passed=False, message="soft")
			return GuardEvalOutcome(passed=True)

		res = evaluate_workflow_guards(
			applies_to_doctype="Exception Record",
			event_name=EVENT_PRE_SUBMIT,
			target_docname=self.ex.name,
			evaluator=ev,
		)
		self.assertTrue(res.passed)
		self.assertEqual(len(res.warning_issues), 1)
		self.assertEqual(res.warning_issues[0].rule_code, "_KT_WG_R20")
		summary = workflow_guard_result_summary(res)
		self.assertEqual(summary["warning_count"], 1)
		self.assertEqual(summary["blocking_count"], 0)

	def test_load_document(self):
		def ev(rule, doc, _ctx):
			self.assertIsNotNone(doc)
			self.assertEqual(doc.doctype, "Exception Record")
			self.assertEqual(doc.name, self.ex.name)
			return GuardEvalOutcome(passed=True)

		evaluate_workflow_guards(
			applies_to_doctype="Exception Record",
			event_name=EVENT_PRE_SUBMIT,
			target_docname=self.ex.name,
			load_document=True,
			evaluator=ev,
		)
