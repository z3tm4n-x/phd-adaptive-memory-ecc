# Stage A — Scientific Review 01

Task: `STAGE-A-SCIENTIFIC-REVIEW-01`

Exact reviewed/base commit: `c41feab9a8210b4f2213104784bb47990ae7f36f`

Implementation parent / accepted specification: `c9ec2197f98207fc43938331542bbe00c8ae5a82`

Prior semantic review, read from its sibling history: `e11e1b1db1ca26b79291dad59f818167f2441620`, `docs/scientific_reviews/CY62167_SEMANTICS_REPAIR_REVIEW_02.md`

Delivery branch: `reviewer/stage-a-scientific-review-01`

Related: RQ-002/003/004/005/006/007. Reviewer: independent Scientific Reviewer. Date: 2026-09-08.

**Recommendation: REVISE — bounded reproduction/provenance correction, not rejection of the central mathematical result.**

The derivation and reviewed implementation support zero Precomputed-to-Causal minimax pass-count gap together with strictly positive selected-policy actuation savings on LL/LH/HL in the six certified cases. Independent checks found no conflicting certificate or policy result. However the required frozen-input reproduction fails on the exact advertised Git blob: the configuration contains the SHA-256 of a CRLF serialization, whereas the blob and `git show` output use LF. The manuscript-style reproduction statement about a newly written run manifest is also unsupported by the script. These must be corrected before accepting the package as reproducible.

No production matrix, transport, mapping, COSRAD or Monte Carlo run was performed. No Stage B, physical calibration, angular conclusion or new research ID is authorized or created.

## 1. Scope and evidence inspected

Read the global operating rules, reviewer role and HANDOFF_CONTRACTS at the exact base; the accepted `docs/research_gates/STAGE-A-PREEXECUTION-01.md`; the complete 19-file implementation package, including decoded compressed contents; and the prior semantic review at its exact sibling commit. The remaining ERR issue from that review is contained: Stage A uses R2-U and its own pass accounting, not ERR `period_feasible`.

GitHub comparison with the implementation parent reports one commit ahead, zero behind and exactly 19 added files, all under `experiments/STAGE-A-IMPLEMENTATION-01/`. No existing specification, result or implementation was modified by that delivery. The specification's historical NOT EXECUTED heading is an execution-authorization record, not evidence against the later implementation delivery.

Evidence categories in this report are distinct: checked source/history and file identities; reviewer mathematical inference; declared modelling assumptions; independent production-linked checks; shared-code/output consistency checks; and remaining unknowns. Passing tests or reproducing frozen values alone is not scientific validation.

## 2. Disposition of candidate claims

| Candidate | Disposition | Required qualification |
|---|---|---|
| 1. Piecewise/sequential-reset certificate, including t=300 | **SUPPORTED for the declared model** | Pair-arrival union bound with actual credited word-reset intervals, clean start and final tails. Reviewer explicit timestamp integration agrees exactly with production `pair()`. It is not exact toggle risk or a hardware trace. |
| 2. Optimal Precomputed and Causal worst-case costs coincide | **SUPPORTED by proof** | Required dominating HH scenario, common finite action set and model information, scenario-independent pass costs, declared comparator classes. Both classes are either nonempty together or empty together; a finite zero gap is reported only when certified policies exist. |
| 3. Selected Causal policies save on LL/LH/HL without increasing HH | **SUPPORTED in all six certified cases** | Conditional computed actuation savings under the prescribed complete selection rule. Not a property of every minimax optimizer, a frequency-weighted benefit, net information value or an operational controller result. |
| 4. Finite ambiguous-rho family is uncertified | **SUPPORTED on the accepted grid** | Required rho=0.01/HH witnesses exhaust the sufficient budget at each shield even for the largest epsilon. No physical infeasibility, exact-risk exclusion or zero-information-value claim follows. |

These are scientifically supported own-result candidates, not accepted RES/CLM. The delivery recommendation remains REVISE because of the concrete reproduction defect in §7.

## 3. Derivation and transition semantics

### Rate allocation and first passage

`rho` allocates erroneous-bit arrival intensity, not instantaneous erroneous occupancy and not parent-event probability. Independent residual singleton and two-bit same-word parent streams have rates `(1-rho)b(t)` and `rho*b(t)/2`; their bit-intensity sum is exactly b(t). Their total parent rate is `(1-rho/2)b(t)`, so equating rho with a fraction of parents would be wrong. The implementation does not make that substitution or recount direct bits as residual singletons.

For the declared mark law, uniform singleton thinning yields independent bit-specific nonhomogeneous Poisson processes conditional on the exogenous scenario. Within one credited-reset interval J, any residual first passage requires arrivals on at least two distinct bits. For a pair the probability is `(1-exp(-x_J))^2 <= x_J^2`, where `x_J=integral_J (1-rho)b(t)/N dt`. This is a necessary-arrival argument: later cancellation cannot remove a recorded first passage, and multiple hits on one bit alone cannot satisfy the distinct-bit event.

The absorbing-direct surrogate follows the same residual transitions and credited reset schedule as the corresponding toggle model until the first direct parent, at which time it records failure. The pathwise first-passage inclusion gives `F_toggle <= F_surrogate`. Union-bounding direct arrival probability by its integrated intensity, and residual failure by the word/pair/interval sum, gives

`F_toggle <= F_surrogate <= Q = min(1, Lambda_D + choose(32,2) sum_w sum_J x_J^2)`.

Stage A does not use the independent-thinning product survival as its certificate. Failure of this upper certificate does not reverse either inequality and cannot establish physical infeasibility. Direct pruning uses strict `Lambda_D > epsilon`; equality is labelled separately, not discarded by a strict-exhaustion test. All accepted epsilon values are below one, so clipping at one does not undermine that pruning rule.

### Sequential service, initial/final intervals and the rate change

For pass end e and word w, the credited reset is `e-P+(w+1)P/Nw = e-a_w`, with `a_w=P(Nw-w-1)/Nw`. Passes end at successive multiples of tau within each block; tau divides 300 and is at least P. There is no overlapping pass or pass that must be started using the next block's level before that level is observed. The 300 s change is not an array-wide reset: except for the last word, the previous credited reset is `300-a_w` and the next is `300+tau2-a_w`.

Explicit interval integration therefore gives initial exposure `r1(tau1-a_w)`, first-block full intervals, crossing exposure `r1*a_w+r2*(tau2-a_w)`, second-block full intervals and final exposure `r2*a_w`. For the last word a_w=0, the boundary reset really does occur at 300 and the final tail has zero length. The code handles that case through the same sum, without inserting a reset for other words. A failure before the final reset remains a first-passage failure.

The credited service is an explicit abstraction. Its physical use assumes that the last service of a four-address group actually leaves the surviving word restored and that service does not itself introduce an unmodelled error. Earlier complete corrections need not be credited in the pair certificate: after each credited clean endpoint, a failure still requires two distinct residual-bit arrivals in the enclosing credited interval. This justifies the weaker arrival-count bound; it does **not** assert a general pathwise monotonic ordering between toggle processes with earlier versus later resets. No exact manufacturer trace or proprietary grouping is inferred.

The analytic sums `A1=P(Nw-1)/2` and `A2=P^2(Nw-1)(2Nw-1)/(6Nw)` and the production phase formula agree with independent timestamp integration. At constant rate and equal tau, the finite-phase accumulation sum before the bit-pair multiplier is

`r^2 [Nw*T*tau - 2*tau*A1 + 2*A2]`.

Thus equality with the old stationary `beta*tau*T*nu_C^2` is the collapsed-phase P=0 limit, not an assertion of equality at the nonzero R2-U pass duration. The derivation states this distinction correctly. The finite-phase term is no larger here because each a_w is below tau.

### Exogenous-information conditioning

The full scenario is conditioned on for analysis, not revealed to the controller early. Under each scenario, the policy's chosen actions are deterministic functions of exogenous levels at 0 and 300. The Poisson streams retain their prescribed deterministic intensities and the same reset-interval proof applies. `LL/LH` share the first-L action and `HL/HH` share the first-H action. No code input supplies future event times, error states or the second level at t=0. A future policy observing internal event counts/state would need a separate argument; it does not inherit this conditioning proof automatically.

## 4. Complete policy class and selection proof

`fixed()` enumerates all 12 diagonal policies; `pre()` enumerates all 144 common pairs. `roots()` enumerates all pairs of first-L/first-H actions. For each root it stores the complete list of feasible second actions for each of four leaves. Within this two-decision deterministic class, past action is already determined by the first-level node, so this representation loses no permitted history dependence. A root is retained only when every required leaf has at least one feasible second action. All four paths remain in each class's constraints.

For a fixed root, second actions affect only their own leaves. Increasing a second action within that leaf's feasible set strictly reduces `300/tau2`, since all accepted actions divide 300 and have distinct pass counts. Selecting `max(A[path])` therefore componentwise minimizes all four path costs for that root. Any smaller feasible choice is worse either in the primary worst-case cost or in the secondary pathwise lexicographic cost vector. It cannot become optimal through the tertiary period tie-break. This establishes the pruning used by `causal()` for the **complete** selection order; it does not rely on a claim that every larger period is feasible.

`key()` then implements: minimum worst cost; minimum `(LL,LH,HL,HH)` cost vector; maximum realized periods in path/time order. Fixed and Precomputed embed constructively in the Causal class. Stored feasible-root masks represent all Cartesian products of their leaf choices, even though only each root's dominating leaf choices need be evaluated for selection. Stored tree counts are the sums of those products, not just root counts.

### HH minimax equality, including empty cases

For the same action pair and fixed rho, every exposure is a nonnegative linear function of the two nonnegative levels. Squaring and summing, and adding the direct term, preserves componentwise level monotonicity. HH therefore dominates the certificate for that pair. This is certificate monotonicity, not a theorem about exact toggle-risk monotonicity.

For any certified causal policy pi, apply its HH action pair precomputed to all paths. HH dominance makes that precomputed policy certified. Its scenario-independent pass cost equals `cost_HH(pi)` and is at most `max_path cost_path(pi)`. Hence `opt_Precomputed <= opt_Causal`. Class inclusion gives the opposite inequality. Both inequalities prove equality whenever a feasible policy exists. The same construction implies Causal nonempty iff Precomputed nonempty; if both are empty there is no finite cost gap to subtract, and specifically no information value of zero to report.

No monotonicity in rho between the three selected values is needed. For an ambiguous-rho policy the HH construction would have to satisfy every member of the same family. Here direct-budget witnesses already preclude a passing family, so an ambiguous-rho policy optimizer is not reached. The generic code's NOT-EXECUTED fallback outside that pruned situation is not a general robust-rho solver and is not accepted as one.

For the accumulation-limited empty known-rho cases, algebra also confirms the minimum on U. The phase sum is affine in tau1 and tau2, with coefficients `r1^2(Nw*B-2*A1)` and `r2^2(Nw*B-2*A1)+2*r1*r2*A1`, respectively; both are nonnegative since B=300 exceeds P. Therefore failure of the HH certificate at `(0.2,0.2)` implies failure of all action pairs under this certificate. It does not imply failure at untested periods or exact physical risk above epsilon.

## 5. Numerical and pathwise conclusions

The following vectors were verified against decoded selected rows, selected trees and component-gap tables; costs were independently ordered over the encoded feasible candidates without invoking production `search()`.

| d, rho, epsilon | Fixed worst passes | Precomputed passes on each path | Causal passes (LL,LH,HL,HH) | Precomputed minus Causal |
|---|---:|---:|---|---|
| 3 mm, 0, .01 | 3000 | 2100 | (2,601,601,2100) | (2098,1499,1499,0) |
| 3 mm, 0, .1 | 300 | 210 | (2,61,61,210) | (208,149,149,0) |
| 5 mm, 0, .001 | 1200 | 900 | (2,301,301,900) | (898,599,599,0) |
| 5 mm, 0, .01 | 120 | 90 | (2,31,31,90) | (88,59,59,0) |
| 5 mm, 0, .1 | 10 | 10 | (2,3,6,10) | (8,7,4,0) |
| 5 mm, .0001, .1 | 20 | 20 | (2,4,6,20) | (18,16,14,0) |

Every pass contributes exactly 2^21 reads, 2^21 writes and .18874368 s occupied time under the fixed R2-U service model. Thus pass savings imply the same componentwise ordering in all three actuation quantities. There is no inferred workload latency, energy, acquisition/controller cost or expected mission benefit. No scenario probabilities were introduced.

The first four Fixed-to-Precomputed gains are available without observing the environment: they arise from enlarging the action class to two predetermined periods on the discrete grid and the finite-window service certificate. They must not be attributed to current-information adaptation. In contrast, changing actions across realized paths is specific to the Causal class.

The prescribed secondary rule matters conceptually: an optimal Precomputed schedule is itself a minimax-optimal Causal policy and saves nothing pathwise. Therefore positive savings are not forced for **every** minimax optimizer. The selected cost vector is fixed by the secondary lexicographic objective; the tertiary period tie-break cannot change an already fixed cost vector. Five Precomputed cases have multiple minimum-cost pairs (counts 2,2,2,2,1,3 in table order), so action differences can depend on period tie-breaking without affecting pass savings. As a bounded check on the stored feasible-root representation, all 24 alternative path-priority orders gave the same selected cost vectors in these six cases. This is an artifact-based sensitivity check, not a new adopted rule or a general invariance theorem.

The ambiguous family includes rho=.01, whose HH integrated direct term exceeds .1 at every shield; this is a sufficient-budget witness for all accepted epsilon values. Nothing requires dropping that member, changing rho post hoc, or erasing the separate known-rho results. Zero minimax gap is reported for the six nonempty comparisons, not for the empty ambiguous family.

## 6. Independent validation and packaging audit

### Checks actually performed

Sources were fetched at the exact commit into a fresh `mktemp -d` directory, `/workspace/scratch/24e1723b7ed9/stage-review.Jmez7e`. The published reproduction helper and its fixed-directory deletion were not executed. Reviewer environment: Python 3.12.13, standard library only. The original execution environment remains the separately recorded Python 3.13.5/Linux environment; it is not replaced by the reviewer environment.

1. Read-only Git comparison and blob-identity checks; full local input byte SHA-256/SHA-1 computation; CRLF/LF diagnostic performed in memory only. Called production `frozen()` directly on the exact-identity local file: it raised the predicted SHA mismatch, without entering the production pipeline.
2. Independent CSV filtering and exact-Fraction order statistics: 16,992 records, 16,971 paired-valid finite nonnegative rows; all six L/H values and all six timestamps match config/input_manifest. Odd row count means one median observation, not an averaged pair. Upstream `rate_pipeline.py` at the frozen commit confirms N_BITS=16,777,216 and full-array scaling; no rescaling is required.
3. Production-linked explicit reset integration: 270 exact comparisons, using Nw in {1,3,4,5,7,8}, five rate pairs (rising, falling, stationary, zero-first and zero-second), three period pairs, and only the three declared rho values. Small diagnostic windows use B=1/T=2, the declared P, and n=32/N=32*Nw. These are validation fixtures, not replacements for the frozen production configuration. All comparisons equal production `pair()` exactly. Boundary cases include the final word reset exactly at the level change and horizon, and tau=B with no interior intervals. Twelve additional production-linked P=0 stationary checks, one per accepted action, also agree exactly.
4. Decoded both `.gz.b64` artifacts without running production. Verified 72 selected rows, six selected case trees, 432 encoded causal roots, 96 case-count rows and 60 component-gap rows. Verified mask tree-count products, agreement of encoded set counts with the CSV, selected winners under an independently written ordering function, shared prefixes, selected actions/risks/resources against tree/CSV data and the production certificate, and all gap arithmetic. This validates artifact linkage and selection over the stored feasible sets; it is not an independently regenerated exhaustive feasible matrix.
5. Checked all 36 direct-audit rows against exact production algebra, 144 action-pair resource identities, and the three rho=0/HH minimum certificates. These are focused algebra/consistency checks, not an invocation of `main()`, `search()`, the complete boundary audit or a matrix rerun. Checked all 24 path-priority permutations on encoded candidates only; no new scientific input or scenario weight was used.

The consolidated local check command was `python -B reviewer_check.py`, exit 0. Its source SHA-256 was `4586fd35d3721ca065ce815943ba9abfcedd6a625cb58cafad0b4c6dd63b5537`. Separate `python -B -` standard-library snippets performed the byte/newline diagnostic, encoded-candidate tie-order audit and final direct/resource checks. No full claimed production reproduction is asserted.

The decisive independent interval algorithm, as used in the check script, constructs timestamps rather than copying the production phase polynomial:

```python
def explicit(model,b1,b2,rho,t1,t2):
 B=model['B'];T=model['T'];P=model['P'];nw=model['nw'];z=R(0)
 for w in range(nw):
  resets={R(0),T}
  for origin,tau in [(R(0),t1),(B,t2)]:
   for k in range(1,int(B/tau)+1):
    pass_start=origin+k*tau-P
    resets.add(pass_start+R(w+1,nw)*P)
  times=sorted(resets)
  for left,right in zip(times,times[1:]):
   low=max(R(0),min(right,B)-max(left,R(0)))
   high=max(R(0),min(right,T)-max(left,B))
   exposure=(1-rho)*(b1*low+b2*high)/model['N']
   z+=exposure**2
 return model['n']*(model['n']-1)//2*z
```

Here R is `fractions.Fraction`; the checked rate pairs were (2,5),(5,2),(3,3),(0,5),(5,0), and period pairs were (.2,.5),(.5,.2),(1,1). Assertions compared `explicit(...) == stage_a.pair(...)` with exact rational arithmetic.

### What the committed tests do and do not prove

`test_phase_sum` compares hand-written exposures with a separately written copy of the polynomial; it never calls production `pair()`. `test_stationary_reduction` likewise proves an algebraic identity separately. Therefore the package's claims of an independently checked production phase sum and of all mandatory checks being covered are stronger than the committed executable evidence. The verification report also names word counts 4 and 7 that are absent from that committed test. The reviewer check above supplies the missing independent production link for this review; its coverage must not be retroactively attributed to the original run.

Other committed tests include production-linked limits/resources, shared-code feasibility/class checks at one chosen case, and one synthetic tie-key test. The class test is not an all-case independent feasibility oracle. Row-order invariance is mathematically supported by sorting and by production consuming frozen L/H, but there is no committed shuffle test. Nine PASS lines establish those nine reported executions, not every broader assertion in verification.json. This distinction does not undermine the independent mathematical proofs in §§3–4.

### Compressed artifacts and exactness

Decoded selected CSV: 15,216 bytes, SHA-256 `237103f972734abafe5e8d0bbfb94ce1ff8d16bb5c9e8c49155e9b4236ef2765`.

Decoded passing-set JSON: 17,889 bytes, SHA-256 `ea79fb3fc0d3e0f6b1c1420ca030ada5e6ca481e3c8db4618626f0628e43cc90`.

The JSON explicitly records U ordering, Fixed actions, Precomputed pairs and each causal root's four second-action masks plus full tree count; pruned cases refer to the direct audit, and searched-empty cases are distinguished. Compression does not hide a different policy model. Both gzip headers have zero mtime and OS byte 255. Byte-for-byte compressed equality should be claimed within the recorded compatible environment, not inferred across arbitrary Python/gzip implementations; decoded content identities are the scientific comparison target.

Classifications use Fractions parsed from frozen decimal strings. Rendered Q, margins and boundary values are rounded binary-float displays, not the operands used in `<=`. Independent selected-row checks agree with exact production classifications and their rendering. Zero numerical ambiguity here means no rational arithmetic ambiguity conditional on those decimals; it does not eliminate input rounding, physical calibration uncertainty or certificate conservatism. The numerical-boundary file is a nearest-case diagnostic, not a substitute for full passing sets. The implementation reevaluates certificates during searches rather than caching a reusable elementary table; that affects efficiency/traceability, not the mathematical selection verified here.

## 7. Findings and smallest corrective actions

### CRITICAL — none identified

No contradiction to the finite-model certificate, HH theorem or reported selected cost vectors was found.

### MAJOR-01 — advertised exact-input reproduction fails its byte gate

**Demonstrated evidence:** the local file has 13,002,858 bytes, 16,993 LF line endings and zero CRLF endings. Its Git blob hash is exactly the connector-confirmed frozen identifier `5de108c6759bcf720073b3fbc6581389d46e63aa`. Its actual SHA-256 is

`9f8a43a00780a0853db6e4a03263eb87672065be5a93edfcc79f544c78f7593d`.

Config instead expects `713eceb0df3faa4ea0eb50f6381c5a26cfb77a969f82e059f58815e8469f1e09`. Replacing LF by CRLF in memory yields exactly that latter hash, with a different Git blob (`33db8f62b47444f4b636f0a5b581e193d7d2a0fc`). Thus this is a serialization-provenance mismatch, not a different numerical rate series. The direct call to `frozen()` raises `RuntimeError: frozen CSV SHA-256 mismatch` before level extraction. `git show` emits the stored LF blob, so the advertised helper cannot pass as written. The absence of a complete byte check in the original run was disclosed, but its asserted fail-closed reproduction remedy is not operational.

**Minimum correction:** distinguish the canonical Git-blob SHA-256 from the historical CRLF-output SHA-256. Make the exact-blob reproduction gate expect the canonical LF bytes, retaining the historical hash under an explicitly different provenance field. Do not silently normalize an arbitrary input, remove the gate, change L/H or rerun transport. Add a small input-gate regression using the canonical file and a deliberately altered file. Record the successful exact-byte/L/H check in a new repair record without rewriting the old run's verification status.

**Closure criterion:** a read-only check of the pinned Git blob passes its declared byte hash, row count and L/H checks; altered bytes fail; hash roles are unambiguous. No full scientific matrix rerun is needed to close this issue. The reviewer already verified the numeric levels independently, so the defect blocks reproducibility acceptance/promotion of the delivery, not the mathematics of the six candidate results.

### MINOR-01 — promised generated run manifest does not exist in the generator

REPORT §11 says the frozen-CSV reproduction additionally records verification in `run_manifest.json`. `stage_a.py::main` writes the eight science artifacts and calls `frozen()`, whose success returns no persisted record; neither it nor reproduce.sh writes a run manifest. The committed manifest is a static original-run record with verification false. It is not regenerated by the supplied command. Likewise the command does not regenerate config/input manifests, derivation or verification reports.

**Correction:** either remove the promise and define reproduction as verified science-table output with a separately recorded input check, or explicitly generate a new, output-local verification manifest with actual hashes/environment. Preserve the original false verification field as historical truth. Never report the original run as fully byte-verified because the reviewer later checked its input.

### MINOR-02 — independent-validation claims exceed persisted tests

**Correction:** persist a production-linked explicit reset-timestamp/overlap-integral test and production-linked stationary-limit check, or accurately cite a separate independently preserved check. Correct verification wording and coverage counts to distinguish original tests, proofs and this review. A small test suite suffices; a full matrix rerun merely repeating constants is not required. This review's successful 270-case oracle and mathematical derivation remove the immediate scientific uncertainty, but do not repair the original test record by implication.

### MINOR-03 — unsafe reproduction-directory handling

The helper deletes a fixed `${TMPDIR:-/tmp}/stage-a-repro` directory and overwrites a fixed CSV path. The reviewer did not execute it. Replace both with paths under a fresh `mktemp -d` directory, keep outputs isolated and make any cleanup explicit. This is a bounded packaging correction, not a reason to change the scientific experiment.

**OPTIONAL:** cache/persist the elementary exact certificate table or document repeated evaluation as an implementation deviation; add decoded artifact hashes and distinguish compressed-byte compatibility from scientific-output equivalence. None changes the finite-model result or requires new scenarios.

## 8. Maximum admissible wording, promotion and next decision

> In the declared finite post-W, data-only Poisson toggle/absorbing-surrogate model, with the prescribed piecewise rate family, sequential credited resets, sufficient first-passage certificate, action grid and R2-U pass cost, the optimal Precomputed and Causal worst-case pass counts coincide whenever certified policies exist. In the six certified known-rho cases, the selected Causal policies strictly reduce computed reads, writes and serial occupied time on LL, LH and HL while preserving HH cost. This is conditional pathwise actuation benefit of current exogenous-level information, not an expected mission benefit, exact physical-risk optimum or net operational information value. The finite ambiguous-rho family fails the chosen sufficient certificate on the accepted grid; physical feasibility and an exact-risk information comparison remain unresolved.

That wording requires all of the following: N=2^24/n=32/Nw=2^19 data-only SEC; declared uniform singleton and two-bit same-word marks; rho={0,.0001,.01} as bit-intensity allocations; exact frozen L/H decimals for d={1,3,5}; LL/LH/HL/HH over two 300 s blocks, no assigned probabilities; clean window start but state carry at 300; full effective group-end restoration, first-passage recording and the declared serial service assumptions; U={.2,.5,1,2,5,10,20,30,60,100,150,300}; the eight experimental epsilons; exogenous current-level-only information, shared first-action prefixes and fixed comparator/selection classes. P grounds service time, not measured hardware throughput. No calibration of rho, proprietary W, parity, heavy-ion contribution, angular operator, estimator or information/controller overhead is accepted.

**Promotion eligibility:** the bounded scientific content is eligible for later consideration, but final promotion of this implementation-backed candidate should await MAJOR-01 closure and truthful provenance/validation wording. No RES/HYP/CLM is created here. The recommendation does not require another broad CY62167 review or redesign of Stage A.

**Next scientific decision:** the simultaneous zero worst-case gap and positive pathwise gap support consideration of a bounded operational-information follow-up. The pathwise difference survives exact arithmetic and changes declared actuation components, satisfying the relevant opportunity test in the accepted specification without inventing an engineering-significance threshold. It neither automatically launches Stage B nor warrants blanket termination on the basis of zero minimax gain. The unresolved rho family prevents quantifying a separate robust certified comparison on this grid, without invalidating known-rho findings. The remaining byte/provenance issue blocks clean delivery acceptance, not recognition of that conditional opportunity; close it through the narrow corrective action above before relying on a claim of reproducible execution.

**Final disposition: REVISE.** One MAJOR packaging/input-identity gate, three bounded MINOR corrections; no demonstrated failure of the central finite-model result. Orchestrator/PI retains scientific acceptance, promotion and subsequent-study authority.
