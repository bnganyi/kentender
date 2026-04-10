# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.separation_of_duty_service import (
	RULE_DOCTYPE,
	ParticipationRecord,
	evaluate_sod_conflicts,
	has_blocking_sod_violation,
	sod_evaluation_summary,
)
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup


def _make_rule(**kwargs):
	data = {
		"doctype": RULE_DOCTYPE,
		"rule_code": "_KT_SOD_R1",
		"source_doctype": "Exception Record",
		"source_action": "submit",
		"source_role": "System Manager",
		"target_doctype": "Exception Record",
		"target_action": "approve",
		"target_role": "System Manager",
		"scope_type": "Same Document",
		"severity": "High",
		"exception_policy": "Block",
		"active": 1,
	}
	data.update(kwargs)
	return frappe.get_doc(data)


def _cleanup_sod_rules_only():
	frappe.db.delete(RULE_DOCTYPE, {"rule_code": ("like", "_KT_SOD_%")})


def _cleanup_sod_eval_data():
	frappe.db.delete(RULE_DOCTYPE, {"rule_code": ("like", "_KT_SOD_%")})
	frappe.db.delete("Exception Record", {"name": ("like", "_KT_SOD_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_SOD_PE"})


class TestSeparationOfDutyConflictRuleDocType(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_sod_rules_only)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_sod_rules_only)
		super().tearDown()

	def test_duplicate_rule_code_blocked(self):
		_make_rule(rule_code="_KT_SOD_DUP").insert()
		dup = _make_rule(rule_code="_KT_SOD_DUP")
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)


class TestSeparationOfDutyEvaluation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		run_test_db_cleanup(_cleanup_sod_eval_data)
		self.entity = _make_entity("_KT_SOD_PE")
		self.entity.insert()
		self.ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"name": "_KT_SOD_EX",
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "Separation of duty evaluation test justification.",
			}
		)
		self.ex.insert()
		self.rule = _make_rule(rule_code="_KT_SOD_R1")
		self.rule.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_sod_eval_data)
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

	def test_conflict_same_document(self):
		v = evaluate_sod_conflicts(
			target_doctype="Exception Record",
			target_docname=self.ex.name,
			proposed_user="Administrator",
			proposed_action="approve",
			proposed_role="System Manager",
			participation_history=self._history_submit(),
		)
		self.assertEqual(len(v), 1)
		self.assertEqual(v[0].rule_code, "_KT_SOD_R1")
		self.assertEqual(v[0].exception_policy, "Block")
		self.assertTrue(has_blocking_sod_violation(
			target_doctype="Exception Record",
			target_docname=self.ex.name,
			proposed_user="Administrator",
			proposed_action="approve",
			proposed_role="System Manager",
			participation_history=self._history_submit(),
		))

	def test_no_conflict_different_document(self):
		other = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"name": "_KT_SOD_EX2",
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "Second exception for SoD scope test justification.",
			}
		)
		other.insert()
		try:
			v = evaluate_sod_conflicts(
				target_doctype="Exception Record",
				target_docname=other.name,
				proposed_user="Administrator",
				proposed_action="approve",
				proposed_role="System Manager",
				participation_history=self._history_submit(),
			)
			self.assertEqual(v, [])
		finally:
			frappe.delete_doc("Exception Record", other.name, force=1, ignore_permissions=1)

	def test_inactive_rule_ignored(self):
		self.rule.db_set("active", 0)
		frappe.db.commit()
		v = evaluate_sod_conflicts(
			target_doctype="Exception Record",
			target_docname=self.ex.name,
			proposed_user="Administrator",
			proposed_action="approve",
			proposed_role="System Manager",
			participation_history=self._history_submit(),
		)
		self.assertEqual(v, [])

	def test_same_scope_key_matches_across_docnames(self):
		self.rule.db_set("scope_type", "Same Scope Key")
		self.rule.db_set("active", 1)
		frappe.db.commit()
		other = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"name": "_KT_SOD_EX3",
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "Third exception for SoD scope key test justification.",
			}
		)
		other.insert()
		try:
			hist = [
				ParticipationRecord(
					user="Administrator",
					doctype="Exception Record",
					docname=self.ex.name,
					action="submit",
					role="System Manager",
					scope_key="TENDER-001",
				),
			]
			v = evaluate_sod_conflicts(
				target_doctype="Exception Record",
				target_docname=other.name,
				proposed_user="Administrator",
				proposed_action="approve",
				proposed_role="System Manager",
				participation_history=hist,
				scope_key="TENDER-001",
			)
			self.assertEqual(len(v), 1)
		finally:
			frappe.delete_doc("Exception Record", other.name, force=1, ignore_permissions=1)

	def test_global_scope_any_document(self):
		self.rule.db_set("scope_type", "Global")
		self.rule.db_set("active", 1)
		frappe.db.commit()
		other = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"name": "_KT_SOD_EX4",
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "Fourth exception for SoD global scope test justification.",
			}
		)
		other.insert()
		try:
			v = evaluate_sod_conflicts(
				target_doctype="Exception Record",
				target_docname=other.name,
				proposed_user="Administrator",
				proposed_action="approve",
				proposed_role="System Manager",
				participation_history=self._history_submit(),
			)
			self.assertEqual(len(v), 1)
		finally:
			frappe.delete_doc("Exception Record", other.name, force=1, ignore_permissions=1)

	def test_warn_only_not_blocking(self):
		self.rule.db_set("exception_policy", "Warn Only")
		self.rule.db_set("active", 1)
		frappe.db.commit()
		v = evaluate_sod_conflicts(
			target_doctype="Exception Record",
			target_docname=self.ex.name,
			proposed_user="Administrator",
			proposed_action="approve",
			proposed_role="System Manager",
			participation_history=self._history_submit(),
		)
		self.assertEqual(len(v), 1)
		self.assertFalse(
			has_blocking_sod_violation(
				target_doctype="Exception Record",
				target_docname=self.ex.name,
				proposed_user="Administrator",
				proposed_action="approve",
				proposed_role="System Manager",
				participation_history=self._history_submit(),
			),
		)
		summary = sod_evaluation_summary(v)
		self.assertEqual(summary["count"], 1)
		self.assertEqual(summary["blocking"], 0)
		self.assertEqual(summary["warn_only"], 1)
