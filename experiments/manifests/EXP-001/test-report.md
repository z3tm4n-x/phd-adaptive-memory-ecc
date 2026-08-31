# EXP-001 deterministic test report

**Command**

```powershell
& "C:\Users\Иван\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s simulation/tests -v
```

**Environment:** CPython 3.12.13, Windows 11 AMD64, standard library only.

**Final result:** 17 tests run in 0.072 s; 17 passed; 0 failures; 0 errors;
0 skipped.  `compileall` also completed successfully for `simulation/src`,
`simulation/tests` and `simulation/run_exp001.py`.

Covered checks include:

- single-event state trace;
- two-event distinct-bit accumulation;
- repeat-hit toggle behavior;
- immediate `E_cap` from one simultaneous parent mark;
- `scrub_then_event` boundary ordering;
- initial capability exceedance at `t0`;
- deterministic and randomized exact `L0/L1` event/state/trace equivalence for
  both `W` variants;
- exact L2 marginal normalization;
- all mandatory `J-A/J-B` invariants and identical L2 input fingerprint;
- explicit L3-U units and first-moment calibration;
- rejection of `L3-E` and scalar parent-event substitution;
- fixed-config validation, precision validation and reduced end-to-end execution.
