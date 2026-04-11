# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-015: Complaint workflow engine integration."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _make_entity, run_test_db_cleanup
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_governance.services.complaint_intake_services import review_complaint_admissibility, submit_complaint

C = "Complaint"
PREFIX = "_KT_CWF"


def _ensure_procurement_categories_for_policies() -> None:
	"""KenTender Workflow Policy.category links to Procurement Category; match complaint_type Select values."""
	for code, title in (
		("Award", "Complaint policy match — Award"),
		("Other", "Complaint policy match — Other"),
	):
		if frappe.db.exists("Procurement Category", code):
			continue
		frappe.get_doc(
			{
				"doctype": "Procurement Category",
				"category_code": code,
				"category_name": title,
				"category_type": "Not Set",
			}
		).insert(ignore_permissions=True)


def _cleanup_cwf():
	for name in frappe.get_all(
		"KenTender Approval Route Instance",
		filters={"reference_doctype": C, "reference_docname": ("like", f"{PREFIX}%")},
		pluck="name",
	):
		try:
			frappe.delete_doc("KenTender Approval Route Instance", name, force=True, ignore_permissions=True)
		except Exception:
			pass
	frappe.db.delete("KenTender Approval Action", {"reference_doctype": C, "reference_docname": ("like", f"{PREFIX}%")})
	for pol_code, tpl_code in (
		(f"{PREFIX}_POL_A", f"{PREFIX}_TPL_A"),
		(f"{PREFIX}_POL_O", f"{PREFIX}_TPL_O"),
	):
		if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
			frappe.delete_doc("KenTender Workflow Policy", pol_code, force=True, ignore_permissions=True)
		if frappe.db.exists("KenTender Approval Route Template", {"template_code": tpl_code}):
			frappe.delete_doc("KenTender Approval Route Template", tpl_code, force=True, ignore_permissions=True)
	frappe.flags.allow_complaint_status_event_delete = True
	for row in frappe.get_all("Complaint Status Event", filters={"complaint": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc("Complaint Status Event", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(C, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(C, row, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": f"{PREFIX}_PE"})
	frappe.flags.allow_complaint_status_event_delete = False


def _ensure_policies() -> None:
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": f"{PREFIX}_POL_A"}):
		return
	_ensure_procurement_categories_for_policies()
	for tpl_code, step_label, pol_code, cat in (
		(f"{PREFIX}_TPL_A", "AdmAward", f"{PREFIX}_POL_A", "Award"),
		(f"{PREFIX}_TPL_O", "AdmOther", f"{PREFIX}_POL_O", "Other"),
	):
		tpl = frappe.get_doc(
			{
				"doctype": "KenTender Approval Route Template",
				"template_code": tpl_code,
				"template_name": step_label,
				"object_type": C,
				"steps": [
					{
						"doctype": "KenTender Approval Route Template Step",
						"step_order": 1,
						"step_name": step_label,
						"actor_type": "Role",
						"role_required": "System Manager",
					}
				],
			}
		)
		tpl.insert()
		pol = frappe.get_doc(
			{
				"doctype": "KenTender Workflow Policy",
				"policy_code": pol_code,
				"applies_to_doctype": C,
				"linked_template": tpl.name,
				"category": cat,
				"active": 1,
				"evaluation_order": 10 if cat == "Award" else 20,
			}
		)
		pol.insert()


class TestComplaintWorkflowEngine(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_cwf)
		_make_entity(f"{PREFIX}_PE").insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_cwf)
		super().tearDown()

	def test_route_resolves_by_complaint_type(self):
		_ensure_policies()
		d1 = submit_complaint(
			business_id=f"{PREFIX}_B1",
			complaint_title="T1",
			complaint_type="Award",
			complainant_type="Citizen",
			complainant_name="N",
			complaint_summary="S",
			complaint_details="D",
			requested_remedy="R",
			received_by_user=frappe.session.user,
		)
		r1 = frappe.db.get_value(
			"KenTender Approval Route Instance",
			{"reference_docname": d1.name, "status": "Active"},
			"template_used",
		)
		tpl_a = frappe.db.get_value("KenTender Approval Route Template", {"template_code": f"{PREFIX}_TPL_A"}, "name")
		self.assertEqual(r1, tpl_a)

		d2 = submit_complaint(
			business_id=f"{PREFIX}_B2",
			complaint_title="T2",
			complaint_type="Other",
			complainant_type="Citizen",
			complainant_name="N",
			complaint_summary="S",
			complaint_details="D",
			requested_remedy="R",
			received_by_user=frappe.session.user,
		)
		r2 = frappe.db.get_value(
			"KenTender Approval Route Instance",
			{"reference_docname": d2.name, "status": "Active"},
			"template_used",
		)
		tpl_o = frappe.db.get_value("KenTender Approval Route Template", {"template_code": f"{PREFIX}_TPL_O"}, "name")
		self.assertEqual(r2, tpl_o)

	def test_admissibility_completes_route(self):
		_ensure_policies()
		d = submit_complaint(
			business_id=f"{PREFIX}_B3",
			complaint_title="T3",
			complaint_type="Award",
			complainant_type="Citizen",
			complainant_name="N",
			complaint_summary="S",
			complaint_details="D",
			requested_remedy="R",
			received_by_user=frappe.session.user,
		)
		review_complaint_admissibility(d.name, "Admissible", admissibility_reason="ok")
		inst = frappe.db.get_value(
			"KenTender Approval Route Instance",
			{"reference_docname": d.name},
			["status", "name"],
			as_dict=True,
		)
		self.assertEqual(inst.status, "Completed")

	def test_direct_workflow_save_blocked(self):
		_ensure_policies()
		d = submit_complaint(
			business_id=f"{PREFIX}_B4",
			complaint_title="T4",
			complaint_type="Award",
			complainant_type="Citizen",
			complainant_name="N",
			complaint_summary="S",
			complaint_details="D",
			requested_remedy="R",
			received_by_user=frappe.session.user,
		)
		doc = frappe.get_doc(C, d.name)
		with self.assertRaises(frappe.ValidationError):
			doc.workflow_state = "Panel Review"
			doc.save(ignore_permissions=True)

	def test_mutation_context_allows_save(self):
		_ensure_policies()
		d = submit_complaint(
			business_id=f"{PREFIX}_B5",
			complaint_title="T5",
			complaint_type="Award",
			complainant_type="Citizen",
			complainant_name="N",
			complaint_summary="S",
			complaint_details="D",
			requested_remedy="R",
			received_by_user=frappe.session.user,
		)
		doc = frappe.get_doc(C, d.name)
		with workflow_mutation_context():
			doc.workflow_state = "Panel Review"
			doc.save(ignore_permissions=True)
