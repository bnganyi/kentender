# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

import json
from typing import Any

from kentender.uat.mvp.paths import mvp_canonical_json_path


def load_mvp_dataset() -> dict[str, Any]:
	path = mvp_canonical_json_path()
	with open(path, encoding="utf-8") as f:
		return json.load(f)


def mvp_password(ds: dict[str, Any]) -> str:
	import os

	env_key = (ds.get("users") or {}).get("password_env") or ""
	if env_key:
		v = os.environ.get(env_key)
		if v:
			return v
	return (ds.get("users") or {}).get("default_password") or "k3nTender!golden"
