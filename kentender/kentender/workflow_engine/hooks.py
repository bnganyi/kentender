# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-010: ordered post-transition side-effect hooks (not Frappe hooks.py)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

HookFn = Callable[..., None]

_hooks: dict[str, list[tuple[int, HookFn]]] = defaultdict(list)


def register_side_effect_hook(
	doctype: str,
	fn: HookFn,
	*,
	order: int = 100,
) -> None:
	"""Register *fn* to run after a workflow transition on *doctype*.

	*fn* signature: ``(doctype, docname, action, actor, context) -> None``
	"""
	dt = (doctype or "").strip()
	if not dt:
		return
	_hooks[dt].append((order, fn))
	_hooks[dt].sort(key=lambda x: x[0])


def run_side_effects(
	*,
	doctype: str,
	docname: str,
	action: str,
	actor: str,
	context: dict[str, Any],
) -> None:
	for _order, fn in _hooks.get(doctype, []):
		fn(doctype, docname, action, actor, context)


def clear_side_effect_hooks_for_tests() -> None:
	_hooks.clear()
