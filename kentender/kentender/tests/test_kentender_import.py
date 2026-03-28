# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import importlib
import unittest


class TestImportHooks(unittest.TestCase):
	def test_import_hooks(self):
		hooks = importlib.import_module("kentender.hooks")
		self.assertEqual(hooks.app_name, "kentender")
