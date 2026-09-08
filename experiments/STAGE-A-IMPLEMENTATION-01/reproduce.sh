#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
TASK="$ROOT/experiments/STAGE-A-IMPLEMENTATION-01"
CSV="${TMPDIR:-/tmp}/stage_a_proton_rate_5min.csv"
OUT="${TMPDIR:-/tmp}/stage-a-repro"
git show 619cb3538e296b3619f21301a176665f4611143f:experiments/RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv > "$CSV"
python3 "$TASK/test_stage_a.py"
rm -rf "$OUT"
python3 "$TASK/stage_a.py" --config "$TASK/config.json" --output-dir "$OUT" --frozen-csv "$CSV"
for f in direct_budget_audit.csv resource_table.csv selected_policies.csv.gz.b64 passing_sets.csv passing_sets.json.gz.b64 resource_gaps.csv selected_policy_trees.json numerical_boundary_summary.csv; do
  cmp "$TASK/$f" "$OUT/$f"
done
echo "PASS: tests, frozen-input gate, deterministic science tables"
