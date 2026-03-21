frappe.pages["tender-notification-log"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Tender Notification Log", "List");
	}, 0);

};
