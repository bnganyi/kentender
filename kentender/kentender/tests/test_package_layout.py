# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""STORY-CORE-003: standard packages are importable (services, api, utils)."""

import importlib
import unittest

_APP = "kentender"


class TestPackageLayout(unittest.TestCase):
	def test_standard_packages_import(self):
		importlib.import_module(f"{_APP}.services")
		importlib.import_module(f"{_APP}.api")
		importlib.import_module(f"{_APP}.permissions")
		importlib.import_module(f"{_APP}.workflow_engine")
		utils_mod = importlib.import_module(f"{_APP}.utils")
		self.assertIsNotNone(utils_mod.__doc__)
