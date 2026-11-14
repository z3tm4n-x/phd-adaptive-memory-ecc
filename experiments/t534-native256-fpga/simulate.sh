#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
out=$(realpath -m "${1:?scratch directory}")
case "${2:?A0/A1/F0/F1}" in A0) a=1;p=0;; A1) a=1;p=1;; F0) a=0;p=0;; F1) a=0;p=1;; *) exit 2;; esac
mkdir -p "$out/$2"
obj="$out/$2"
verilator --cc --exe --build -j 3 -Wno-fatal --top-module harness -GADAPTIVE=$a -GPROTECTED=$p \
    -CFLAGS '-O3' --Mdir "$obj" "$here"/rtl/{rule,scan_engine,controller}.sv \
    "$here/test/harness.sv" "$here/test/observe.cpp" > "$obj/build.log" 2>&1
: > "$obj/observations.txt"
run() { "$obj/Vharness" "$a" "$p" "$@" | tee -a "$obj/observations.txt"; }
for trial in clean last edges all one_err one_data common_err; do run full "$trial"; done
if ((a)); then
    for level in {1..7}; do run boundary "$level" 0; done
    for defect in {1..5}; do run boundary 1 "$defect"; done
    for kind in 0 1 2; do run recovery "$kind"; done
fi
