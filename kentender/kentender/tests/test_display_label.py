# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe.tests.utils import FrappeTestCase

from kentender.utils.display_label import code_title_label


class TestDisplayLabel(FrappeTestCase):
	def test_code_title_label(self):
		self.assertEqual(code_title_label("SOC", "Social Development"), "SOC — Social Development")
		self.assertEqual(code_title_label("", "Title"), "Title")
		self.assertEqual(code_title_label("C", ""), "C")
		self.assertEqual(code_title_label(None, None), "")
