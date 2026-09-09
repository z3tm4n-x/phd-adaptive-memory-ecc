#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/re-goes-real-temporal-repair.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
RATE="${RATE_CSV_OVERRIDE:-$ROOT/experiments/RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv}"
FALLBACK="${FALLBACK_OVERRIDE:-$ROOT/experiments/RE-GOES-CAUSAL-INPUT-CONTRACT-01/fallback_rows.csv.gz}"

python "$HERE/numerical_repair.py" --config "$HERE/config.json" --output-dir "$TMP" --rate-csv "$RATE" --fallback "$FALLBACK"
python "$HERE/resource_map.py" --config "$HERE/config.json" --dir "$TMP"
python "$HERE/summarize_results.py" --dir "$TMP"
python "$HERE/test_numerical_repair.py" --config "$HERE/config.json" --dir "$TMP" --rate-csv "$RATE" --fallback "$FALLBACK" > "$TMP/test_output.txt"
cat "$TMP/test_output.txt"

# Scientific CSV equality.  The container representation itself is deliberately not a gate.
cat "$HERE"/applicability_resource_summary.csv.gz.b64.part* > "$TMP/applicability_resource_summary.csv.gz.b64"
python - "$TMP/applicability_resource_summary.csv.gz.b64" "$TMP/applicability_resource_summary.expected.csv" <<'PY1'
import base64,gzip,sys
from pathlib import Path
src=Path(sys.argv[1]).read_bytes()
Path(sys.argv[2]).write_bytes(gzip.decompress(base64.b64decode(src)))
PY1
cmp "$TMP/applicability_resource_summary.csv" "$TMP/applicability_resource_summary.expected.csv"
python - "$HERE/model_compatibility.csv.gz.b64" "$TMP/model_compatibility.expected.csv" <<'PYM'
import base64,gzip,sys
from pathlib import Path
Path(sys.argv[2]).write_bytes(gzip.decompress(base64.b64decode(Path(sys.argv[1]).read_bytes())))
PYM
cmp "$TMP/model_compatibility.csv" "$TMP/model_compatibility.expected.csv"
cmp "$TMP/g1_endpoint_summary.csv" "$HERE/g1_endpoint_summary.csv"
cmp "$TMP/repair_regression_witnesses.csv" "$HERE/repair_regression_witnesses.csv"
cmp "$TMP/selection_recomputed.csv" "$HERE/selection_recomputed.csv"
cmp "$TMP/test_output.txt" "$HERE/test_output.txt"

# Historical baseline actions are scientifically unchanged; compare discrete decisions/resources and re-check Q<=epsilon.
python - "$HERE/baseline_actions.csv" "$TMP/baseline_actions.csv" <<'PY2'
import csv,sys
from decimal import Decimal as D
old=list(csv.DictReader(open(sys.argv[1],newline='')))
new=list(csv.DictReader(open(sys.argv[2],newline='')))
if len(old)!=len(new): raise SystemExit('baseline row count changed')
keys=('shield','epsilon','comparator','status','tau1','tau2','passes','reads','writes','occupied_s','occupancy_percent','u0','u1')
for i,(a,b) in enumerate(zip(old,new)):
    for k in keys:
        if a[k]!=b[k]: raise SystemExit(f'baseline semantic field changed row={i} field={k}: {a[k]} != {b[k]}')
    if b['status']=='CERTIFIED':
        if D(b['Q'])>D(b['epsilon']): raise SystemExit(f'baseline certificate failed row={i}')
print('PASS unchanged baseline decisions/resources')
PY2

# Transient scientific maps are not committed; reproduce their exact hashes.
python - "$TMP" "$HERE/run_manifest.json" <<'PY3'
import hashlib,json,sys
from pathlib import Path
d=Path(sys.argv[1]);m=json.loads(Path(sys.argv[2]).read_text())
for name,want in m['transient_sha256'].items():
    got=hashlib.sha256((d/name).read_bytes()).hexdigest()
    if got!=want: raise SystemExit(f'transient hash mismatch {name}: {got} != {want}')
raw=hashlib.sha256((d/'applicability_resource_summary.csv').read_bytes()).hexdigest()
if raw!=m['applicability_resource_summary_raw_sha256']:
    raise SystemExit(f'applicability raw hash mismatch {raw}')
print('PASS repaired transient scientific hashes')
PY3
printf 'PASS decompressed compact scientific CSV comparison\n'
printf 'PASS RE-GOES-REAL-TEMPORAL-NUMERICAL-REPAIR-01 reproduction\n'
