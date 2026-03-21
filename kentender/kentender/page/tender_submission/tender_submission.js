frappe.pages["tender-submission"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Tender Submission", "List");
	}, 0);

};
