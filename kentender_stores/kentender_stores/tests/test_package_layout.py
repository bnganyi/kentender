# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""STORY-CORE-003: standard packages are importable (services, api, utils)."""

import importlib
import unittest

_APP = "kentender_stores"


class TestPackageLayout(unittest.TestCase):
	def test_standard_packages_import(self):
		importlib.import_module(f"{_APP}.services")
		importlib.import_module(f"{_APP}.api")
		utils_mod = importlib.import_module(f"{_APP}.utils")
		self.assertIsNotNone(utils_mod.__doc__)
