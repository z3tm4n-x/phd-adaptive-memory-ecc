# CY62167 Physical Bridge — Scientific Re-review 03

Date: 2026-09-13. Role: independent Scientific Reviewer.

## 1. Target, scope and verdict

**Recommendation: PASS_WITH_MINOR in the fixed-window domain below. No blocking CRITICAL or MAJOR remains in this local repair.** SR-02 MAJOR-01 is CLOSED for the corrected event inclusion, deterministic-window probability bound and the specified finite executor validation. One MINOR remains: the expectation cannot be removed for merely past-known, random delay bounds. This review gives the exact corrected scope; a broader random-delay theorem is not needed for acceptance of the deterministic case.

Exact scientific target: **`d3cd3e9385f62f047954ce3e54454eb5976ddcb8`**, all 16 files of `experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-02/`.

Assignment and this review branch base: **`631169dafa34e4e5ebc107f37e5882f58c575b2c`**, `docs/research_gates/CY62167-PHYSICAL-BRIDGE-SR-HANDOFF-03.md`. RE assignment: `ec6b1b3cd10ff1268979c60e08167279603f23d5`. Controlling prior review: **`57021de76b45971ca2687e69c4a890f02647df8f`**, especially §§4–8. The erroneous earlier repair `c48ca29eb65fee96154d645819c4e533a1709037` remains historical, not the reviewed implementation.

GLOBAL, the Scientific Reviewer role, HANDOFF_CONTRACTS, current status, the bounded RE/SR assignments, prior findings and the complete target package were considered. Current-status engineering acceptance is not scientific evidence. Previously accepted D3/coverage results and RES were not reopened. No rate reconstruction, physical campaign, controller comparison or new result registration was performed.

The numerical CY62167 bound, actual executor WCET, full-device coverage and actual-CY opposite-decision witness remain **NOT_ESTABLISHED**. They are deliberately outside this repair's completion criteria, not new defects or reasons to withhold its limited acceptance.

## 2. Disposition of SR-02

| SR-02 issue | SR-03 disposition | Evidence and remaining boundary |
|---|---|---|
| MAJOR-01: invalid ideal-failure/RMW decomposition, missing expectation and inadequate executor evidence | **CLOSED for fixed deterministic windows** | REPORT §3 now proves `E_CW subset P union B`; an event-driven executor and independent production-linked checks support the declared finite domain. The residual random-D extension is the MINOR in §4. |
| §5.1: optional rate-summary falsely qualified supplied inputs | **CLOSED by exclusion/removal in this package** | Neither new checker exposes `--rate-summary`; physical output is null and the acceptance interface is `EXCLUDED`. No new numerical qualification pipeline is claimed. Historical scripts are not repaired or accepted by this finding. |
| §5.2: synthetic distinct-arrival probability labelled as exact toggle first passage | **CLOSED** | `distinct_arrival_event_probability` is now explicit, with committed arithmetic source. It is not `F_CW` or exact ideal-toggle first passage. |
| §5.3: missing passing-m0 premise and upper/lower decision wording | **CLOSED by narrowing/correction** | No actual opposite-decision pair is claimed; a passing complete m0 is expressly required for that stronger conclusion. `upper > epsilon` is certificate failure; equality passes an inclusive rule; exclusion needs a qualified lower greater than epsilon. |
| §7 / inherited MINOR-03: wrong derived-file identity and run-protocol overclaim | **CLOSED as a scope/provenance correction** | Correct `direct_rate_5min.csv` path and `nu_C_bit_DREG_s-1 / 2^24` expression; run/segment ECC-disabled linkage remains ASSUMPTION/UNKNOWN, not established by archive hashes. The physical evidence itself is not newly supplied. |

The original complete witness and numerical-margin goals of SR-01 were not proved retrospectively. Their unsupported stronger formulations remain withdrawn. This is closure of a local proof/executor defect, not completion of Issue #15.

## 3. Independently assessed event inclusion and pair bound

### 3.1 Correct event, executor and initial/final state

P is the occurrence of at least two **distinct arrival labels** in one deterministic inter-check interval of any word. It is not the instantaneous stored-error set and not exact ideal-at-read failure. B is a hit in a bit different from the observed singleton's bit while its correcting write is pending. The observed origin remains stored even when a same-bit hit temporarily clears physical storage.

The interval proof in REPORT §3 is valid. Before the first physical exceedance, an opening check can be clean or singleton. A clean opening has no write, so exceedance requires two distinct arrival labels. At a singleton opening with origin b, either a distinct bit arrives before write completion, which is B, or only b toggles until the latched clean image is committed. Subsequent exceedance then requires two distinct post-commit labels in that same inter-check interval, which is P. The initial interval starts clean. If H cuts a pending write, absence of B leaves at most the original erroneous bit; a failure before H is therefore still covered. A later clean write cannot erase historical first passage.

Thus **`E_CW subset P union B`**, under the following material conditions:

- Clean start, no pending write; predetermined potential check times for each word.
- Clean checks do not write; singleton checks latch the corrected clean image and complete that write before the next check of the same word. No competing writes or decoder/controller faults.
- Atomic single-bit toggles in this registered submodel; no simultaneous multibit parent marks. Arrival/check and arrival/commit coincidences are excluded for deterministic traces and have probability zero in the stated continuous NHPP model with fixed timings.
- P uses the actual deterministic partition, including initial and final partial intervals. Failure is sticky.

The old inclusion through exact ideal-at-read failure is correctly preserved as false. The required trace gives `(physical_failure, ideal_failure, B, P) = (true, false, false, true)`. No assumptions or outcomes were altered to conceal that counterexample.

### 3.2 Probability of P and different word phases

For independent simple per-bit NHPPs within a word, common deterministic rate r(t), and a deterministic interval I, let `mu_I = integral_I r`. For each unordered pair of bits, the probability that both have at least one arrival is `(1-exp(-mu_I))^2 <= mu_I^2`. Union over pairs, intervals and words gives

`Pr(P) <= C(32,2) * sum_w sum_{I in Pi_w} (integral_I r)^2`.

If every initial, complete and final interval is at most tau, Cauchy-Schwarz gives

`Pr(P) <= W*C(32,2)*tau*integral_H r(t)^2 dt`.

This reasoning handles each word's phase separately before applying the common bound; it does not approximate phases by quadrature. Cross-word independence is unnecessary. Finite integrated rate and square-integrable r give a finite, useful expression; an infinite bound is only trivial. Event-dependent partitions, non-simple joint marks and unqualified endogenous intensities do not inherit this calculation.

The argument works for general n, with `C(n,2)`, and then specializes to n=32. Three-bit enumeration does not prove the 32-bit theorem; the proof provides that connection. Neither includes the full internal `(32,38)` code or mixed data/parity routes.

## 4. MINOR-01: distinguish past-known D from deterministic windows

REPORT §4.2 and CONTRACT correctly put an expectation around the singleton-check sum, but then remove it after dropping J while allowing D to be “deterministic or past-known.” The `B-EXPECTATION` disposition row carries the same ambiguity. Past measurability does not make D, or its all-check window count, deterministic.

For fixed potential checks c_wk, check-measurable singleton indicator J_wk and check-measurable delay upper D_wk, independent future NHPP increments justify

`Pr(B) <= 31*E[sum_wk J_wk * integral_[c_wk,min(c_wk+D_wk,H)] r(t)dt]`

`<= 31*E[integral_H K_D(t) r(t)dt]`.

The latter expectation remains if the windows are random. The observed singleton bit also depends on history, but the common per-bit rate makes the same 31-bit bound valid conditionally. A completion time observed in the future must not silently replace a predeclared/past-known upper.

For **deterministic D_wk and deterministic windows**, the expectation is unnecessary and the submitted formula is correct:

`U_B = 31*integral_H K_D(t) r(t)dt`.

Alternatively, a pointwise deterministic dominating window-count envelope `Kbar >= K_D` gives `Pr(B) <= 31*integral Kbar*r` even if the actual delay is random. It must genuinely dominate, not merely average over paths.

An elementary two-history arithmetic check illustrates the distinction without supplying any CY input: if a future event-count exposure is 0.01 or 0.4 with equal history probabilities, the unconditional occurrence probability is approximately 0.16981506. The smaller realized exposure 0.01 does not bound it; the expected exposure 0.205 does. This is an expectation-identity illustration, not a new physical counterexample or campaign.

**Minimum correction:** in CONTRACT, REPORT §4.2 and the `B-EXPECTATION` row, retain the expectation for past-known random windows, and label the expectation-free line as deterministic-window-only (or explicitly dominated by a deterministic envelope). This is a limited domain/formula correction. The executor tests all use fixed delays, no numerical physical bound is released, and the deterministic theorem is complete. No additional general random-delay derivation or broad repair cycle is required for the present **PASS_WITH_MINOR**. A realized random all-check integral is outside the accepted unconditional certificate.

## 5. Duty simplification

For `c_wk=phi_w+k*tau`, fixed phases, common deterministic upper `D<tau`, and r constant on blocks of length an integer multiple of tau, the periodically extended all-check coverage has integral W*D per period. Multiplying by the constant rate within each complete block and summing gives

`U_B <= 31*W*(D/tau)*integral_H r(t)dt`.

This is a weighted-integral identity for complete blocks, not a pointwise equality of coverage. Pre-start potential windows are absent because there is no pending start; dropping them and truncating windows at H can only decrease exposure. The reporting horizon must be a union of the stated complete rate blocks for this version of the formula. An arbitrary partial final rate block needs explicit window integration or its own bound. Uniform staggering is unnecessary.

The frozen illustrative 300-second rate blocks, tau=1 and aligned horizon satisfy the block arithmetic, giving 504.00 for both all-check and duty exposures. This does not qualify a real executor schedule or physical rate trace. For arbitrary r, average duty alone is insufficient. A maximum-gap condition suffices for the pair term, but does not limit extra checks and therefore does not by itself establish the RMW duty term.

## 6. Reproduction, provenance and export comparison

### 6.1 Exact bytes and execution history

All 15 file blob IDs in MANIFEST matched the exact target before execution. MANIFEST itself is blob `2b0e7857f06b5e7740f4966149cde0361ed0f5ff`; REPORT is `d033e4c4d4626a29c5eb0a7bfbd7e0df5e59b73e`. Git history confirms 18 linear commits from `ec6b1b3c...`, with only 16 new package files. CONTRACT, config and executor_model are unchanged from frozen mirror `ae208424274336f0bd0eb0fa923e1a974a3412bd`.

The two checker fixes were inspected as diffs, not inferred from final pass flags. `0ef88511...` moves the clean/no-write inspection before the next singleton check/write. `50317bd0...` makes the independent implementation choose the chronologically next arrival/check/commit. Both address demonstrated checker defects, without changing the model, frozen slot family or executor_model.

The saved failed run is retained: main targeted FAIL with main enumeration 4096/60/0; independent old/new violations 0/564 before the chronology fix. Those are recorded historical outcomes, not successful pre-execution checks. This review did not rerun the failed historical snapshot. The before-fix source and diffs substantiate the described causes. The asserted local commits `0cab8b63...` and `43ebefec...` and their before-execution timing were not independently time-attested here. GitHub publication was retrospective, as explicitly disclosed; Git commit order does not supply the missing temporal attestation. This limitation does not invalidate the independently checkable deterministic theorem or current frozen outputs.

### 6.2 Commands actually run

The exact target package was extracted into a fresh isolated directory; published source bytes remain available unmodified in the Git target. The following four commands completed successfully there:

```sh
python3 -m py_compile executor_model.py check_executor.py independent_check.py probability_qa.py
python3 check_executor.py --config config.json --counterexample traces/counterexample_input.json --out outputs/executor_check.json --trace-out outputs/counterexample_trace.json
python3 independent_check.py --config config.json --out outputs/independent_check.json
python3 probability_qa.py
```

RE records Python 3.13.5 / Linux x86_64 / stdlib; a kernel/libc version is not specified in the package. SR used **Python 3.12.14, Clang 22.1.3, Linux 6.18.44 x86_64, glibc 2.39**, stdlib. No claim of identical environments is made.

| Export | Actual comparison |
|---|---|
| executor_summary.json | All `checks`, `physical_slice`, `scientific_acceptance_rate_interface` values match the generated full output. Counts match 4096/60/0; `first_old_violation.marks` matches `[0,0,0,1,-1,-1]`. Full executor_check.json is not a committed file and was not treated as one. |
| counterexample_trace.json | Every JSON value matches, including all six trace rows; bytes differ only in serialization/formatting. |
| independent_check.json | Semantic and byte identity; SHA-256 `7a1d1753fe1764097f925d67700f387074e6505f8eed24811f0ad96cca9c8833`. |
| probability_qa.json | Semantic and byte identity; SHA-256 `064b3a8aa8414f576166b8f00a3448f974b8befe254b271279bfa3e0e7c9e5e9`. |

The published trace SHA-256 is `a020162533a6ae3113518c465d49d67283f9888f8354aecbd0a6b46d0e10a02f`; reproduced serialization is `2657a9a157bb0cea5d3d0cfb093dcb0717c5bde46ec47822abd867e91260e176`. This is not a scientific mismatch. All detailed targeted checks omitted from the compact summary were inspected in the generated full output. The physical slice remains `bound=null`, `status=NOT_ESTABLISHED`, and the rate acceptance interface is `EXCLUDED`.

## 7. Independent production-linked validation and its limits

The new SR checker is `docs/scientific_reviews/checks/cy62167_physical_bridge_review_03.py`. It verifies exact source bytes before loading the RE modules for comparison. Its expected result is calculated independently: visits to deterministic checks determine which clean writes are scheduled; at each query time, physical state is reconstructed from arrival parity since the latest actual committed clean image, and ideal state from parity since the latest check. Pending origin/windows, B, arrival-label partitions and sticky first passage are reconstructed from those histories. This does not copy the main/bitmask next-event selector or use their results to derive the oracle's writes/states.

The oracle matched **every returned main-executor trace field and terminal field on all 4096 frozen streams**, and separately matched the RE bitmask implementation's four indicators. There were 60 violations of the intentionally rejected old inclusion and zero violations of the repaired inclusion. The mandatory trace in the generated full export was also matched independently.

Nine additional bounded probes checked: clean/no-write; initial first passage; pending-at-H without failure; pending-at-H with a distinct-hit failure; commit exactly at H with sticky failure; same-bit clearing while still pending; final partial interval; nonuniform fixed check spacing; and bit labels including bit 31. All nine matched the complete main trace and the bitmask indicators. Thus there are **4105 full-trace comparisons and 4105 four-indicator comparisons**, plus the separate mandatory-export comparison. One preliminary SR fixture accidentally placed a hit exactly at a commit; the oracle rejected that out-of-contract fixture before comparison. It was moved to a distinct timestamp; no RE file or criterion changed.

The checker also independently enumerates occupied/not-occupied cells to recover the synthetic distinct-arrival probability, approximately 0.000590007300664386, instead of reusing the QA expression `3p^2-2p^3`. The synthetic RMW calculation is a potential-window arrival probability, not measured CW risk. The duty identity is justified analytically above; reproducing the inherited 504.00 fixture alone would not make it independent validation.

Actual own-check command:

```sh
python3 -B /workspace/scratch/24e1723b7ed9/physical-bridge-review-03/docs/scientific_reviews/checks/cy62167_physical_bridge_review_03.py /workspace/scratch/24e1723b7ed9/repo /workspace/scratch/24e1723b7ed9/physical-bridge-r3-checks.eBM6Jv/experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-02
```

Shared dependencies remain: scientific definitions, the SR-selected slots and contract, check/commit conventions, Python arithmetic and the interpretation of a clean latch. The main and RE bitmask implementations also share the next-event algorithmic structure after the fix; absence of imports alone is not independence. The parity-history oracle supplies a different production-linked path, while the proof supplies the general argument. Finite enumeration is not Monte Carlo, independent physical data, or proof of every possible input to either Python API. Acceptance is for the declared in-contract finite checks, not a general-purpose validated API accepting arbitrary delays, ties or horizons.

## 8. Maximum admissible wording and next decision

> For the declared clean-start registered data-only SEC model with deterministic per-word check partitions, no write after a clean check, and a latched clean correcting write after a singleton check completed before the next check, physical capability first passage is included in the union of a distinct-pair-arrival event and a distinct-hit pending-write event. Under independent simple per-bit NHPP arrivals with common deterministic rate r, deterministic interval lengths at most tau and deterministic correcting-window upper bounds, this gives the sufficient upper `min(1, W*C(32,2)*tau*integral_H r^2 + 31*integral_H K_D*r)`. The duty-factor form additionally requires periodic fixed phases, a common deterministic D<tau and a horizon made of aligned complete constant-rate blocks of integer-period length. The repaired event executor reproduces the required counterexample to the stronger ideal-failure inclusion and agrees with independent state reconstruction on the frozen finite family and stated boundary probes. No physical CY62167 numerical risk certificate is established by these results.

For past-known random windows, retain the expectation or use a proven deterministic dominating envelope; the expectation-free random-window reading is not accepted. A full-device extension needs its own qualified omitted-route bound. Datasheet minimum write-cycle timing is not WCET; data-only capability exceedance is not DUE/SDC/system failure; the experimental epsilon is not a numerical project requirement.

**Orchestrator may limitedly accept the local fixed-window proof/executor result and close SR-02 MAJOR-01, recording MINOR-01's scope correction.** The stated deterministic result is scientifically eligible for consideration as a bounded component; this review does not register a RES or promote the whole bridge. There is no blocking demand for new numerical or physical work to close this local repair. Numerical selected-slice/full-device results and a complete actual-CY m0/m1 witness remain NOT_ESTABLISHED. Issue #15 and the choice of the next physical evidentiary step remain with Orchestrator/PI; no such execution is authorized here.
