# EXP-001-IMPLEMENTATION-01 — Local Research Engineer report

**Status:** technical implementation and bounded synthetic execution complete;
awaiting Research Orchestrator acceptance and Scientific Reviewer inspection.
This report is not a `RES-xxx` record.

## Provenance and scope

- Base commit: `e1e7b93cc72b7b295a8298560adf2cd507d7256b`.
- Implementation commit: the commit containing this report; resolve with
  `git log -1 --format=%H -- experiments/manifests/EXP-001/implementation-report.md`.
- Inputs: synthetic and fully declared in
  `simulation/configs/EXP-001/bounded-phase1.json` and
  `simulation/configs/EXP-001/joint-discriminator.json`.
- HPP and piecewise-constant NHPP are controlled scenarios, not selected
  empirical SRAM models.
- Every swept `epsilon` is an experiment parameter, not a project reliability
  requirement.
- `L3-E` is not implemented.

The handoff named
`docs/questions/RQ-002-minimum-adequate-sram-radiation-error-model.md`.
That path does not exist at the exact base commit.  The canonical file at that
commit, `docs/questions/RQ-002-sram-radiation-error-model.md`, was read and used.

## Implemented semantics

- `L0`: parent event, explicit physical-cell topology and deterministic `W`.
- `L1`: joint post-`W` word/bit mark retaining parent ID and epoch.
- `L2-independent_word_marginals`: exact enumerated per-word multiplicity PMFs;
  each word is reconstructed independently at the reused parent epoch, with
  uniform-without-replacement bit allocation.
- `L3-U`: individual ungrouped bit-toggle arrivals over `A`, uniformly allocated
  over logical cells.  Its intensity is in
  `ungrouped_upsets_per_arbitrary_time_unit_over_A` and is first-moment calibrated
  to expected total upset exposure over `A`.  This is not a stochastic-process
  equivalence claim.
- Main matrix update: simultaneous parent mark with repeat-hit toggle semantics.
- `J-A/J-B` update: one fresh monotone bit per selected word and parent event,
  with common parent epochs.
- Restoration: periodic synchronous global clear; at an exact boundary the scrub
  transition precedes the event transition.
- Decision rule: select the maximal candidate scrub period whose 95% Wilson CI
  upper bound is no greater than the swept `epsilon`.

## Hard invariant and precision results

- `L0/L1`: 768,000 trajectory state/outcome checks, zero mismatches; 288,302
  converted parent-event marks checked.
- `J-A/J-B`: all words have exact per-event impact probability `1/2`; exactly two
  words are impacted; derived L2 marginal inputs are identical; pair association
  differs; no parameter outside the joint subset distribution differs.
- Joint run: 39,742 common parent epochs and 158,968 fresh-bit updates checked.
- `L3-U`: all six first-moment calibration checks pass.  Expected total exposure
  is 3 for the single-cell scenarios and 9 for both three-cell scenarios.
- Maximum 95% CI half-widths: bounded `F_A` 0.010954 (limit 0.011), joint `F_A`
  0.006929 (limit 0.007), paired `Delta F_A` 0.004177 (limit 0.008).

## Mandatory joint discriminator

`Delta F_A` is defined as `F_A(J-B) - F_A(J-A)`.

| `T_scrub` | `F_A(J-A)` (95% CI) | `F_A(J-B)` (95% CI) | paired `Delta F_A` (95% CI) |
|---:|---:|---:|---:|
| 0.5 | 0.10560 [0.10142, 0.10994] | 0.16410 [0.15903, 0.16930] | 0.05850 [0.05525, 0.06175] |
| 1.0 | 0.19080 [0.18541, 0.19630] | 0.27710 [0.27094, 0.28335] | 0.08630 [0.08241, 0.09019] |
| 2.0 | 0.31340 [0.30701, 0.31986] | 0.41445 [0.40764, 0.42129] | 0.10105 [0.09687, 0.10523] |
| 4.0 | 0.45625 [0.44936, 0.46316] | 0.54965 [0.54275, 0.55654] | 0.09340 [0.08937, 0.09743] |

The selected restoration period differs between `J-A` and `J-B` at swept
`epsilon = 0.15, 0.25, 0.35, 0.55`.  Relative to `J-B`, using `J-A` is
false-safe at one candidate period for each of those four values; the reverse
comparison is correspondingly false-conservative.  The declared L2 rule differs
from `J-A` at one swept `epsilon` and from `J-B` at three swept `epsilon` values.

**Admissible interpretation only:** for this tested pair/domain, the declared
per-word marginal summary alone does not identify `F_A` or the restoration
decision.  This does not establish universal marginal insufficiency and does not
generalize the behavior of the tested L2 reconstruction to other rules.

## Bounded representation comparison

The matrix contains 384 `F_A` rows and 768 decision rows over two `W` variants,
three topology classes, HPP/NHPP scenarios, clean/non-clean initial states, four
candidate scrub periods and four representations.

| Reduction | signed error range vs `L1` | maximum absolute error | mean absolute error | false-safe / false-conservative decision rows | selected-period discrepancies |
|---|---:|---:|---:|---:|---:|
| `L2-independent_word_marginals` | [-0.093375, 0.054625] | 0.093375 | 0.049581 | 4 / 6 of 192 | 10 of 192 |
| `L3-U` | [-0.555125, 0.266750] | 0.555125 | 0.134807 | 10 / 20 of 192 | 30 of 192 |

Both signs occur.  No conservatism direction is inferred.  The largest absolute
error occurred when a three-cell topology concentrates within one word under one
`W`, while L3-U discards that grouping.

Ten small adjacent point-estimate reversals in the `T_scrub` ordering were found;
the largest decrease was 0.001875.  This is not a failed invariant: under toggle
semantics, a repeat hit can clear an error, so monotonicity in scrub period was not
assumed.  Decisions therefore use the explicit feasible set rather than assuming
it is a prefix of the candidate-period grid.

## Runtime, memory and retained outputs

- Final wall time: 74.900 s.
- Peak process working set: 25,772,032 bytes (Windows `PeakWorkingSetSize`).
- Raw trajectories: not persisted; Bernoulli and paired counts were aggregated
  online.  No external raw-output path exists for this run.
- Bounded aggregate tables and invariant manifests are retained in this directory.
- Scientific decision/delta tables were reproduced byte-for-byte in repeated runs;
  checksums are recorded in `reproducibility-verification.json`.

## Non-claims and remaining gates

These outputs do not establish a target SRAM model, empirical HPP/NHPP adequacy,
a numerical system requirement, a decoder/system outcome, a final cost function,
universal marginal sufficiency/insufficiency, L3-U/L3-E equivalence or novelty.
No `HYP-xxx` or `RES-xxx` was created.  Orchestrator acceptance and adversarial
Scientific Reviewer review remain required.
