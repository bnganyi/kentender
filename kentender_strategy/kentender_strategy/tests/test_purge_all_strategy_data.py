# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.services.purge_all_strategy_data import purge_all_strategy_data


class TestPurgeAllStrategyData(FrappeTestCase):
	def test_purge_removes_national_framework(self):
		bid = "_KT_PURGE_NF_001"
		frappe.get_doc(
			{
				"doctype": "National Framework",
				"name": bid,
				"framework_code": "PURGE-NF",
				"framework_name": "Purge test NF",
				"framework_type": "National Development Plan",
				"version_label": "v1",
				"status": "Draft",
				"is_locked_reference": 0,
				"start_date": "2026-01-01",
				"end_date": "2026-12-31",
			}
		).insert(ignore_permissions=True)

		purge_all_strategy_data(commit=False)

		self.assertFalse(frappe.db.exists("National Framework", bid))
