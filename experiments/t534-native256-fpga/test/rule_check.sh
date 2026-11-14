#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
out=$(realpath -m "${1:?scratch directory}")
mkdir -p "$out"
iverilog -g2012 -s policy_tb -o "$out/rule.vvp" "$here/rtl/rule.sv" "$here/test/policy_tb.sv"
vvp "$out/rule.vvp" | tee "$out/rule.txt"
for mode in 0 1; do
    iverilog -g2012 -s sem_connection -Psem_connection.ADAPTIVE=$mode -o "$out/sem$mode.vvp" \
        "$here"/rtl/{rule,scan_engine,controller,config_repair,board}.sv "$here/test/sem_connection.sv"
    vvp "$out/sem$mode.vvp" | tee "$out/sem$mode.txt"
done
