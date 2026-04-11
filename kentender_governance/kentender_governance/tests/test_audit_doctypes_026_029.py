# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-026–029: KenTender Audit Query / Finding / Response / Action."""

import frappe
from frappe.model.base_document import get_controller
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, today

from kentender.tests.test_procuring_entity import run_test_db_cleanup

PREFIX = "_KT_GOV026"
AQ = "KenTender Audit Query"
AF = "KenTender Audit Finding"
AR = "KenTender Audit Response"
AA = "KenTender Audit Action"


def _cleanup_audit(prefix: str):
	for dt in (AA, AR, AF, AQ):
		for name in frappe.get_all(dt, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)


def _cleanup_ops026():
	_cleanup_audit(PREFIX)


class TestAuditDoctypes026029(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_ops026)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ops026)
		super().tearDown()

	def test_KT_GOV026_029_controllers_import(self):
		get_controller(AQ)
		get_controller(AF)
		get_controller(AR)
		get_controller(AA)

	def test_KT_GOV026_audit_query_and_related_ref(self):
		q = frappe.get_doc(
			{
				"doctype": AQ,
				"business_id": f"{PREFIX}_Q1",
				"query_title": "Check contract file",
				"query_text": "<p>Please confirm version on record.</p>",
				"raised_by_user": "Administrator",
				"raised_on": today(),
				"status": "Open",
				"response_due_date": today(),
			}
		).insert(ignore_permissions=True)
		self.assertTrue(q.display_label)

	def test_KT_GOV027_finding_links_query(self):
		qn = (
			frappe.get_doc(
				{
					"doctype": AQ,
					"business_id": f"{PREFIX}_Q2",
					"query_title": "Evidence gap",
					"query_text": "<p>Need documents.</p>",
					"raised_by_user": "Administrator",
					"raised_on": today(),
					"status": "Open",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		f = frappe.get_doc(
			{
				"doctype": AF,
				"business_id": f"{PREFIX}_F1",
				"audit_query": qn,
				"finding_title": "Missing sign-off",
				"finding_detail": "<p>No approval log.</p>",
				"severity": "High",
				"status": "Issued",
				"identified_on": today(),
				"identified_by_user": "Administrator",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(f.display_label)

	def test_KT_GOV028_response_finding_consistency(self):
		qn = (
			frappe.get_doc(
				{
					"doctype": AQ,
					"business_id": f"{PREFIX}_Q3",
					"query_title": "Pricing review",
					"query_text": "<p>Explain variance.</p>",
					"raised_by_user": "Administrator",
					"raised_on": today(),
					"status": "Open",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		other_q = (
			frappe.get_doc(
				{
					"doctype": AQ,
					"business_id": f"{PREFIX}_QOTHER",
					"query_title": "Other",
					"query_text": "<p>X</p>",
					"raised_by_user": "Administrator",
					"raised_on": today(),
					"status": "Open",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		fn = (
			frappe.get_doc(
				{
					"doctype": AF,
					"business_id": f"{PREFIX}_F2",
					"audit_query": qn,
					"finding_title": "Variance",
					"finding_detail": "<p>Details</p>",
					"severity": "Medium",
					"status": "Issued",
					"identified_on": today(),
					"identified_by_user": "Administrator",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		bad_f = (
			frappe.get_doc(
				{
					"doctype": AF,
					"business_id": f"{PREFIX}_F3",
					"audit_query": other_q,
					"finding_title": "Other finding",
					"finding_detail": "<p>Y</p>",
					"severity": "Low",
					"status": "Issued",
					"identified_on": today(),
					"identified_by_user": "Administrator",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

		frappe.get_doc(
			{
				"doctype": AR,
				"business_id": f"{PREFIX}_R1",
				"audit_query": qn,
				"audit_finding": fn,
				"response_text": "<p>We uploaded the file.</p>",
				"responded_by_user": "Administrator",
				"responded_on": now_datetime(),
				"status": "Submitted",
			}
		).insert(ignore_permissions=True)

		self.assertRaises(
			frappe.ValidationError,
			lambda: frappe.get_doc(
				{
					"doctype": AR,
					"business_id": f"{PREFIX}_RBAD",
					"audit_query": qn,
					"audit_finding": bad_f,
					"response_text": "<p>No</p>",
					"responded_by_user": "Administrator",
					"responded_on": now_datetime(),
					"status": "Submitted",
				}
			).insert(ignore_permissions=True),
		)

	def test_KT_GOV029_action_chain(self):
		qn = (
			frappe.get_doc(
				{
					"doctype": AQ,
					"business_id": f"{PREFIX}_Q4",
					"query_title": "Controls",
					"query_text": "<p>Test controls.</p>",
					"raised_by_user": "Administrator",
					"raised_on": today(),
					"status": "Open",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		fn = (
			frappe.get_doc(
				{
					"doctype": AF,
					"business_id": f"{PREFIX}_F4",
					"audit_query": qn,
					"finding_title": "Segregation",
					"finding_detail": "<p>Weakness</p>",
					"severity": "Critical",
					"status": "Issued",
					"identified_on": today(),
					"identified_by_user": "Administrator",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		rn = (
			frappe.get_doc(
				{
					"doctype": AR,
					"business_id": f"{PREFIX}_R2",
					"audit_query": qn,
					"audit_finding": fn,
					"response_text": "<p>Plan attached.</p>",
					"responded_by_user": "Administrator",
					"responded_on": now_datetime(),
					"status": "Submitted",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		act = frappe.get_doc(
			{
				"doctype": AA,
				"business_id": f"{PREFIX}_A1",
				"audit_query": qn,
				"audit_finding": fn,
				"audit_response": rn,
				"action_title": "Implement dual sign-off",
				"assigned_to_user": "Administrator",
				"due_date": today(),
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(act.display_label)
