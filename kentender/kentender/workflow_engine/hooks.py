# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-010: ordered post-transition side-effect hooks (not Frappe hooks.py)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

HookFn = Callable[..., None]

_hooks: dict[str, list[tuple[int, str | None, HookFn]]] = defaultdict(list)


def register_side_effect_hook(
	doctype: str,
	fn: HookFn,
	*,
	order: int = 100,
	action: str | None = None,
) -> None:
	"""Register *fn* to run after a workflow transition on *doctype*.

	*fn* signature: ``(doctype, docname, action, actor, context) -> None``

	If *action* is set, the hook runs only when :func:`run_side_effects` is
	called with the same *action* string; if ``None``, the hook runs for every
	action (backward compatible).
	"""
	dt = (doctype or "").strip()
	if not dt:
		return
	af = (action or "").strip() or None
	_hooks[dt].append((order, af, fn))
	_hooks[dt].sort(key=lambda x: x[0])


def run_side_effects(
	*,
	doctype: str,
	docname: str,
	action: str,
	actor: str,
	context: dict[str, Any],
) -> None:
	act = (action or "").strip()
	for _order, act_filter, fn in _hooks.get(doctype, []):
		if act_filter is not None and act_filter != act:
			continue
		fn(doctype, docname, action, actor, context)


def clear_side_effect_hooks_for_tests() -> None:
	_hooks.clear()
