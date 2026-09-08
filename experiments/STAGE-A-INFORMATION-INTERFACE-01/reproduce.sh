#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STAGE_A_DIR="${STAGE_A_DIR:-$HERE/../STAGE-A-IMPLEMENTATION-01}"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/stage-a-information-interface.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

python3 "$HERE/information_interface.py" \
  --config "$HERE/config.json" \
  --stage-a-dir "$STAGE_A_DIR" \
  --output-dir "$TMP"

for f in \
  information_regions.csv \
  information_boundaries.json \
  policy_region_map.csv.gz.b64 \
  resource_summary.csv.gz.b64 \
  retention_breakpoints.csv \
  summary.json
do
  cmp "$HERE/$f" "$TMP/$f"
done

STAGE_A_DIR="$STAGE_A_DIR" python3 -m unittest -v "$HERE/test_information_interface.py"
python3 -m py_compile "$HERE/information_interface.py" "$HERE/test_information_interface.py"

echo "PASS: regenerated maps match committed outputs; focused tests and syntax checks passed"
