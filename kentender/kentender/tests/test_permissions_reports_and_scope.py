# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PERM-015-style checks for report open helpers and scope re-exports."""

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.permissions.reports import user_can_open_script_report
from kentender.permissions.scope import merge_entity_scope_filters


class TestPermissionsReportsAndScope(FrappeTestCase):
	def test_merge_entity_scope_filters_central_unconstrained_without_active_entity(self):
		filters = merge_entity_scope_filters({"status": "Open"}, "Administrator", active_entity=None)
		self.assertEqual(filters, {"status": "Open"})

	def test_user_can_open_my_requisitions_as_administrator(self):
		if not frappe.db.exists("Report", "My Requisitions"):
			return
		self.assertTrue(user_can_open_script_report("My Requisitions", user="Administrator"))
