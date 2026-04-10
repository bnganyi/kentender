# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Site preparation: remove UAT-MVP seed data so Minimal Golden can load without duplicate/conflicting test rows."""

from __future__ import annotations

from kentender.uat.mvp.dataset import load_mvp_dataset
from kentender.uat.mvp.reset import reset_mvp_seed_data


def cleanup_mvp_uat_data() -> None:
	"""Delete MVP canonical rows (UAT-MVP* PRs, budget, strategy chain, masters).

	Scoped to identifiers in ``mvp_canonical.json`` — not a global truncate of strategy tables.
	"""
	reset_mvp_seed_data(load_mvp_dataset())
