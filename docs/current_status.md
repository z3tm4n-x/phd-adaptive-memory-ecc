# Current Status

**Updated:** 2026-08-31

## Current phase

The bounded EXP-001 validation repair has passed Scientific Reviewer re-review.
The corrective and scientific-review gates are closed. A narrowly scoped first
own-result candidate is prepared for PI wording approval but is not yet a
registered `RES-xxx`. The bounded Chen/IHP/Potsdam
Evidence Audit is accepted and now constrains the control-method target. The
Russian normative baseline remains accepted with explicit unresolved interfaces.

The controlling [DEC-002](decisions/DEC-002-integrated-evidence-to-adaptive-control-roadmap.md)
architecture is unchanged:

`radiation-test evidence → identifiable device-error representation → W/ECC organization → ECC-level reliability → online risk assessment → adaptive restoration decision`.

Adaptive restoration control remains the final/core dissertation layer.

## Active scientific gate

[EXP-001 Scientific Re-review 02](scientific_reviews/EXP-001_SCIENTIFIC_REREVIEW_02.md)
is accepted with recommendation `PASS`. It confirms that `MAJOR-01` and
`MINOR-01…04` are closed, no repair-induced scientific regression exists and no
new issue was found. The PI accepts this disposition and considers the EXP-001
corrective gate closed.

The active gate is PI wording approval of
[`DRAFT-RES-001`](result_candidates/DRAFT-RES-001-exp001-four-word-identified-set.md).
The candidate preserves the maximum wording and complete fourteen-condition
validity domain accepted by the Reviewer. It is not a permanent result and may
not be cited as `RES-001` before explicit PI approval.

PI accepted the scientific content and returned `REVISE — wording only`. The
candidate now refers specifically to one-event per-word marginal impact
probabilities under mandatory two-distinct-word event cardinality and separates
the no-feasible-action outcome at experimental `epsilon=0.15` from the selected-
period differences at `0.25` and `0.35`. No calculation or review gate was
reopened; final PI `ACCEPT` remains pending.

No new experiment, target-device extension, retroactive `HYP-xxx` or permanent
result registration is authorized before that approval.

## Active Research Questions

- RQ-001 — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`; DEC-001 unchanged.
- RQ-002 — `OPEN / EXP-001 BOUNDED RESULT CANDIDATE`.
- RQ-003 — `OPEN / ACTIVE NEXT INTERFACE`; owns parameterized ECC capability,
  state and decoder-outcome semantics and must keep `E_cap` distinct from
  DUE/SDC/miscorrection/system-visible outcomes.
- RQ-004 — `OPEN / QUEUED NEXT`; must distinguish external exposure information
  from internal protected-memory state/history and propagate observation
  uncertainty to the risk interface.
- RQ-005 — `OPEN / QUEUED NEXT`; retains the measurable multi-component resource
  vector without premature scalarization.
- RQ-006 — `OPEN / EXP-001 BOUNDED RESULT CANDIDATE`; owns `W`, topology, joint post-`W`
  impact and reduction-sufficiency/bound conditions.

The future integrated adaptive-control question is prepared as a candidate in
[`research_backlog.md`](research_backlog.md), but is not permanently registered.
It requires explicit PI acceptance of its final wording/ID before control-method
development; that separate future approval does not alter the current
`DRAFT-RES-001` wording gate.

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

These are accepted review findings and form the basis of a bounded result
candidate, not yet `RES-xxx`. They do not bound physical SRAM topology or
establish universal insufficiency of marginal models.

### Validation-repair disposition

The original 768,000 L0/L1 comparisons remain correctly labelled as
outcome/final-signature comparisons. The repair adds a bounded, independent
full-trace validation layer rather than relabelling the production run.
Scientific Review 02 confirms closure of the demonstrated shared-path weakness
without changing configurations, scientific outputs or the EXP-001 question.
EXP-001 is now `SCIENTIFIC REVIEW PASS / PROMOTION CANDIDATE`.

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
EXP-001 and do not authorize a broad literature cycle. Before the next
quantitative experiment, the Orchestrator must define the smallest bounded
full-text pass needed to turn these lines into controlled comparison points.

## Updated scientific roadmap

1. **Approve or revise the bounded result candidate.** PI reviews the exact
   statement and fourteen-condition validity domain; no permanent `RES-001`
   exists before acceptance.
2. **Control the minimum prior-art boundary.** After result approval and before
   the next quantitative experiment, convert only the named domestic lines that
   can change the next method/gate into bounded full-text comparison points.
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

## Prepared next quantitative gate — not active

No new `EXP` may start before PI approval of the bounded result candidate. The
subsequent own quantitative stage must answer more than “dependence can matter.”
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
simply create another synthetic pair with different `F_A`. Exact gate wording,
RQ/interface dependencies and the bounded prior-art handoff will be proposed
after PI disposition of the result candidate.

## Genuine blockers and PI inputs

The only current blocking PI decision is acceptance, revision or rejection of
the bounded `DRAFT-RES-001` wording.

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
- EXP-001 is implemented, independently validated within the repair scope and
  has `Scientific Review 02: PASS`.
- `DRAFT-RES-001` awaits PI wording approval and is not a permanent result.
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
