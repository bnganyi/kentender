# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import importlib
import json
import unittest

from kentender.uat.minimal_golden.dataset import load_minimal_golden_dataset
from kentender.uat.minimal_golden.paths import minimal_golden_canonical_json_path


class TestMinimalGoldenPackage(unittest.TestCase):
	def test_import_commands(self):
		importlib.import_module("kentender.uat.minimal_golden.commands")

	def test_canonical_json_loads(self):
		ds = load_minimal_golden_dataset()
		self.assertEqual(ds.get("entity", {}).get("entity_code"), "MOH")
		self.assertIn("strategy", ds)
		path = minimal_golden_canonical_json_path()
		with open(path, encoding="utf-8") as f:
			json.load(f)
