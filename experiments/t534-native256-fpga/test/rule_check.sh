#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
out=$(realpath -m "${1:?scratch directory}")
mkdir -p "$out"
iverilog -g2012 -s policy_tb -o "$out/rule.vvp" "$here/rtl/rule.sv" "$here/test/policy_tb.sv"
vvp "$out/rule.vvp" | tee "$out/rule.txt"
