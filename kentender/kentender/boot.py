"""Desk boot extensions for KenTender."""


def extend_boot_session(bootinfo):
	"""Expose a version token so the desk can drop stale Page localStorage (see pageview.js)."""
	# Bump when list-redirect Page stubs (JS/HTML) change — avoids blank desk pages from cached Page docs without script.
	bootinfo.kentender_page_stub_version = 2
