# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe.tests.utils import FrappeTestCase

from kentender.uat.minimal_golden.dataset import load_minimal_golden_dataset
from kentender.uat.minimal_golden.templates import DEFAULT_TEMPLATE_CODES, ensure_minimal_golden_template_codes
from kentender.uat.minimal_golden.verify import verify_minimal_golden, verify_strategy_chain_integrity


class TestMinimalGoldenVerifyStrategy(FrappeTestCase):
	def test_template_codes_defaults(self):
		ds = load_minimal_golden_dataset()
		out = ensure_minimal_golden_template_codes(ds)
		self.assertEqual(out["procurement"], DEFAULT_TEMPLATE_CODES["procurement"])
		self.assertIn("QCBS_SIMPLE", out["evaluation"])

	def test_verify_strategy_chain_runs(self):
		ds = load_minimal_golden_dataset()
		checks = verify_strategy_chain_integrity(ds)
		self.assertTrue(any(c.get("check") == "strategy_national_framework_exists" for c in checks))

	def test_verify_minimal_golden_structure(self):
		ds = load_minimal_golden_dataset()
		result = verify_minimal_golden(ds)
		self.assertIn("checks", result)
		self.assertIsInstance(result["checks"], list)
