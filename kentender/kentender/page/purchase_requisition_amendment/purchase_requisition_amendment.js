frappe.pages["purchase-requisition-amendment"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Purchase Requisition Amendment", "List");
	}, 0);

};
