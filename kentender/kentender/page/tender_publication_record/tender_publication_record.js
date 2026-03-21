frappe.pages["tender-publication-record"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Tender Publication Record", "List");
	}, 0);

};
