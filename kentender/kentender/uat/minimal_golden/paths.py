# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

import os


def repo_root() -> str | None:
	_here = os.path.dirname(os.path.abspath(__file__))
	cur = _here
	for _ in range(8):
		candidate = os.path.join(cur, "uat", "seed_packs", "minimal_golden", "minimal_golden_canonical.json")
		if os.path.isfile(candidate):
			return cur
		parent = os.path.dirname(cur)
		if parent == cur:
			break
		cur = parent
	return None


def minimal_golden_canonical_json_path() -> str:
	bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "minimal_golden_canonical.json")
	if os.path.isfile(bundled):
		return bundled
	root = repo_root()
	if root:
		return os.path.join(root, "uat", "seed_packs", "minimal_golden", "minimal_golden_canonical.json")
	raise FileNotFoundError(
		"minimal_golden_canonical.json not found (expected under kentender.uat.minimal_golden.data or uat/seed_packs/minimal_golden/)."
	)
