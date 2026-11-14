#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
src="$here/../t534-native256-fpga"
out=$(realpath -m "${1:?pass output directory}")
mode_set=${2:-all}
case "$mode_set" in
    all) cases=(F_board A_board F_core A_core);;
    edges) cases=();;
    F_board|A_board|F_core|A_core) cases=("$mode_set");;
    *) exit 2;;
esac
mkdir -p "$out"
for mode in "${cases[@]}"; do
    a=0; b=0
    [[ "$mode" == A_* ]] && a=1
    [[ "$mode" == *_board ]] && b=1
    obj="$out/$mode"
    mkdir -p "$obj"
    verilator --cc --exe --build -j 2 -Wno-fatal --top-module latency_probe \
        -GADAPTIVE="$a" -GBUILTIN="$b" --timescale 1ns/1ns -CFLAGS '-O3' --Mdir "$obj" \
        "$src"/rtl/{rule,scan_engine,controller,config_repair,board}.sv \
        "$src/test/sem_connection.sv" "$here/latency_probe.sv" "$here/read_latency.cpp" > "$obj/build.log" 2>&1
    for plane in 0 1; do
        "$obj/Vlatency_probe" "$a" "$b" "$plane" > "$out/${mode}_$plane.csv"
    done
    if (( ! b )); then
        strict="$out/${mode}_strict.txt"
        if "$obj/Vlatency_probe" "$a" "$b" 0 strict-held > "$strict" 2>&1; then
            echo "Expected the general held-address property to fail" >&2
            exit 1
        fi
        grep -q 'strict ordinary request returned another address' "$strict"
    fi
done
if [[ $mode_set == all || $mode_set == edges ]]; then
    for a in 0 1; do
        iverilog -g2012 -s critical_edges -Pcritical_edges.ADAPTIVE="$a" \
            -o "$out/edges_$a.vvp" "$src"/rtl/{rule,scan_engine,controller}.sv "$here/critical_edges.sv"
        vvp "$out/edges_$a.vvp" | awk '/^(GRANT|VALID|PASS) /' > "$out/edges_$a.txt"
        grep '^PASS' "$out/edges_$a.txt"
    done
fi
if [[ $mode_set == all ]]; then
    python3 "$here/check.py" --record "$out" --results "$out/results" --reference "$here/results/pin-trials.zip"
    cmp "$here/results/summary.json" "$out/results/summary.json"
    cmp "$here/results/pin-trials.zip" "$out/results/pin-trials.zip"
fi
