#!/usr/bin/env bash
set -eu
pkg=$(cd "$(dirname "$0")" && pwd)
base=$(realpath "${1:?path to pinned release worktree}")
out=$(realpath -m "${2:?scratch directory}")
pin=689807698880fe7ef4f3ca6c9e7fa3426493a6f8
mkdir -p "$out"
# Read committed bytes even if a local release checkout has pending edits.
for name in rule core; do git -C "$base" show "$pin:rtl/native64k/$name.sv" > "$out/$name.sv"; done
iverilog -g2012 -s fault_tb -o "$out/fault" "$out/rule.sv" "$out/core.sv" "$pkg/fault_tb.sv"
pids=()
for i in $(seq 0 14); do
    vvp "$out/fault" "+case=$i" > "$out/$i.log" & pids+=($!)
    if [ "${#pids[@]}" -eq 4 ] || [ "$i" = 14 ]; then
        for pid in "${pids[@]}"; do wait "$pid"; done
        pids=()
    fi
done
for i in $(seq 0 14); do grep '^OBS ' "$out/$i.log"; done > "$out/observations.txt"
