# CY62167 Physical Bridge — Scientific Re-review 02

Date: 2026-09-12. Role: independent Scientific Reviewer.

## 1. Scope and recommendation

**Recommendation: REVISE.** No CRITICAL finding. One new, bounded MAJOR concerns the justification and validation of the claimed conditional-write repair. It is repairable without a new physical experiment, rate regeneration, controller redesign, or a general CY62167 review.

The exact scientific target is **`c48ca29eb65fee96154d645819c4e533a1709037`**, all 15 files of `experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01/`. The assignment is `eef9068591d6e125dd273dbf615216cec23df99b:docs/research_gates/CY62167-PHYSICAL-BRIDGE-SR-HANDOFF-02.md`. Prior review: `18b78a647ac299290b5e2399b8af581e14240b88`; repair assignment: `d4918569e278289e300eee8bb0504211b23ac92b`; scientific input base: `69e92fe36b3b7933cebccbedd457cc0309dd4d1c`.

This independent report is based on documentary commit **`a0287a33326393ffdabf2ae14a096abaf3e929c5`**, not on the detached RE delivery. Publication of this report does not update the blocked RE branch, import its delivery into main, or accept Issue #15. GLOBAL, the Scientific Reviewer role, HANDOFF_CONTRACTS, prior review/disposition, the repair assignment and the complete target package were inspected.

The old complete physical witness and numerical coverage threshold are withdrawn consistently in the operative numerical outputs. Neither has been proved by the repair. The pair-exposure coefficient admits a useful, weaker proof, given below. However, the ideal-at-read comparison does not justify the claimed physical-only RMW correction as written; the four fixed-state assertions are not an executor validation. The distinction is substantive, not a demand for a more general model.

## 2. Disposition of the previous findings

| Previous finding | Original stronger claim proved? | Stronger claim withdrawn? | Original goal still open? | Disposition |
|---|---|---|---|---|
| MAJOR-01: complete compatible, opposite-decision actual-CY `m0/m1` pair | No | Yes for the actual-device witness; conditional maximum wording still needs the passing-`m0` premise | Yes | Overclaim removed, not evidentiary closure. Conditional extension is narrower; see §3. |
| MAJOR-02: selected-slice conditional-write physical upper and numerical omitted-route margin | No | Yes: both numerical outputs are null; the old margin is explicitly arithmetic only | Yes | Historical numerical overclaim removed. New symbolic/executor claim requires the local MAJOR below. |
| MINOR-01: sharpness, minimality and `[0,1]` identified-set wording | No new sharpness/minimality theorem | Yes | Not required for the weaker results | CLOSED by scope correction. `[0,1]` is only a trivial enclosure. |
| MINOR-02: machine decision status vocabulary | Not a scientific proof question | Mixed status vocabulary removed | No schema blocker | CLOSED as a schema repair: one of `SUFFICIENT`, `INSUFFICIENT`, `NOT_ESTABLISHED`. The truth of the CW `SUFFICIENT` row is a separate issue. |
| MINOR-03: SOURCE/ASSUMPTION/UNKNOWN and actual source access | Current reread/rehash is recorded by RE, not independently repeated here | Historical identity and current access are now distinguished | Run-specific protocol qualification remains open | PARTIALLY CLOSED. Archive identity does not establish file/segment-to-ECC-disabled protocol linkage. The required derived filename is also misidentified; see §7. |

These dispositions must not be condensed to “both MAJOR scientifically closed.” Removal of an unsupported positive conclusion is legitimate progress, but is not its proof. Previously accepted D3/`2t+1`, conditional coverage and 329004-case evidence were not reopened or rerun.

## 3. Conditional extension: what is and is not established

REPORT §5.2 correctly makes existence of a complete compatible `m0` and admissibility of an observation-invariant hidden extension assumptions. Under that extension, an atomic three-distinct-cell mark in one fixed SEC word is the previously accepted all-policy capability-exceedance event. If its horizon probability is greater than the same experimental epsilon, it supplies an excluding lower bound in `m1`.

An **opposite-decision pair additionally requires a policy in `m0` with full-device first-passage probability at most epsilon**, on the same horizon, initial/service state and information contract. A changed lower bound alone does not supply this positive side. REPORT §9's “opposite-decision theorem only conditional on ... closed” omits that premise. Add it, or call the result an observation-invariant extension that changes an excluding lower bound. Ledger `SAME` entries mean “held equal by this hypothetical construction,” not verified compatibility of two completed CY models.

Absence of a recovered proprietary W or measured parity law is not proof that compatible completions cannot be constructed. Conversely, registered cluster records, external-address recovery and a restricted mapping family do not establish such completions. No physical probability for a hidden parity triple has been supplied. The relevant event remains `E_cap`, not DUE, SDC, or system failure.

Concrete decision-capable information is a qualified full-word D3 lower bound exceeding epsilon, or a qualified registered upper plus an omitted-route upper at most epsilon. An opposite-decision witness instead needs an explicit admissible passing completion and an admissible excluding extension preserving all included observations. No universal requirement to recover every proprietary topology detail follows.

## 4. New MAJOR-01: conditional-write inclusion and probabilistic qualification

### 4.1 A falsifying execution trace

REPORT §§1, 3.1 and 7 claim that transition semantics are explicit and executable. `repair_checks.py:semantic_checks()` instead assigns four fixed set states; it does not execute read/check, conditional latching, delayed writeback and both coupled processes along a timeline. `independent_check.py` checks two bitmask examples, not this execution.

The stronger inclusion suggested by “ideal-at-read ... plus additional physical-only RMW path” is false if the RMW bad event counts only a hit distinct from the singleton observed at read. Start clean, use two bits `b,c` in one word, check at time 1 and complete the latched correcting write at 1.2. There are no other writes. First passage is sticky.

| Time/action | Physical stored errors | Ideal-at-read errors |
|---|---|---|
| 0.5: toggle b | b | b |
| 1: singleton check; physical clean image latched, ideal reset | b | empty |
| 1.1: toggle b during RMW | empty | b |
| 1.2: commit latched clean image | empty | b |
| 1.3: toggle b | b | empty |
| 1.4: toggle c | b,c: first passage | c: still safe |

There is **no distinct-from-b hit during RMW**, and no ideal first passage, yet physical first passage occurs after writeback. Thus `E_CW` is not included in `E_ideal-at-read union B_distinct-RMW`. The ordering survives small perturbations of arrival times and scales to any positive write delay shorter than the next check interval; it is not an isolated equality artifact. It is not a calibrated CY trace.

The supplied independent checker executes a componentwise state/latch timeline without importing RE simulation logic. Across 4096 small three-bit streams, 60 violate this stronger inclusion. This finite result supports the counterexample, not a universal correctness claim.

### 4.2 A weaker inclusion preserves a useful pair term

The counterexample does **not** disprove the final pair-plus-RMW numerical form. Replace ideal failure by the larger event **P: at least two distinct bit arrival labels occur in a deterministic inter-check interval**, including the initial and final partial intervals. Let B count a hit in a bit distinct from the observed singleton during its pending correcting write.

Under the following conditions, `E_CW subset P union B`:

- Clean start with no pending write; fixed actual per-word check times; all initial, complete and final inter-check intervals have length at most tau.
- The clean branch does not write. A singleton check latches the clean corrected image, whose write completes before the next check of that word; there are no other writes or decoder/controller faults. First passage is historical, not erased by later repair.
- Atomic single-bit toggles; no simultaneous direct multibit parent marks in this registered submodel.

Proof: consider the interval containing the first physical exceedance. If its opening check was clean, two distinct arrival labels are necessary. If it was singleton, a distinct hit before the correcting write is charged to B. Without B, only the original bit can toggle before that write, which commits a clean image. Any subsequent exceedance before the next check requires two distinct post-write arrival labels, hence P. The initial interval starts clean. This also treats a horizon ending before the pending write.

For independent simple per-bit NHPP arrivals within each word with common deterministic rate r(t), P has the bound

`Pr(P) <= W*C(32,2)*sum_intervals (integral_I r)^2 <= W*C(32,2)*tau*integral_H r^2`.

For different word phases the interval sums are taken separately for each word before applying the common upper. Independence across words is unnecessary for this union bound. This bounds the enlarged arrival event, not exact toggle first passage. Fixed or otherwise separately justified interval selection matters; realized event-dependent partitions cannot silently inherit the deterministic Poisson calculation.

### 4.3 The singleton-check sum needs an expectation

The REPORT §3.2 set R of actual singleton checks is random. Its realized exposure sum is not a deterministic bound on an unconditional probability. For deterministic potential checks `c_wk`, singleton indicators `J_wk` measurable at the check, and a deterministic/past-known completion-delay upper `D_wk`, an adequate statement is

`Pr(B) <= 31*E[sum_wk J_wk * integral_[c_wk,min(c_wk+D_wk,H)] r(t) dt]`

`<= 31*sum_wk integral_[c_wk,min(c_wk+D_wk,H)] r(t) dt`.

This uses exogenous deterministic rates and independent future increments; an endogenous intensity requires its conditional-intensity/compensator justification. A future-dependent observed completion time must not be treated as a deterministic window without that argument. A safe deterministic delay upper avoids this problem. The all-check envelope removes the random singleton selection, but still needs the actual schedule.

### 4.4 Duty reduction: sufficient conditions, not an automatic objection

Let `K_D(t)` count the all-check RMW windows covering t. The deterministic envelope is `31*integral K_D(t)*r(t) dt`. An average duty factor alone does not upper-bound this weighted integral. A one-word pulse wholly inside a write window with D/tau=0.1 gives exposure 1 versus duty-weighted 0.1 in the checker's synthetic fixture. This is not a counterexample to the frozen 300-second rate-bin interface.

There is a useful exact qualification: checks `c_wk=phi_w+k*tau` with fixed phases, a common delay upper D less than tau, clean start/no pending pre-window writes, and r constant on blocks containing integer numbers of tau periods. The exposure identity also allows D=tau, but the executor inclusion then needs write-completion-before-next-check ordering explicitly. Integrating the periodically extended window-count function over each complete block gives `W*D/tau` times that block's rate integral. Removing pre-start windows and truncating at H can only decrease exposure. Consequently a zero additional schedule-boundary term **can be valid** when the rate blocks and horizon have this alignment, including 300-second constant bins with tau=1 second and a 24-hour window. Uniform staggering is not needed for this integral identity; periodic phases are.

The checker also integrates an eight-phase finite schedule across a rising 300-second boundary and obtains 504.00 for both the all-check and duty exposures. This illustrates the identity, not the actual CY executor. A maximum-gap promise alone does not imply periodic check frequency: extra checks can increase the RMW term. With arbitrary rate variation one can instead integrate K directly or provide a proven pointwise/window boundary envelope. Do not set `boundary_term=0` because it is a function default, and do not demand a positive correction when the above exact alignment is actually established.

### 4.5 Smallest correction and closure criterion

**MAJOR-01 corrective action:** replace the invalid ideal-failure decomposition with the enlarged pair-arrival event (or supply another valid proof); state the expectation/all-check envelope and actual schedule/delay conditions; revise the corresponding `SUFFICIENT` claim; add the same-bit RMW trace as a genuine coupled read/write regression. Correct the synthetic “exact” event label discussed below.

**Closure:** a complete event inclusion and probabilistic bound under explicit conditions, plus a trace-level checker retaining clean/no-write, pending latch/write, cancellation and sticky first passage. The counterexample must be recognized as physical failure without ideal failure, not forced to satisfy the invalid inclusion. No new CY numerical upper or production rerun is required to close this local symbolic claim. The proof in §§4.2–4.4 supplies a bounded route; missing proof of the stronger comparison does not invalidate that weaker result.

## 5. Local MINOR issues and validation limits

### 5.1 Optional numerical input is not qualified by its current status label

The optional `--rate-summary` path is unused in the frozen reviewed run. Nevertheless, both scripts accept a matching slice and an unattested synthetic zero summary as `QUALIFIED_BY_SUPPLIED_FROZEN_SUMMARY`. They also accept I1=I2=-1. The main script then reports pair=-260046848.0, a negative total bound and passing decisions. These are deliberately invalid input probes, not substituted scientific inputs.

The hash of received bytes is not provenance, positivity, outward rounding, or executor qualification. `independent_check.py` is weaker still and does not independently validate source identity or the boundary contribution. Two rearrangements of the same expression share its assumptions.

**MINOR; inactive-path limitation:** exclude this interface from present acceptance. Before using it to release a number, reject nonfinite/negative or incompatible summaries, validate source/slice/rate units and one-sided integrals, and require the schedule/delay/boundary contract. Otherwise label it an unvalidated supplied-summary calculation, not qualified evidence. No current false CY certificate is present because both frozen outputs are null.

### 5.2 “Exact pair first passage” is an enlarged event, not exact toggle risk

The inline QA source is not committed; successful re-arithmetic cannot recover its historical independence. The saved `exact_pair_first_passage=0.0005900073006648299` for n=3, r=0.01, two unit intervals matches the probability of two distinct arrival labels in at least one interval: 0.000590007300664386 (within floating-point rounding).

An independent Poisson-event-count recurrence for actual toggle first passage gives **0.000588062091637824**, not that value. The recurrence tracks safe zero/singleton states and loss into the absorbing failure state; it does not reuse RE's formula. Both are below the pair upper 0.0006. The independent distinct-RMW calculation is 0.003992010656008528, below 0.004.

**MINOR terminology correction:** identify exactly which event the QA computes. Its arithmetic supports the enlarged pair event used in §4.2, not an exact toggle-risk oracle. The delivered four set fixtures and two bitmask fixtures establish only their individual state identities; neither is independent CW execution validation. That stronger claim is addressed by MAJOR-01.

### 5.3 Conditional and certificate decision wording

**MINOR:** add the passing-`m0` premise to REPORT §9, qualify hypothetical `SAME` ledger entries, and correct HANDOFF's suggestion that `U_reg_CW >= epsilon` falsifies the positive registered-side candidate. An upper strictly greater than epsilon fails that sufficient certificate, not necessarily the underlying risk condition; equality passes an inclusive `Q <= epsilon` rule. A proven lower bound greater than epsilon is a different, excluding statement. These require local wording changes, not a new study.

## 6. Actual reproduction and independently performed checks

Before execution, the nine MANIFEST delivery entries were checked for Git blob identity, byte size and SHA-256. All matched. The three pre-execution source/config blobs match target and `b386d8ff...`:

| File | Git blob |
|---|---|
| config.json | `5bd359ab8dfc991d614b8fbcd7cdbae438eeee6d` |
| repair_checks.py | `9f083d3a78723fbdb573441318b1d886d0a008ce` |
| independent_check.py | `2a453113f1f897c3011f2fc097635883689e092c` |

Git history confirms the target's single immediate parent `b386d8ff...`, ten delivery additions, and six commits/15 repair-only additions relative to `0c979c34...`. That verifies committed sequencing, not an independent timestamp of calculations.

An isolated copy of the exact package was materialized from Git. Commands actually completed there:

```sh
python3 repair_checks.py --config config.json --out outputs/repair_checks.json
python3 independent_check.py --config config.json --out outputs/independent_check.json
python3 -m py_compile repair_checks.py independent_check.py
```

All exited successfully. Four set-state and two bitmask checks passed. Both resulting JSON files are byte-identical to the reviewed outputs, both `bound=null`, `rate_qualification=NOT_ESTABLISHED`:

- repair_checks.json: `c7db9010bcf5d6c90ac15b47ab12e9b7e0037e1f5dd807cfd43630d1eee4013f`.
- independent_check.json: `e5f6d7e161e92144fead972bfc0ac1a0501d5a96734dee3295c7dfdb3c9d644c`.

RE records Python 3.13.5 / Linux 6.18.35 x86_64 / stdlib. SR used Python 3.12.14 (Clang 22.1.3), Linux 6.18.35 x86_64, glibc 2.39, stdlib. This is deterministic reproduction of the actual narrow outputs, not independent confirmation of the physical upper.

Own checker, included with this report, was run as:

```sh
python3 -B /workspace/scratch/24e1723b7ed9/physical-bridge-review-02/docs/scientific_reviews/checks/cy62167_physical_bridge_review_02.py /workspace/scratch/24e1723b7ed9/repo /workspace/scratch/24e1723b7ed9/physical-bridge-r2-checks.AqpNQE/experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01
```

It checks exact RE source identities before the optional CLI probes. Its independent timeline enumerated 4096 streams: 60 counterexamples to ideal-failure-plus-distinct-RMW, zero to the larger pair-event inclusion in that finite fixture. Its independent arithmetic, exact window integrals and invalid-input probes gave the results above. Initial comparison of the saved synthetic “exact” value with the independent toggle recurrence failed; diagnosis identified the different distinct-arrival event, which the final checker distinguishes explicitly.

Analytical proofs and independent timeline/arithmetic checks are distinct from shared-formula consistency and frozen-output regression. No claim here relies on hash equality as scientific validation. The original frozen outputs were not overwritten; no upstream environment, old 329004 cases, Monte Carlo, mapping fit or controller comparison was run.

## 7. Correct rate input and residual provenance limitation

The repair misnames the required file in REPORT, HANDOFF, input and decision descriptions. Exact-target Git evidence identifies:

| Object | Verified identity / significance |
|---|---|
| Required derived file | `experiments/RE-CY62167-ECC-RISK-BRIDGE-01/direct_rate_5min.csv` |
| Full-file identity in `full_output_manifest.json` | SHA-256 `c10a68e721716c8c9b96bf99a9e2d1de0bd3b179ebcc747b3fd149ff0741ff83`; 237888 rows, 53420841 bytes |
| Manifest Git blob | `ba08014e869fd82fe9b7a89017038c7d053d3824` |
| Committed derived-file stub | 512 bytes; Git blob `3e845b9da6ea6669b5538629e3fcb18dad69737c`; not the full numerical trace |
| Different, present upstream file | `experiments/RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv`; 13002858 bytes; blob `5de108c6759bcf720073b3fbc6581389d46e63aa` |

Read-only inspection of decoded `risk_bridge.py.zlib.b85` confirms that it writes `direct_rate_5min.csv` and divides the selected accumulated-bit rate by `N_DATA_BITS=2^24`. The needed DREG residual field is `nu_C_bit_DREG_s-1`, not `r_D_DREG_s-1` or an unconverted upstream proton rate. The selected frozen window, 10-mm shielding, main_loglog/central_mean convention and DREG population must remain unchanged. I1 is per-bit integrated rate (dimensionless); I2 has inverse-time units.

**MINOR correction:** fix the name/path; limit absence claims to inspected locations. The presence of the different upstream table does not establish equivalence or authorize substitution. This review did not search all storage, reread the raw irradiation runs, rehash the external archives, or independently repeat RE's PDF rereads. RE's recorded current source access is evidence of that reported activity, not proof of every segment's ECC-disabled protocol. Qualify the remaining blanket protocol assertion as an assumption unless a run/segment-specific source link is supplied.

The exact full derived file, or traceably source-equivalent outward I1/I2 with the rate/schedule qualifications needed for their use, can remove the numerical input gap. It does not establish the executor delay bound, full-device omitted routes, or the compatibility of a physical `m0/m1` pair.

## 8. Maximum defensible result and limited acceptance

The following wording is scientifically admissible now, with the reviewer-qualified event distinction and conditions:

> The repair withdraws the previously unqualified actual-CY opposite-decision witness and numerical full-device coverage threshold. Under a clean-start, data-only registered model with independent per-bit single-arrival streams, fixed per-word check partitions of maximum length tau, and the explicitly bounded conditional-write executor, capability first passage is covered by a distinct-pair-arrival event or a distinct-hit pending-write event. The former has the phase-free upper `W*C(32,2)*tau*integral r^2`; the latter requires an expected singleton-check exposure or a deterministic all-check exposure envelope. A duty-factor simplification additionally requires an appropriate periodic schedule/rate alignment or a proved boundary envelope. No selected-slice numerical CW upper or actual full-device decision is established. The hidden-parity extension is conditional on compatible completions and observation-invariant admissibility; an opposite decision additionally requires a passing base completion.

The 32-data-bit calculation is not complete `(32,38)` data-and-parity reliability. It supplies no hidden-event occurrence probability, full-device `delta_cov`, measured controller delay, or system reliability requirement. Datasheet `tWC >= 45 ns` is a minimum cycle time, not the needed check-to-write upper. Experimental epsilon is not a project requirement. Certificate failure is not physical infeasibility.

**Limited acceptance is admissible** for the withdrawal of the old overclaims, the retained previously accepted structural results, the reproducible null numerical disposition, and the carefully qualified enlarged-event argument in this review. It is **not** admissible for the delivery's unqualified “transition semantics repaired” status or a completed physical bridge. Before accepting the new symbolic/executor repair as delivered, close MAJOR-01 and make the local terminology/interface scope corrections above. This needs an addressed proof-and-trace repair, not a broad experimental cycle.

For the original bridge, the concrete remaining requirements are: a qualified frozen rate summary/trace; an actual check schedule and correcting-write delay upper satisfying the selected bound; a justified omitted-route upper or decisive full-word D3 lower bound for the same domain; and, if an opposite-decision witness is still sought, an admissible passing completion plus the observation-invariant excluding extension. These are alternative decision routes where indicated, not a demand to obtain all physical information universally. Issue #15 remains open. No new result is registered and no next execution is authorized by this review.
