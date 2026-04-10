# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Human-readable labels for link fields (code + title pattern)."""


def code_title_label(code: str | None, title: str | None) -> str:
	"""Return ``code — title`` when both parts exist; otherwise the non-empty part."""
	c = (code or "").strip()
	t = (title or "").strip()
	if c and t:
		return f"{c} — {t}"
	return t or c
