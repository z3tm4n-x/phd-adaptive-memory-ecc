# EXP-001 validation-repair test report

**Task:** `EXP-001-VALIDATION-REPAIR-01`

**Base:** `0ca6f13481ea0818c59395ead26db2f58cb6188e`

**Status:** all validation-repair tests and compilation checks pass; bounded
Scientific Reviewer re-review remains required. This is not a `RES-xxx` record.

**Command**

```powershell
& "C:\Users\Иван\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s simulation/tests -v
& "C:\Users\Иван\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q simulation/src simulation/tests simulation/run_exp001.py
```

**Environment:** CPython 3.12.13, Windows 11 AMD64, standard library only.

**Final result:** 32 tests run in 0.138 s; 32 passed; 0 failures; 0 errors;
0 skipped. `compileall` completed with exit code 0 for `simulation/src`,
`simulation/tests` and `simulation/run_exp001.py`.

Covered checks include:

- single-event state trace;
- two-event distinct-bit accumulation;
- repeat-hit toggle behavior;
- immediate `E_cap` from one simultaneous parent mark;
- `scrub_then_event` boundary ordering;
- initial capability exceedance at `t0`;
- independent test-only physical-event oracle with no import or reuse of the
  production mapping/conversion/state-transition implementation;
- 267 physical streams, each comparing production L0 and production L1
  separately with the oracle's complete transition trace (534 path-to-oracle
  comparisons);
- exhaustive single-cell checks for every cell in the fixed 8x8 domain under
  both `contiguous_words` and `round_robin_words` (128 streams);
- 128 bounded randomized streams over both `W` variants, clean/non-clean starts
  and toggle/set_error semantics;
- deterministic oracle cases covering single/multi-cell marks, repeat hits,
  toggle clearing, immediate `E_cap`, sequential accumulation, initial
  exceedance and scrub-boundary ordering;
- mutation/sentinel: an intentionally contiguous-converted mark declared as
  round-robin is accepted by the production joint simulator but rejected by the
  independent oracle trace and `E_cap` comparison;
- exact L2 marginal normalization;
- all mandatory `J-A/J-B` invariants and identical L2 input fingerprint;
- explicit L3-U units and first-moment calibration;
- rejection of `L3-E` and scalar parent-event substitution;
- enforcement of exactly four words, `t_c=1`, clean start, valid two-word marks,
  full reset, phase/window alignment, fresh-bit capacity and declared trial
  total before analytical output;
- deterministic `q` endpoints, `S(q,m)`, fixed `F_A` values and exact decision
  table checks;
- machine recording of all fourteen analytical validity conditions;
- fixed-config validation, precision-linked analytical validation and reduced
  end-to-end execution.

The fixed full experiment was also rerun. All seven scientific files are
byte-identical to their canonical pre-repair versions; see
`validation-repair-regression.json`.
