frappe.pages["tender-lot"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Tender Lot", "List");
	}, 0);

};
