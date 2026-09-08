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

# Uncompressed scientific/report maps must remain byte-identical.
for f in \
  information_regions.csv \
  information_boundaries.json \
  retention_breakpoints.csv \
  summary.json
do
  cmp "$HERE/$f" "$TMP/$f"
done

# The gzip/base64 artefacts are transport containers.  Scientific reproduction
# is equality of the decoded CSV bytes, not equality of gzip header metadata
# (e.g. the OS byte can differ across Python/platform versions with identical
# payload and trailer).
decode_csv() {
  python3 - "$1" "$2" <<'PY'
import base64, gzip, pathlib, sys
src=pathlib.Path(sys.argv[1])
dst=pathlib.Path(sys.argv[2])
dst.write_bytes(gzip.decompress(base64.b64decode(src.read_text().strip())))
PY
}

for stem in policy_region_map resource_summary
do
  committed="$HERE/${stem}.csv.gz.b64"
  regenerated="$TMP/${stem}.csv.gz.b64"
  decode_csv "$committed" "$TMP/${stem}.committed.csv"
  decode_csv "$regenerated" "$TMP/${stem}.regenerated.csv"
  cmp "$TMP/${stem}.committed.csv" "$TMP/${stem}.regenerated.csv"
  if ! cmp -s "$committed" "$regenerated"; then
    echo "NOTE: ${stem} gzip/base64 container bytes differ, decoded CSV bytes are identical" >&2
  fi
done

STAGE_A_DIR="$STAGE_A_DIR" python3 -m unittest -v "$HERE/test_information_interface.py"
python3 -m py_compile "$HERE/information_interface.py" "$HERE/test_information_interface.py"

echo "PASS: regenerated scientific maps match committed outputs; focused tests and syntax checks passed"
