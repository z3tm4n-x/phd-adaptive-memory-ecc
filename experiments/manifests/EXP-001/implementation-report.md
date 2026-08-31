# EXP-001-VALIDATION-REPAIR-01 — Local Research Engineer report

**Status:** validation repair complete; awaiting Research Orchestrator acceptance
and bounded Scientific Reviewer re-review. This report is not a `RES-xxx`
record and does not alter the EXP-001 scientific question.

## Provenance and unchanged scope

- Canonical base/parent of the repair commit:
  `0ca6f13481ea0818c59395ead26db2f58cb6188e`.
- Original Research Engineer implementation commit:
  `84728d1b5768e7c91c508495d696c5980943ae57`.
- Repair commit: the commit containing this report; resolve with
  `git log -1 --format=%H -- experiments/manifests/EXP-001/implementation-report.md`.
- Fixed bounded config SHA-256:
  `77f78ea988e1ee9106d4f414556fb76a0b6eefec0a2724a04484252c75eb0112`.
- Fixed J-discriminator config SHA-256:
  `e79b9f8914cea2a5a616f1ba0b26c38fe4d09fef4969dc39148ad051502e58c0`.
- Configurations, seeds, model question and scientific assumptions were not
  changed.
- HPP and piecewise-constant NHPP remain synthetic controlled scenarios, not
  selected empirical SRAM models. Swept `epsilon` values remain experiment
  parameters, not project requirements. `L3-E` remains unimplemented.

## MAJOR-01 disposition — independent L0 oracle

`simulation/tests/independent_l0_oracle.py` is a test-only direct physical-event
oracle. It imports no production `exp001` object. From primitive parameters and
plain physical-event fields it independently implements:

- `contiguous_words`: `word=cell//bits_per_word`,
  `bit=cell%bits_per_word`;
- `round_robin_words`: `word=cell%word_count`,
  `bit=cell//word_count`;
- initial-state validation and distinct-error state;
- toggle and `set_error` updates after a complete simultaneous parent mark;
- periodic full reset and `scrub_then_event` boundary ordering;
- complete state snapshots and DEC-001 `E_cap` first passage, including an
  initial exceedance at `t0`.

The oracle does not call or import `physical_to_joint`, `convert_l0_to_l1`,
`PhysicalMapping.map_cells`, `simulate_joint_events`,
`simulate_physical_events`, `_apply_joint_event` or another production mapping/
update helper. A source-level independence guard fails if any prohibited symbol
or production-package import appears in the oracle.

Each tested physical stream is evaluated three ways: directly by the oracle,
through production L0 and through independently prepared production L1. L0 and
L1 are each compared separately with the oracle for `e_cap`, first-passage time,
final state and every transition record `(time, kind, parent_id, state)`.

Coverage comprises 267 streams and 534 separate production-path-to-oracle
complete-trace comparisons:

- 128 exhaustive single-cell streams: all 64 physical cells under each of the
  two fixed 8x8 `W` variants;
- 128 bounded randomized streams: 16 deterministic seeds × two `W` variants ×
  clean/non-clean starts × toggle/`set_error` semantics;
- 11 deterministic streams covering single/multi-cell marks, repeat hits,
  toggle clearing, immediate capability exceedance, sequential accumulation,
  initial exceedance and scrub-boundary ordering.

The mutation/sentinel intentionally applies the contiguous conversion to
physical cell 8 while declaring round-robin `W`. The resulting structurally
valid joint mark passes through the production joint simulator. With word 0 bit
0 initially erroneous, the mutant returns `e_cap=false`, whereas the direct
round-robin oracle returns `e_cap=true`; the complete traces differ. Thus the
repaired gate detects the shared-mapping failure class identified by MAJOR-01.

The fixed production run itself was not expanded into a 768,000-trace run. It
still performs **768,000 outcome/final-signature comparisons**, with zero
mismatch, over 288,302 converted parent-event marks. The independent complete-
trace validation is the bounded test layer described above.

## MINOR-01 — complete analytical validity domain

Every exact endpoint, identified-interval or exact-decision statement in the
repaired EXP-001 artefacts is accompanied by all fourteen required conditions:

1. one declared domain contains exactly four logical words with common
   correction capability `t_c=1`;
2. the reporting window starts from a clean state;
3. every parent event impacts exactly two distinct words;
4. every selected word receives exactly one fresh erroneous bit, with no repeat
   hit, toggle-clear or within-interval repair;
5. every word has one-event impact probability exactly `1/2`;
6. one fixed pair-probability vector is used and pair marks are i.i.d. across
   parent events;
7. pair marks are independent of HPP event times and counts;
8. parent arrivals form a simple HPP, giving Poisson counts and independent
   increments;
9. parent impacts are simultaneous and `E_cap` is evaluated after the complete
   mark;
10. scrubbing is instantaneous, periodic, synchronous and clears the complete
    erroneous-bit state;
11. `t0` is aligned with the scrub phase and the reporting duration is exactly
    `k*T_scrub`, with no partial leading or trailing interval;
12. deterministic-boundary events have probability zero under the HPP and the
    implementation ordering is `scrub_then_event`;
13. `F_A` is the DEC-001 reporting-window first-passage event, so an exceedance
    remains counted even if a later scrub clears the state;
14. every logical word has enough unused bit positions for the generated
    fresh-bit construction over the finite run.

The complete list is also versioned in the EXP specification, Orchestrator
disposition and machine-readable `analytical-validation.json`.

## MINOR-02 — pointwise statistical scope

All Wilson and paired-normal intervals are labelled as pointwise 95% intervals,
not simultaneous intervals. The Wilson-upper-bound restoration decisions are
pointwise-interval-based conservative decisions; they do not provide family-
wise or selection-valid coverage over periods, models or scenarios. The seven
fixed scientific files retain their original columns for byte compatibility;
their statistical scope is stated in the companion analytical validation, run
summary, run manifest and this report.

## MINOR-03 — enforced analytical preconditions

Before any analytical row is generated, validation now enforces:

- exactly four words and `t_c=(1,1,1,1)`;
- a clean initial state;
- nonempty, unique, in-range marks containing two distinct words;
- fresh monotone `set_error` semantics, simultaneous marks and capability
  checking after the complete mark;
- periodic synchronous full reset and `scrub_then_event` ordering;
- `t0`/phase alignment and an integer number of complete intervals for every
  candidate period;
- a positive-rate HPP;
- `total_trials_per_aggregate == len(batch_seeds) * trials_per_seed`.

Fresh-bit capacity is checked over every generated finite stream before
analytical output. The fixed run used at most 7 fresh bit positions in any word
against 128 available. Invalid-config and exhausted-capacity tests are
deterministic.

## MINOR-04 — deterministic and precision-linked analytics

Deterministic tests cover the J-A/J-B `q` endpoints, `S(q,m)`, all eight fixed
exact `F_A` endpoint values and every exact/robust selected-period value over the
epsilon grid. The former standalone `0.02` acceptance gate is no longer used.
The fixed scientific aggregate retains the legacy field only to preserve the
required byte identity. The active gate requires absolute Monte Carlo error to
be no greater than the predeclared maximum Wilson half-width (`0.007`); all eight
checks pass. All eight exact values also lie inside their corresponding
pointwise Wilson intervals.

## Analytical result reporting within the complete domain above

Within exactly the fourteen-condition synthetic domain, the fixed endpoint
probabilities remain unchanged:

| `T_scrub` | Exact `F_A(J-A)` | Exact `F_A(J-B)` | MC J-A pointwise 95% CI | MC J-B pointwise 95% CI |
|---:|---:|---:|---:|---:|
| 0.5 | 0.1090539734 | 0.1660547350 | 0.10560 [0.10142, 0.10994] | 0.16410 [0.15903, 0.16930] |
| 1.0 | 0.1933388517 | 0.2760017321 | 0.19080 [0.18541, 0.19630] | 0.27710 [0.27094, 0.28335] |
| 2.0 | 0.3148651286 | 0.4126072776 | 0.31340 [0.30701, 0.31986] | 0.41445 [0.40764, 0.42129] |
| 4.0 | 0.4586588671 | 0.5488823892 | 0.45625 [0.44936, 0.46316] | 0.54965 [0.54275, 0.55654] |

Exact endpoint-specific selected periods differ at experiment parameters
`epsilon=0.15,0.25,0.35`. At `epsilon=0.55`, exact J-A and J-B both select 4;
the committed pointwise-Wilson rule selects 4 versus 2 because J-B's pointwise
upper endpoint is 0.5565350802. That row is CI-decision conservatism, not a pure
structural difference. The machine-readable exact and robust decision table is
in `analytical-validation.json`.

The admissible interpretation remains narrow: over this tested pair and complete
domain, the declared one-word marginal summary plus fixed two-word event
cardinality does not point-identify `F_A` or every exact restoration decision.
This is not universal marginal insufficiency and does not generalize the tested
L2 reconstruction to other rules or domains.

## Regression verification

- Unit tests: 32 run, 32 passed, zero failures/errors/skips (0.138 s).
- `compileall`: exit code 0.
- Fixed run: all precision and hard invariant checks pass.
- Runtime: 62.05119380000542 s.
- Peak process working set: 25,935,872 bytes via Windows
  `PeakWorkingSetSize`.
- Fixed configs and seeds: unchanged.
- Scientific output differences: zero.

| Scientific file | SHA-256 before | SHA-256 after | Byte-identical |
|---|---|---|---|
| `bounded-aggregate.csv` | `84e3f031da8ed0cb70209b10e9f8f8c06a08f00add8cb7c440db1d92be94804c` | same | yes |
| `bounded-decisions.csv` | `530f37e2f4cc5232a872fa7a96ce28bde2560bd4192866574ae11c7b2ae70ae9` | same | yes |
| `bounded-invariants.json` | `cc316d1892d0aaf181d04c001acf51b02e93f18ac4d64e18aa22fb5fb380ea0f` | same | yes |
| `joint-discriminator-aggregate.csv` | `9aec0a6638cc9a53627558abc67d4a6e54232641b5d188f2656620e739377a53` | same | yes |
| `joint-discriminator-decisions.csv` | `f689c3a008653fc461c8f04f95cb1b411004393ac1e84fb7ed71483386921d79` | same | yes |
| `joint-discriminator-delta.csv` | `acc677f17a9e4a9408dd1d423b69e78c719bf193853dd8ead0ae04e39f1abdbc` | same | yes |
| `joint-discriminator-invariants.json` | `255afd28c55e08b8190b203b1b1e130a2f9167eb9737ef6912f0ab32a2907e65` | same | yes |

Full before/after hashes and machine-readable validation evidence are in
`validation-repair-regression.json`.

## Exact reproduction commands

```powershell
& "C:\Users\Иван\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s simulation/tests -v
& "C:\Users\Иван\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q simulation/src simulation/tests simulation/run_exp001.py
& "C:\Users\Иван\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" simulation/run_exp001.py --bounded-config simulation/configs/EXP-001/bounded-phase1.json --joint-config simulation/configs/EXP-001/joint-discriminator.json --output-dir experiments/manifests/EXP-001 --repo-root .
```

## Deviations, blockers and non-claims

No scientific output changed, no invariant failed and no technical blocker
remains for bounded re-review. No `HYP-xxx`, `RES-xxx`, physical-device claim,
empirical HPP/NHPP claim, numerical project requirement, L3-U/L3-E equivalence,
universal marginal-sufficiency statement or novelty claim was created.
