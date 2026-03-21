frappe.pages["tender-document-version"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Tender Document Version", "List");
	}, 0);

};
