#!/usr/bin/env bash
# Symlink all KenTender Frappe apps from this monorepo into frappe-bench/apps/.
# Usage (from bench root):  bash apps/kentender_platform/scripts/link_apps_on_bench.sh
set -euo pipefail
BENCH_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
APPS_DIR="$BENCH_ROOT/apps"
for name in kentender kentender_strategy kentender_budget kentender_procurement \
	kentender_governance kentender_compliance kentender_stores kentender_assets \
	kentender_integrations; do
	src="kentender_platform/$name"
	if [[ ! -d "$APPS_DIR/$src" ]]; then
		echo "error: expected $APPS_DIR/$src" >&2
		exit 1
	fi
	ln -sfn "$src" "$APPS_DIR/$name"
	echo "linked apps/$name -> $src"
done
echo "Done. Run: cd $BENCH_ROOT && bench setup requirements --dev"
