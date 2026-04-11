# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe.tests.utils import FrappeTestCase

from kentender.uat.wipe_test_data import (
	LEGACY_SEED_USER_EMAILS,
	collect_uat_seed_user_emails,
)


class TestUatWipeTestData(FrappeTestCase):
	def test_collect_uat_seed_user_emails_matches_minimal_golden_only(self):
		emails = set(collect_uat_seed_user_emails())
		self.assertIn("requisitioner.test@ken-tender.test", emails)
		self.assertIn("strategyadmin.test@ken-tender.test", emails)
		self.assertIn("hod.test@ken-tender.test", emails)
		self.assertIn("supplier1.test@ken-tender.test", emails)
		self.assertIn("supplier2.test@ken-tender.test", emails)
		self.assertNotIn("strategy.uat@ken-tender.test", emails)

	def test_legacy_seed_list_covers_old_bootstraps_not_golden(self):
		legacy = set(LEGACY_SEED_USER_EMAILS)
		self.assertIn("strategy.uat@ken-tender.test", legacy)
		self.assertIn("requisitioner.uat-mvp@ken-tender.test", legacy)
		for e in collect_uat_seed_user_emails():
			self.assertNotIn(e, legacy, "golden emails must not be in LEGACY_SEED_USER_EMAILS")
