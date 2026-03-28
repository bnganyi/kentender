# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import unittest


class TestImportHooks(unittest.TestCase):
	def test_import_hooks(self):
		import importlib

		hooks = importlib.import_module("kentender_stores.hooks")
		self.assertEqual(hooks.app_name, "kentender_stores")
