frappe.pages["supplier-compliance-document"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Supplier Compliance Document", "List");
	}, 0);

};
