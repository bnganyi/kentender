# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Minimal Golden template codes (Implementation Pack v2 — GOLD templates stage).

Full DocTypes for procurement / evaluation / acceptance template *versions* are not shipped yet
(see ``docs/security`` xlsx skip **Procurement Template / Version**). This module records the
canonical codes so seeds and docs stay aligned until template rows can be inserted.
"""

from __future__ import annotations

from typing import Any


DEFAULT_TEMPLATE_CODES: dict[str, str] = {
	"procurement": "ONT_STANDARD",
	"evaluation": "QCBS_SIMPLE",
	"acceptance": "GOODS_SIMPLE",
}


def ensure_minimal_golden_template_codes(ds: dict[str, Any]) -> dict[str, str]:
	"""Return merged template code map from dataset JSON (defaults from Implementation Pack).

	Reserved for future Procurement / Evaluation / Acceptance template DocTypes (see MODULE_IMPLEMENTATION_TRACKER).
	"""
	custom = (ds.get("template_codes") or {}) if isinstance(ds.get("template_codes"), dict) else {}
	out = dict(DEFAULT_TEMPLATE_CODES)
	for k, v in custom.items():
		if isinstance(v, str) and v.strip():
			out[str(k)] = v.strip()
	return out
