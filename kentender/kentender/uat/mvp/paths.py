# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

import os


def repo_root() -> str | None:
	"""Platform repo root (contains top-level ``uat/seed_packs``), if present."""
	_here = os.path.dirname(os.path.abspath(__file__))
	cur = _here
	for _ in range(8):
		candidate = os.path.join(cur, "uat", "seed_packs", "mvp_canonical.json")
		if os.path.isfile(candidate):
			return cur
		parent = os.path.dirname(cur)
		if parent == cur:
			break
		cur = parent
	return None


def mvp_canonical_json_path() -> str:
	"""Bundled copy in the app package, or repo ``uat/seed_packs`` when developing from source."""
	bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mvp_canonical.json")
	if os.path.isfile(bundled):
		return bundled
	root = repo_root()
	if root:
		return os.path.join(root, "uat", "seed_packs", "mvp_canonical.json")
	raise FileNotFoundError(
		"mvp_canonical.json not found (expected under kentender.uat.mvp.data or uat/seed_packs/)."
	)
