# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE
from kentender.services.controlled_action_service import (
	ACTION_SUBMIT,
	AUDIT_COMPLETED,
	AUDIT_GATE_PASSED,
	AUDIT_GUARD_BLOCKED,
	AUDIT_PERMISSION_DENIED,
	SOURCE_MODULE,
	log_controlled_action_completed,
	run_controlled_action_gate,
)
from kentender.services.workflow_guard_service import (
	EVENT_PRE_SUBMIT,
	GuardEvalOutcome,
	WORKFLOW_GUARD_RULE_DOCTYPE,
)
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity


class TestControlledActionService(FrappeTestCase):
	def setUp(self):
		super().setUp()
		_ensure_test_currency()
		self.entity = _make_entity("_KT_CA_PE")
		self.entity.insert()
		self.ex = frappe.get_doc(
			{
				"doctype": "Exception Record",
				"business_id": "_KT_CA_EX",
				"exception_type": "Other",
				"procuring_entity": self.entity.name,
				"triggered_by": "Administrator",
				"justification": "Controlled action service test.",
			}
		)
		self.ex.insert()
		frappe.get_doc(
			{
				"doctype": WORKFLOW_GUARD_RULE_DOCTYPE,
				"rule_code": "_KT_CA_R1",
				"rule_name": "CA test rule",
				"applies_to_doctype": "Exception Record",
				"event_name": EVENT_PRE_SUBMIT,
				"rule_type": "Validate",
				"severity": "Medium",
				"evaluation_order": 10,
				"exception_policy": "Block",
				"active": 1,
			}
		).insert()

	def tearDown(self):
		frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"target_docname": self.ex.name})
		frappe.db.delete(WORKFLOW_GUARD_RULE_DOCTYPE, {"rule_code": "_KT_CA_R1"})
		frappe.db.delete("Exception Record", {"business_id": "_KT_CA_EX"})
		frappe.db.delete("Procuring Entity", {"entity_code": "_KT_CA_PE"})
		frappe.db.commit()
		frappe.set_user("Administrator")
		super().tearDown()

	def _audit_rows(self):
		return frappe.get_all(
			AUDIT_EVENT_DOCTYPE,
			filters={"target_doctype": "Exception Record", "target_docname": self.ex.name},
			fields=["event_type", "source_module"],
			order_by="creation asc",
		)

	def test_admin_submit_gate_passes_and_audits(self):
		res = run_controlled_action_gate(
			doctype="Exception Record",
			docname=self.ex.name,
			action=ACTION_SUBMIT,
			user="Administrator",
			procuring_entity=self.entity.name,
		)
		self.assertTrue(res.ok)
		self.assertTrue(res.permission_ok)
		self.assertIsNotNone(res.guard_result)
		self.assertTrue(res.guard_result.passed)
		rows = self._audit_rows()
		types = [r.event_type for r in rows]
		self.assertIn(AUDIT_GATE_PASSED, types)
		self.assertTrue(any(r.source_module == SOURCE_MODULE for r in rows))

	def test_guest_read_denied(self):
		res = run_controlled_action_gate(
			doctype="Exception Record",
			docname=self.ex.name,
			action=ACTION_SUBMIT,
			user="Guest",
			procuring_entity=self.entity.name,
		)
		self.assertFalse(res.ok)
		self.assertFalse(res.permission_ok)
		self.assertIsNone(res.guard_result)
		rows = self._audit_rows()
		types = [r.event_type for r in rows]
		self.assertIn(AUDIT_PERMISSION_DENIED, types)
		self.assertIn("kt.security.access_denied", types)

	def test_workflow_guard_blocks(self):
		def ev(rule, _doc, _ctx):
			return GuardEvalOutcome(passed=False, message="blocked by test")

		res = run_controlled_action_gate(
			doctype="Exception Record",
			docname=self.ex.name,
			action=ACTION_SUBMIT,
			user="Administrator",
			guard_evaluator=ev,
			procuring_entity=self.entity.name,
		)
		self.assertFalse(res.ok)
		self.assertTrue(res.permission_ok)
		self.assertIsNotNone(res.guard_result)
		self.assertFalse(res.guard_result.passed)
		rows = self._audit_rows()
		types = [r.event_type for r in rows]
		self.assertIn(AUDIT_GUARD_BLOCKED, types)

	def test_skip_guards_no_workflow_event(self):
		res = run_controlled_action_gate(
			doctype="Exception Record",
			docname=self.ex.name,
			action=ACTION_SUBMIT,
			user="Administrator",
			run_workflow_guards=False,
			procuring_entity=self.entity.name,
		)
		self.assertTrue(res.ok)
		self.assertIsNone(res.guard_result)

	def test_log_completed(self):
		doc = log_controlled_action_completed(
			action=ACTION_SUBMIT,
			doctype="Exception Record",
			docname=self.ex.name,
			actor="Administrator",
			procuring_entity=self.entity.name,
			extra={"foo": "bar"},
		)
		self.assertTrue(doc.name)
		self.assertEqual(doc.event_type, AUDIT_COMPLETED)
