frappe.pages["requisition-tender-handoff"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Requisition Tender Handoff", "List");
	}, 0);

};
