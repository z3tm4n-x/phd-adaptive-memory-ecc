# Current Status

**Updated:** 2026-08-31

## Current phase

Obtain the bounded Scientific Reviewer re-review of the accepted EXP-001
validation repair, then promote or reject a narrowly scoped first own result.
The bounded Chen/IHP/Potsdam
Evidence Audit is accepted and now constrains the control-method target. The
Russian normative baseline remains accepted with explicit unresolved interfaces.

The controlling [DEC-002](decisions/DEC-002-integrated-evidence-to-adaptive-control-roadmap.md)
architecture is unchanged:

`radiation-test evidence → identifiable device-error representation → W/ECC organization → ECC-level reliability → online risk assessment → adaptive restoration decision`.

Adaptive restoration control remains the final/core dissertation layer.

## Active scientific gate

[EXP-001 Scientific Review 01](scientific_reviews/EXP-001_SCIENTIFIC_REVIEW_01.md)
is an accepted review record with recommendation `REVISE`, no `CRITICAL` issue,
one `MAJOR` and four `MINOR` issues.

Research Engineer repair commit `072b70adabb9827ee59c94b2b3d5cf044b25cdf9`
has passed Orchestrator disposition:

1. the test-only oracle is independent of production mapping/conversion and
   transition helpers;
2. 267 physical streams produce 534 separate full-trace L0/L1-to-oracle
   comparisons across both declared `W`, clean/non-clean starts, toggle and
   `set_error` semantics;
3. the exhaustive 8x8 single-cell mapping and mutation/sentinel checks pass;
4. all four MINOR corrections are implemented and machine-recorded;
5. 32/32 tests and `compileall` pass;
6. an independent fixed rerun satisfies every precision/precondition check and
   reproduces all seven scientific files plus `analytical-validation.json`
   byte-for-byte.

The remaining gate is a bounded Scientific Reviewer re-review of finding closure
and regression only. `PASS` or `PASS_WITH_MINOR` makes a bounded `RES-001`
admissible; it does not create the result automatically.

No target-device extension, new literature cycle, retroactive `HYP-xxx` or
redesign of EXP-001 is part of this gate.

## Active Research Questions

- RQ-001 — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`; DEC-001 unchanged.
- RQ-002 — `OPEN / EXP-001 SCIENTIFIC RE-REVIEW`.
- RQ-003 — `OPEN / ACTIVE NEXT INTERFACE`; owns parameterized ECC capability,
  state and decoder-outcome semantics and must keep `E_cap` distinct from
  DUE/SDC/miscorrection/system-visible outcomes.
- RQ-004 — `OPEN / QUEUED NEXT`; must distinguish external exposure information
  from internal protected-memory state/history and propagate observation
  uncertainty to the risk interface.
- RQ-005 — `OPEN / QUEUED NEXT`; retains the measurable multi-component resource
  vector without premature scalarization.
- RQ-006 — `OPEN / EXP-001 SCIENTIFIC RE-REVIEW`; owns `W`, topology, joint post-`W`
  impact and reduction-sufficiency/bound conditions.

The future integrated adaptive-control question is prepared as a candidate in
[`research_backlog.md`](research_backlog.md), but is not permanently registered.
It requires explicit PI acceptance of its final wording/ID before control-method
development; that approval does not block the current re-review or RQ-003 work.

## EXP-001 disposition

### Accepted findings within the reviewed model class

Scientific Reviewer independently accepted:

- the pair-probability parameterization;
- `1/6 <= q <= 1/2`, with J-B and J-A attaining the two endpoints;
- `S(q,m)=exp(-m)[1+m+q m^2/2]` and the aligned reporting-window `F_A`;
- the identified-set interpretation within the complete fourteen-condition
  validity domain in review Section 7.4;
- the separation of representation/dependence uncertainty, Monte Carlo
  estimation uncertainty and CI-decision conservatism;
- exact endpoint decision differences at experimental `epsilon=0.15`, `0.25`
  and `0.35`, but not at `epsilon=0.55`.

These are accepted review findings, not yet `RES-xxx`. They do not bound physical
SRAM topology or establish universal insufficiency of marginal models.

### Validation-repair disposition

The original 768,000 L0/L1 comparisons remain correctly labelled as
outcome/final-signature comparisons. The accepted repair adds a bounded,
independent full-trace validation layer rather than relabelling the production
run. It closes the demonstrated shared-path validation weakness at Orchestrator
level without changing configurations, scientific outputs or the EXP-001
question. Scientific Review 01 remains `REVISE` until the Reviewer confirms
closure.

## Chen/IHP/Potsdam control-prior-art disposition

[CONTROL-PRIOR-ART Evidence Audit 01](evidence_audits/CONTROL-PRIOR-ART_EVIDENCE_AUDIT_01.md)
is `ACCEPTED WITH BOUNDED WORDING CORRECTION`.

- Candidates 1, 2, 4, 5, 6, 7, 8a and 8b are accepted only within the controlled
  S3/S4/S5 family.
- Candidate 3 is accepted only after correcting the claim: S5 newly specifies
  the six-hour input window and makes the already-present next-hour target
  explicit; it does not first add the `t+1` target.
- S5 is the strongest single architecture comparator; S3 remains necessary for
  feature provenance and S4 for the separate reactive HSIAO branch.
- No additional Chen-family Paper Card is required now.
- No permanent `CLM`/`EVD`, novelty or non-novelty conclusion is created.

The controlled family is genuine close prior art for online fault-count/rate
input, next-hour point prediction or reactive assessment, and adaptive
wash/scrub-frequency selection. Generic adaptive scrubbing, ML-to-frequency,
online fault counts and scrub-count reduction cannot be project novelty claims.

The accepted bounded differences become method-design axes only if the project
makes them operational and demonstrates a quantitative reliability, uncertainty,
decision, resource or implementation consequence.

## Russian normative baseline

[NORMATIVE-BASELINE-01](normative_baseline/NORMATIVE-BASELINE-01_extraction_matrix.md)
remains `ACCEPTED WITH LIMITATION / PARTIAL — NAMED INPUT NEEDED`.

Accepted practical chain:

`diagnostic observations → PMI/software classification → classified ORE counts → cross sections → sensitivity representation → environment convolution → scalar rate/probability`.

No normative deficiency or automatic equivalence to `W`, `E_cap` or `F_A` is
inferred. The STO controlled-edition status remains `AMBIGUOUS`.

## Additional domestic prior-art signals

PI-provided signals concerning the Meshchanov/Lushnikov/Krasnikov, Podzolko,
Boruzdina/Ulanova/Chumakov and Zebrev/Galimov lines are recorded in
[`research_backlog.md`](research_backlog.md) as `UNVERIFIED`. They constrain
future novelty-risk verification but are not accepted evidence, do not change
EXP-001 and do not authorize a broad literature cycle.

## Updated scientific roadmap

1. **Close EXP-001 review.** Obtain the bounded Scientific Reviewer re-review of
   the accepted repair and regression evidence.
2. **Promote only the bounded result.** If the re-review passes, create a
   candidate `RES-001` using the maximum admissible wording and complete validity
   domain from Scientific Review 01; no retroactive hypothesis.
3. **Activate RQ-003.** Define the minimum parameterized ECC state/capability and
   decoder-outcome contract consumed by reliability and observation layers.
4. **Converge RQ-004 and RQ-005.** Bound at least one internal and one external
   observation channel with uncertainty/latency semantics, and a measurable
   resource vector containing scrub activity plus nonredundant service/hardware
   components.
5. **Generalize the own method.** Replace the single extremal discriminator with
   an information-state/model-set formulation
   `I -> M(I) -> F_A set/bound -> admissible actions -> T_scrub -> resource cost`,
   and quantify the control-resource price of information deficit.
6. **Move to a physically defensible domain.** Use plausible event/W classes and
   observable test outputs to determine effect magnitude, controlled error or a
   safe-reduction domain, then connect the result to adaptive `T_scrub` selection
   and resource cost.
7. **Only then broaden claims.** Run the separate classical
   inspection/maintenance prior-art pass before a literature-level integrated
   control novelty claim, not before the next bounded model work.

## Next quantitative gate

The next own quantitative stage must answer more than “dependence can matter.”
Its gate is to define, for retained information `I`, an admissible model set and
the induced interval/bound for `F_A`, then determine for every candidate
`T_scrub`:

- exact/model feasibility at a specified model;
- estimated feasibility under a declared statistical rule;
- robust feasibility over representation/model/observation uncertainty;
- conditions under which the admissible or selected action is invariant;
- decision and resource consequences over a physically defensible domain.

The next experiment or derivation must be preregistered before execution and may
use a hypothesis or an explicit decision/falsification criterion. It must not
simply create another synthetic pair with different `F_A`.

## Genuine blockers and PI inputs

No new PI decision is required for the EXP-001 re-review or the RQ-003 protocol
revision/mapping.

Before target-like calibration, useful but non-blocking material remains:

- controlled-edition or registry evidence for STO 04.01.0005–2022;
- one representative/de-identified SRAM private PMI and diagnostic/software log
  schema;
- target-like memory organization/interleaving information;
- applicable current normative documents named in the accepted extraction.

Permanent registration of the prepared integrated adaptive-control RQ will
require explicit PI acceptance of its exact wording and ID. A future genuine
branch decision is required only if evidence forces a choice between incompatible
observable channels, ECC semantics or target hardware domains.

## Active hypotheses and results

- No `HYP-xxx` is registered; none is created retroactively for EXP-001.
- EXP-001 is implemented and its validation repair is Orchestrator-accepted, but
  Scientific Review 01 remains `REVISE` pending bounded re-review.
- No `RES-xxx` is registered.

## Constraints

- Do not reopen RQ-001 or revise DEC-001 without a concrete contradiction.
- Do not identify `E_cap` with DUE/SDC/miscorrection/system failure.
- Do not assign a numerical reliability requirement without traceable provenance.
- Do not generalize EXP-001 to physical SRAM or universal marginal-model
  insufficiency.
- Do not infer normative deficiency or Chen-family novelty/non-novelty.
- Do not let representation/reliability work replace adaptive control as the
  dissertation core.
