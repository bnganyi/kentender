# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

import json
from typing import Any

from kentender.uat.minimal_golden.paths import minimal_golden_canonical_json_path


def load_minimal_golden_dataset() -> dict[str, Any]:
	path = minimal_golden_canonical_json_path()
	with open(path, encoding="utf-8") as f:
		return json.load(f)


def minimal_golden_password(ds: dict[str, Any]) -> str:
	import os

	env_key = (ds.get("users") or {}).get("password_env") or ""
	if env_key:
		v = os.environ.get(env_key)
		if v:
			return v
	return (ds.get("users") or {}).get("default_password") or "k3nTender!golden"
