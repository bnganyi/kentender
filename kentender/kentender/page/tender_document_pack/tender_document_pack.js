frappe.pages["tender-document-pack"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Tender Document Pack", "List");
	}, 0);

};
