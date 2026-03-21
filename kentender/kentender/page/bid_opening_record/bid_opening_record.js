frappe.pages["bid-opening-record"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Bid Opening Record", "List");
	}, 0);

};
