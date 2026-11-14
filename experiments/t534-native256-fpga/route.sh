#!/usr/bin/env bash
set -eu
here=$(cd "$(dirname "$0")" && pwd)
out=$(realpath -m "${1:?scratch directory}")
case "${2:?A0/A1/F0/F1}" in A0) a=1;p=0;; A1) a=1;p=1;; F0) a=0;p=0;; F1) a=0;p=1;; *) exit 2;; esac
mkdir -p "$out/$2-launch"
cd "$out/$2-launch"
"${VIVADO:-vivado}" -mode batch -source "$here/route.tcl" -tclargs "$out/$2" "$a" "$p" > driver.log 2>&1
test -s "$out/$2/bank.ebd" -a -s "$out/$2/clocked_direction_Fast_max.rpt"
