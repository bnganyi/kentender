// Drop Frappe's localStorage cache for Page docs when KenTender redirect stubs change.
// Stale entries can omit `script`, so on_page_load never runs → blank desk main area.
$(document).on("startup", function () {
	var v = frappe.boot && frappe.boot.kentender_page_stub_version;
	if (v == null) {
		return;
	}
	var marker = "kentender_page_stub_ls_v";
	var prev = localStorage.getItem(marker);
	if (prev === String(v)) {
		return;
	}
	Object.keys(localStorage).forEach(function (key) {
		if (key.indexOf("_page:") === 0) {
			localStorage.removeItem(key);
		}
	});
	localStorage.setItem(marker, String(v));
});
