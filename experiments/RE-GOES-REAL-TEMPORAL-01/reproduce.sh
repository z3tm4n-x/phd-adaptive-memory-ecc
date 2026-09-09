#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TMP="${TMPDIR:-/tmp}/re-goes-real-temporal-01-reproduce"
RATE="${RATE_CSV_OVERRIDE:-$ROOT/experiments/RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv}"
FALLBACK="${FALLBACK_OVERRIDE:-$ROOT/experiments/RE-GOES-CAUSAL-INPUT-CONTRACT-01/fallback_rows.csv.gz}"
rm -rf "$TMP"; mkdir -p "$TMP"
python "$HERE/real_temporal.py" --config "$HERE/config.json" --output-dir "$TMP" --rate-csv "$RATE" --fallback "$FALLBACK"
python "$HERE/resource_map.py" --config "$HERE/config.json" --dir "$TMP"
python "$HERE/summarize_results.py" --dir "$TMP"
cp "$HERE/selected_windows.csv" "$TMP/selected_windows.csv"
python "$HERE/test_real_temporal.py" --config "$HERE/config.json" --dir "$TMP" --rate-csv "$RATE" --fallback "$FALLBACK" > "$TMP/test_output.txt"
cat "$TMP/test_output.txt"
python - "$TMP/applicability_resource_summary.csv" "$TMP/applicability_resource_summary.csv.gz.b64" <<'PY1'
import base64,gzip,sys
from pathlib import Path
raw=Path(sys.argv[1]).read_bytes()
Path(sys.argv[2]).write_bytes(base64.b64encode(gzip.compress(raw,mtime=0))+b"\n")
PY1
for f in baseline_actions.csv selection_recomputed.csv model_compatibility.csv applicability_resource_summary.csv.gz.b64 g1_endpoint_summary.csv test_output.txt; do
  cmp "$TMP/$f" "$HERE/$f"
done
python - "$TMP" "$HERE/run_manifest.json" <<'PY2'
import hashlib,json,sys
from pathlib import Path
d=Path(sys.argv[1]); m=json.loads(Path(sys.argv[2]).read_text())
for name,want in {**m["transient_intermediate_sha256"], **m["transient_full_maps_sha256"]}.items():
    got=hashlib.sha256((d/name).read_bytes()).hexdigest()
    if got!=want: raise SystemExit(f"full-map hash mismatch {name}: {got} != {want}")
print("PASS transient full-map hashes")
PY2
printf 'PASS compact release byte comparison\n'
