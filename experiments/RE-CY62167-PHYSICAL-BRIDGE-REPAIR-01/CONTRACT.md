# RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01 — pre-execution contract

**Repair handoff:** `d4918569e278289e300eee8bb0504211b23ac92b`.  
**Reviewed delivery:** `0c979c34d537c9f328858010a8df6cdeab598735`.  
**Scientific Review:** `18b78a647ac299290b5e2399b8af581e14240b88`, verdict `REVISE`.  
**Scope:** only MAJOR-01/MAJOR-02 and MINOR-01..03. No new environment model, no full Phase A/B/COSRAD rerun, no new controller, no RES-004, no re-proof of D3.

## Frozen question

Can the first physical-bridge delivery be repaired so that, on the already selected CY62167 slice, (a) a positive model is genuinely compatible with the same information contract and with conditional-write execution, and (b) a second compatible model gives the opposite decision; or, if not, what exact concrete input prevents that claim?

A completed full-CY witness requires both sides. An abstract extension theorem alone is not called a completed witness.

## Information set I

`I` contains all information used by the claim, not only the data projection:

1. AN88889 device facts: internal Hamming SEC `(32,38)`, 32 data + 6 parity cells; 16-bit interleaving; corrected read output does not repair the stored word automatically.
2. Datasheet interface facts: 45-ns speed grade; `tRC>=45 ns`, `tAA<=45 ns`, `tWC>=45 ns`; ERR/read timing; automatic write-back unsupported.
3. Empirical ordinary-row `(x,y)->A`; `A->W/parity` remains unknown.
4. Registered-cluster semantics: stored files are post-processed clusters rather than identified physical parents; split/merge/censoring remain possible; parity cells are absent from the registered data interface; relevant cluster campaigns used internal ECC disabled.
5. Frozen proton multiplicity/geometry summaries and `sigma_bit(E)` identity. Absolute file/segment `sigma_k(E)` is unavailable because aligned fluence/run linkage is not established.
6. Frozen registered data-only DREG mission model and selected-window output from `RE-CY62167-ECC-RISK-BRIDGE-01`; these are model inputs, not newly revalidated physical laws.
7. 55/210 W families only as restricted diagnostics, not complete physical W families.
8. Selected-window clean initial data-word state and first-passage semantics.

No unrecorded physical rate, parity sensitivity, parent linkage or W fact may be added merely to make a witness pass.

## Compatibility contract

A complete compatible model must specify: parent-event time/mark law over full `(32,38)` words; fixed internal W/parity placement satisfying known architecture facts; observation operator including allowed censor/split/merge behavior; initial physical state; decoder/service/conditional-write semantics; a law for every hidden population that may contribute to `E_cap`; and the frozen registered data-process projection when used by the selected slice.

Compatibility means the induced law for every element included in `I` is the same as the frozen law/data used by the claim and no source-supported device constraint is violated. Same data-cell projection alone is insufficient.

A pair `m0,m1` is an actual non-identifiability witness only if both satisfy this same contract. Otherwise the repair returns only a conditional extension theorem plus the exact missing input.

## Frozen slice

Do not change:

- `t0=2026-01-19T04:00:00+00:00`;
- `H=24 h`;
- shielding `10 mm Al`;
- `main_loglog`, `central_mean`, `DREG`;
- `tau=1 s`;
- `epsilon_analysis=1e-3` (analysis line only);
- historical `U_historical=0.0003098119451681036`, from `risk_curves.csv` blob `cc5067f2c5eeba7b552839a4532fee9292b64398`.

No environment transport recalculation may be substituted.

## Conditional-write execution contract

1. A word is read/ECC-checked at time `r`.
2. If clean, no correcting write occurs; arrivals after `r` remain in both physical and ideal-at-check processes.
3. If singleton, the ideal-at-check comparator clears at `r`, whereas the physical stored word remains erroneous until correcting write completion `w=r+Delta`.
4. First passage during `(r,w]` is charged to explicit `delta_exec(Delta)`.
5. Later writeback cannot erase historical first passage.
6. Parity/unknown-W/hidden-parent routes remain in physical coverage uncertainty unless separately bounded.

`tWC>=45 ns` is a minimum legal write-cycle time, not a WCET. Therefore no numeric `Delta` is declared proven; the repair may return a conditional curve or maximum admissible `Delta` only.

## Preferred one-sided registered bound

For independent simple per-bit registered arrivals with frozen per-bit rate `r(t)`, a phase-free sufficient pair bound is

`U_pair = W * C(32,2) * tau * integral_H r(t)^2 dt`,

using `(integral_I r)^2 <= |I| integral_I r^2 <= tau integral_I r^2` on every inter-check interval.

A conservative RMW mismatch bound is

`delta_exec(Delta) <= 31 * W * (Delta/tau) * integral_H r(t) dt + boundary_term`,

when each word is checked once per `tau` and every read is pessimistically treated as a singleton. The exact schedule must justify `boundary_term=0` or retain it explicitly.

Then `U_reg_CW(Delta) <= min(1,U_pair+delta_exec(Delta))` for the registered data-only process under these assumptions.

If the exact frozen `r(t)` trace or source-equivalent frozen summaries `integral_r` and `integral_r2` cannot be recovered from controlled saved inputs, no numerical `U_reg_CW` is claimed and the exact missing artifact is reported rather than reconstructed from `U_historical`.

## Fixed witness test

1. Can a complete positive `m0` be specified under the same `I`, including full-word hidden/parity law, with a one-sided upper below `epsilon`?
2. Can `m1` be produced by an observation-invariant admissible modification of that same model, without changing any element of `I`, such that a D3 component gives the opposite decision?
3. If either fails, identify the concrete missing input and show why its two possible values cross the decision.

Allowed conditional theorem: **if** the admissible family is closed under an unobserved parity-mark extension that leaves the full observation law in `I` unchanged, adding a D3 extension can change the all-policy lower bound without changing that observation law. This is not evidence that actual CY62167 satisfies the closure antecedent.

## Predeclared checks

- executable conditional-write traces: clean/no-write, singleton/check/write, distinct hit inside RMW, same-bit cancellation, first-passage persistence;
- independent arithmetic direction check for `U_pair`/`delta_exec` on a small explicit rate model;
- exact frozen-slice and historical-risk identity;
- exact hash/provenance of any frozen rate input used; substitute traces forbidden;
- compatibility ledger for proposed `m0/m1`: every row of `I` marked `SAME | NOT_APPLICABLE | VIOLATED | UNKNOWN`;
- machine decision status exactly one of `SUFFICIENT | INSUFFICIENT | NOT_ESTABLISHED`, with qualifications separate.

Existing D3 329,004-case result is reused, not rerun as new evidence.

## Completion

**Full repair:** complete compatible m0/m1 + positive conditional-write upper on same slice + opposite decisions + no material unresolved compatibility row.

**Limited repair:** preserve reviewed D3/conditional lemmas, qualify or precisely block MAJOR-02, withdraw stronger old witness wording, and identify the concrete missing fact/artifact.

No Scientific Review PASS or RES is assigned.