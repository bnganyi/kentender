# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-010: requisition queue query helpers and script report wiring."""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.uat.kt_test_local_users import delete_kt_test_local_user
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender.permissions.registry import UAT_ROLE
from kentender_procurement.services.requisition_queue_queries import (
	get_my_requisitions,
	get_pending_requisition_approvals,
	get_planning_ready_requisitions,
	requisition_report_row_values,
)
from kentender_procurement.services.requisition_workflow_actions import (
	RAR_DOCTYPE,
	approve_requisition_step,
	reject_requisition,
	submit_requisition,
)

PR = "Purchase Requisition"


def _cleanup_q010_workflow():
	for dn in frappe.get_all(PR, filters={"name": ("like", "_KT_Q010_%")}, pluck="name") or []:
		for inst in frappe.get_all(
			"KenTender Approval Route Instance",
			filters={"reference_doctype": PR, "reference_docname": dn},
			pluck="name",
		):
			try:
				frappe.delete_doc("KenTender Approval Route Instance", inst, force=True, ignore_permissions=True)
			except Exception:
				pass
	code = "_KT_Q010_WF"
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": code}):
		frappe.delete_doc("KenTender Workflow Policy", code, force=True, ignore_permissions=True)
	if frappe.db.exists("KenTender Approval Route Template", {"template_code": code}):
		frappe.delete_doc("KenTender Approval Route Template", code, force=True, ignore_permissions=True)


def _ensure_q010_route_policy() -> None:
	code = "_KT_Q010_WF"
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": code}):
		return
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": code,
			"template_name": "Q010 test route",
			"object_type": PR,
			"steps": [
				{
					"doctype": "KenTender Approval Route Template Step",
					"step_order": 1,
					"step_name": "Approve",
					"actor_type": "Role",
					"role_required": "System Manager",
				}
			],
		}
	)
	tpl.insert()
	frappe.get_doc(
		{
			"doctype": "KenTender Workflow Policy",
			"policy_code": code,
			"applies_to_doctype": PR,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": 1,
		}
	).insert()


def _ensure_other_user():
	email = "_kt_q010_other@test.local"
	if frappe.db.exists("User", email):
		return email
	u = frappe.new_doc("User")
	u.email = email
	u.first_name = "KT"
	u.send_welcome_email = 0
	u.enabled = 1
	u.user_type = "System User"
	u.insert(ignore_permissions=True)
	u.add_roles("System Manager")
	return email


def _ensure_user_with_roles(email: str, *roles: str) -> str:
	if frappe.db.exists("User", email):
		u = frappe.get_doc("User", email)
	else:
		u = frappe.new_doc("User")
		u.email = email
		u.first_name = "KT"
		u.send_welcome_email = 0
		u.enabled = 1
		u.user_type = "System User"
		u.insert(ignore_permissions=True)
	have = {r.role for r in u.roles}
	for role in roles:
		if role not in have:
			u.append("roles", {"role": role})
	u.save(ignore_permissions=True)
	return email


def _grant_procuring_entity_perm(user: str, entity_name: str) -> None:
	if frappe.db.exists(
		"User Permission",
		{"user": user, "allow": "Procuring Entity", "for_value": entity_name},
	):
		return
	frappe.get_doc(
		{
			"doctype": "User Permission",
			"user": user,
			"allow": "Procuring Entity",
			"for_value": entity_name,
			"apply_to_all_doctypes": 1,
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()


def _pr_kw(entity: str, currency: str, business_id: str, **extra):
	kw = {
		"doctype": PR,
		"name": business_id,
		"title": "Queue test",
		"requisition_type": "Goods",
		"status": "Draft",
		"workflow_state": "Draft",
		"approval_status": "Draft",
		"requested_by_user": frappe.session.user,
		"procuring_entity": entity,
		"fiscal_year": "2026-2027",
		"currency": currency,
		"request_date": "2026-04-01",
		"priority_level": "Medium",
		"budget_reservation_status": "None",
		"planning_status": "Unplanned",
		"items": [
			{
				"doctype": "Purchase Requisition Item",
				"item_description": "Line",
				"quantity": 1,
				"estimated_unit_cost": 100,
			}
		],
	}
	kw.update(extra)
	return kw


def _cleanup_q010_full():
	_cleanup_q010_workflow()
	for name in frappe.get_all(PR, filters={"name": ("like", "_KT_Q010_%")}, pluck="name") or []:
		frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": name})
		frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_Q010_%")})
	for em in (
		"_kt_q010_other@test.local",
		"_kt_q010_req_only@test.local",
		"_kt_q010_hod@test.local",
	):
		delete_kt_test_local_user(em)


class TestRequisitionQueueQueries(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_q010_full)
		self.entity = _make_entity("_KT_Q010_PE").insert()
		self.entity2 = _make_entity("_KT_Q010_PE2").insert()
		_ensure_q010_route_policy()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_q010_full)
		super().tearDown()

	def _new_pr(self, suffix: str, **extra):
		doc = frappe.get_doc(_pr_kw(self.entity.name, self.currency, f"_KT_Q010_{suffix}", **extra))
		doc.insert()
		return doc

	def test_get_my_requisitions_user_and_entity(self):
		mine = self._new_pr("MY1")
		other = _ensure_other_user()
		theirs = self._new_pr("MY2", requested_by_user=other)
		other_ent = self._new_pr("MY3")
		frappe.db.set_value(PR, other_ent.name, "procuring_entity", self.entity2.name)
		frappe.db.commit()

		rows = get_my_requisitions()
		names = {r["name"] for r in rows}
		self.assertIn(mine.name, names)
		self.assertNotIn(theirs.name, names)

		rows_e = get_my_requisitions(procuring_entity=self.entity.name)
		names_e = {r["name"] for r in rows_e}
		self.assertIn(mine.name, names_e)
		self.assertNotIn(other_ent.name, names_e)

	def test_get_pending_submitted_not_approved(self):
		doc = self._new_pr("PEND1")
		submit_requisition(doc.name)
		pending = {r["name"] for r in get_pending_requisition_approvals()}
		self.assertIn(doc.name, pending)

		other = _ensure_other_user()
		doc2 = self._new_pr("PEND2", requested_by_user=other)
		submit_requisition(doc2.name, user=other)
		self.assertIn(doc2.name, {r["name"] for r in get_pending_requisition_approvals()})
		approve_requisition_step(
			doc2.name,
			workflow_step="Final",
			decision_level="L1",
			comments="ok",
		)
		pending2 = {r["name"] for r in get_pending_requisition_approvals()}
		self.assertNotIn(doc2.name, pending2)
		self.assertIn(doc.name, pending2)

	def test_get_planning_ready_filters(self):
		open_pr = self._new_pr("PLN1")
		rows = {r["name"] for r in get_planning_ready_requisitions()}
		self.assertIn(open_pr.name, rows)

		cancelled = self._new_pr("PLN2")
		frappe.db.set_value(PR, cancelled.name, "status", "Cancelled")
		frappe.db.commit()
		rows2 = {r["name"] for r in get_planning_ready_requisitions()}
		self.assertNotIn(cancelled.name, rows2)

		rej = self._new_pr("PLN3")
		submit_requisition(rej.name)
		reject_requisition(rej.name, workflow_step="HOD", decision_level="L1", comments="no")
		rows3 = {r["name"] for r in get_planning_ready_requisitions()}
		self.assertNotIn(rej.name, rows3)

	def test_requisition_report_row_values_aligns_with_columns(self):
		doc = self._new_pr("ROW1")
		doc.reload()
		vals = requisition_report_row_values(doc.as_dict())
		self.assertEqual(vals[0], doc.name)
		self.assertEqual(len(vals), 10)

	def test_script_reports_execute(self):
		self._new_pr("RPT1")
		for mod_path in (
			"kentender_procurement.kentender_procurement.report.my_requisitions.my_requisitions",
			"kentender_procurement.kentender_procurement.report.pending_requisition_approvals.pending_requisition_approvals",
			"kentender_procurement.kentender_procurement.report.planning_ready_requisitions.planning_ready_requisitions",
		):
			mod = importlib.import_module(mod_path)
			columns, data = mod.execute({})
			self.assertTrue(columns)
			self.assertIsInstance(data, list)

	def test_get_planning_ready_empty_for_requisitioner_only(self):
		req_email = "_kt_q010_req_only@test.local"
		_ensure_user_with_roles(req_email, UAT_ROLE.REQUISITIONER.value)
		self.assertEqual(get_planning_ready_requisitions(user=req_email), [])

	def test_get_pending_hod_sees_assigned_rows_only(self):
		hod_email = "_kt_q010_hod@test.local"
		_ensure_user_with_roles(hod_email, UAT_ROLE.HOD.value)
		_grant_procuring_entity_perm(hod_email, self.entity.name)

		doc = self._new_pr("HODQ1")
		submit_requisition(doc.name)
		frappe.db.set_value(PR, doc.name, "hod_user", hod_email)
		frappe.db.commit()

		other = _ensure_other_user()
		doc2 = self._new_pr("HODQ2", requested_by_user=other)
		submit_requisition(doc2.name, user=other)
		frappe.db.set_value(PR, doc2.name, "hod_user", other)
		frappe.db.commit()

		rows = {r["name"] for r in get_pending_requisition_approvals(user=hod_email)}
		self.assertIn(doc.name, rows)
		self.assertNotIn(doc2.name, rows)
