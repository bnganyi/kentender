# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMasterDataCore006(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete("Document Type Registry", {"document_type_code": ("like", "_KT_M6_%")})
		frappe.db.delete("Reference Number Policy", {"policy_code": ("like", "_KT_M6_%")})
		frappe.db.delete("Procurement Method", {"method_code": ("like", "_KT_M6_%")})
		frappe.db.delete("Procurement Category", {"category_code": ("like", "_KT_M6_%")})
		frappe.db.delete("Funding Source", {"funding_source_code": ("like", "_KT_M6_%")})
		frappe.db.commit()
		super().tearDown()

	def test_funding_source_valid_and_duplicate_blocked(self):
		a = frappe.get_doc(
			{
				"doctype": "Funding Source",
				"funding_source_code": "_KT_M6_FS1",
				"funding_source_name": "Test Fund",
				"funding_source_type": "Grant",
			}
		)
		a.insert()
		self.assertEqual(a.name, "_KT_M6_FS1")
		dup = frappe.get_doc(
			{
				"doctype": "Funding Source",
				"funding_source_code": "_KT_M6_FS1",
				"funding_source_name": "Other",
				"funding_source_type": "Loan",
			}
		)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_procurement_category_valid_duplicate_hierarchy(self):
		root = frappe.get_doc(
			{
				"doctype": "Procurement Category",
				"category_code": "_KT_M6_CAT_ROOT",
				"category_name": "Root",
				"category_type": "Goods",
			}
		)
		root.insert()
		child = frappe.get_doc(
			{
				"doctype": "Procurement Category",
				"category_code": "_KT_M6_CAT_CHILD",
				"category_name": "Child",
				"category_type": "Goods",
				"parent_category": root.name,
			}
		)
		child.insert()
		dup = frappe.get_doc(
			{
				"doctype": "Procurement Category",
				"category_code": "_KT_M6_CAT_CHILD",
				"category_name": "Dup",
				"category_type": "Works",
			}
		)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

		leaf = frappe.get_doc(
			{
				"doctype": "Procurement Category",
				"category_code": "_KT_M6_CAT_LEAF",
				"category_name": "Leaf",
				"category_type": "Services",
				"parent_category": child.name,
			}
		)
		leaf.insert()
		leaf.parent_category = leaf.name
		self.assertRaises(frappe.ValidationError, leaf.save)

	def test_procurement_category_circular_hierarchy_blocked(self):
		a = frappe.get_doc(
			{
				"doctype": "Procurement Category",
				"category_code": "_KT_M6_CA",
				"category_name": "A",
				"category_type": "Goods",
			}
		)
		a.insert()
		b = frappe.get_doc(
			{
				"doctype": "Procurement Category",
				"category_code": "_KT_M6_CB",
				"category_name": "B",
				"category_type": "Goods",
				"parent_category": a.name,
			}
		)
		b.insert()
		a.parent_category = b.name
		self.assertRaises(frappe.ValidationError, a.save)

	def test_procurement_method_valid_and_duplicate_blocked(self):
		m = frappe.get_doc(
			{
				"doctype": "Procurement Method",
				"method_code": "_KT_M6_M1",
				"method_name": "Open Tender",
			}
		)
		m.insert()
		dup = frappe.get_doc(
			{
				"doctype": "Procurement Method",
				"method_code": "_KT_M6_M1",
				"method_name": "Other",
			}
		)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_reference_number_policy_valid_and_duplicate_blocked(self):
		p = frappe.get_doc(
			{
				"doctype": "Reference Number Policy",
				"policy_code": "_KT_M6_P1",
				"target_doctype": "Purchase Order",
				"pattern": "PO-.#####",
			}
		)
		p.insert()
		dup = frappe.get_doc(
			{
				"doctype": "Reference Number Policy",
				"policy_code": "_KT_M6_P1",
				"target_doctype": "Sales Invoice",
				"pattern": "SI-.#####",
			}
		)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_document_type_registry_valid_and_duplicate_blocked(self):
		d = frappe.get_doc(
			{
				"doctype": "Document Type Registry",
				"document_type_code": "_KT_M6_D1",
				"document_type_name": "Bid Submission",
			}
		)
		d.insert()
		dup = frappe.get_doc(
			{
				"doctype": "Document Type Registry",
				"document_type_code": "_KT_M6_D1",
				"document_type_name": "Other",
			}
		)
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)
