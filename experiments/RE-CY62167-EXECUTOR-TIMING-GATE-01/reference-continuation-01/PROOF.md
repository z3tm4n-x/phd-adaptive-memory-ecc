# Conditional executor bound — reference continuation 01

OWN RESULT proposed for review, not an accepted RES or physical-device theorem.
Controlling input d59de85eb46ae1fa254f3b936ce6fa64c28bcff0; configuration locked
in the preregistration commit before computing this result. No slot was changed.

## Model and quantifiers

There are N=524288 words of 32 modeled data bits. The frozen 288-row rate r(t)
is constant on each 300-s block of H=[2026-01-19 04:00 UTC, 2026-01-20 04:00 UTC).
Within each word the 32 simple per-bit NHPPs are independent, with the same r.
Marks toggle one data bit atomically. Cross-word independence is not needed
for the union bound. ECC capability is one erroneous modeled data bit.
This is the inherited registered data-only model, NOT a claim that the three
physical SRAMs, their inner ECC, 7 outer parity bits or hidden storage obey it.

On the preparation interval each bit has a deterministic intensity no greater
than the parameter r_pre_upper; the NHPP/within-word independence assumption
extends across t0 (independent increments including intervals straddling it).
No pre-H measurement is inferred from the frozen series. The named example
sets r_pre_upper=max(r_j) by ASSUMPTION.

Fix any deterministic clock trajectory satisfying the interval envelope in
TIMING.md, externally anchored to t0. The bound is uniform over such trajectories.
It also applies after conditioning on an exogenous clock independent of the
arrival processes. It does NOT license arbitrary radiation-dependent clock
time changes; that coupling must be addressed by the future joint contract.

Assume qualified trusted preparation and correct transfers outside the explicitly
paid service event below. At a scrub latch, if no arrival occurs in the whole
service tube, the executor sees the correct coherent modeled word; it corrects
a singleton and clean/ERR-only writes preserve correct data. These are MODEL
transfer semantics, not an inference from ERR or evidence of inner-ECC behavior.
Application reads cause no state update and never shift reservations.
Write and hold completion satisfy TIMING.md before the tick-24 fence.
No fault/retry/clock pause is silently admitted to an otherwise valid epoch.

## Histories, service event, and inclusion

Let g(x) denote real time of service tick x, with epoch_tick=0.
Word w is prepared in
Q_w=[g(-20000000+24w), g(-20000000+24(w+1))].
Its qualified endpoint sigma_w is the latter, conservative fence time.
Its scrub tubes are
R_wk=[g(kP+floor(wP/N)),g(kP+floor(wP/N)+24)], k>=0.
Intersect histories with H as necessary, but keep complete tubes for upper bounds.
Use closed tubes; endpoint convention has zero probability under simple NHPP
with continuous integrated intensity. The deterministic tests include endpoints.

B is any modeled data-bit arrival in the union of all Q_w and all R_wk touching H.
Pay every reserved tube, whether the eventual outcome is clean, corrected, ERR-only
or detected uncorrectable. This makes the tube set independent of outcomes.
B includes read aperture and pending write, once, not only 31 “other” bits.

Outside B, each word is clean at its own sigma_w. Inductively, until the first
capability exceedance, it is clean at every subsequent scrub fence: zero errors
remain zero (including ERR write), one error is corrected, and there is no hit
inside the tube. The physical write may finish earlier than the fence; extending
the protected service event to the fence makes this later clean endpoint valid.
No assertion of a globally clean array at t0 is made.

Partition each word's history [sigma_w,H_end] by its scrub fence endpoints.
Let Pairs be the event that in one such interval arrivals occur on at least two
distinct data bits. Toggle cancellations do not invalidate necessity: from a
clean endpoint, >1 erroneous bits requires arrivals on two distinct bits.
Thus first passage, including unsafe state already present at t0, satisfies

    E_exec,H ⊆ Pairs ∪ B.

This inclusion may additionally count pre-H first passage; that is conservative.
After the first passage the decoder may miscorrect or fault; no post-failure
behavior is used to prove that the event did not happen. A hit before a word's
own initialization is erased by its qualified full write and is not initial
model history. Hits during that write are in B.

## Pair bound with initial age and clock envelope

For an interval I, write Lambda_I=integral_I r(t) dt, extending with an upper
r_pre_upper before t0. Independence of two bit processes gives
Pr(N_i(I)>0,N_j(I)>0) <= Lambda_I^2. Summing 496 unordered pairs and applying
Cauchy-Schwarz gives Lambda_I^2 <= |I| integral_I r(t)^2 dt.

Successive scrub fences are P ticks apart. The initial fence gap is

    20000000 + floor(wP/N) - 24w ticks.

Since floor increments are 190 or 191, this increases with w. Exhaustive
independent enumeration verifies the maximum 107416921 ticks. Let

    p_plus  = upper(P) seconds
    L       = max(p_plus, upper(107416921))
    T_pre   = upper(20000000)
    K       = N*496
    I2      = 300*sum_j r_j^2.

The last incomplete interval is bounded by the next scheduled fence gap even
if that fence is outside H. Extending all word histories to [-T_pre,H_end]
only enlarges their integrals. Therefore

    Pr(Pairs) <= K*L*(I2 + T_pre*r_pre_upper^2).

L≈1.0742229216460573 s includes late first scrub, not just preparation age.
Global replacement by L is deliberately loose; no optimization of phases,
period, physical topology, rates or epsilon was performed.

## Service-tube exposure, block edges and clocks

Let D=upper(24) seconds and p_minus=lower(P) seconds. Each word has one
preparation tube, so its contribution to Pr(B) is <=32*N*D*r_pre_upper.

In a real-time block [a,a+300), a scrub tube can intersect only if its start
is in [a-D,a+300]. Starts for one word are separated by at least p_minus.
Consequently at most

    n_block = floor((300+D)/p_minus)+1 = 301

tubes intersect that block. The total intersection measure is <=n_block*D.
Multiply by that block's intensity and sum. Boundary tubes may be counted at
full duration on both sides; this only overestimates the integral. The same
argument covers first/last clipped blocks; no full-cycle identity is assumed.

    Pr(B) <= 32*N*D*(r_pre_upper + n_block*sum_j r_j).

Expectation of Poisson counts and a union bound suffice. Correlation of B with
Pairs is immaterial. B appears only once; Pairs may overlap B conservatively.
There is no additional independent “read risk” or pending surcharge being paid.

## One bound and its permitted pre-H parameter

    U_exec(r_pre)=min(1,A+Bcoef*r_pre+C*r_pre^2)
    A=K*L*I2 + 32*N*D*n_block*sum_j r_j
    Bcoef=32*N*D
    C=K*L*T_pre.

Exact fractions, all decomposed terms, signed slack and a certified 180-step
bisection bracket for the nonnegative root of A+Bcoef*r+C*r^2=.001 are in
bounds.json. The checker independently enumerates all first gaps and uses
95-digit Decimal arithmetic, sharing only frozen inputs and the declared
mathematical bound; it does not import the production calculator.

For the named assumed r_pre=max(r_j):

| Component | Upper / value (rounded here, exact in bounds.json) |
| --- | ---: |
| Pair term in H | 0.00033281120939194375 |
| Service-tube term in H | 0.00062974563158061519 |
| Pair term before H | 0.000000020088634849906944 |
| Preparation-tube term | 0.000000076512606764920255 |
| U_exec | 0.00096265344221417375 |
| 0.001-U_exec | +0.00003734655778582626 |
| Permitted r_pre endpoint | about 7.833153909485812e-7 per bit per second |

The last row is a sufficient-domain boundary for this upper, not a physical
pre-H rate guarantee or a necessary operating limit. Above it this upper fails;
no excluding lower has been established.

The larger initial gap adds ≈2.2979940439975607e-5 to the H pair bound relative
to using p_plus alone. Clock period dilation adds ≈1.5491718347741628e-8 relative
to exact 1 s. Clock/block counting adds ≈3.4283233348046483e-6 to the tube term
relative to nominal 32*N*(240 ns/1 s)*I1. Together with the two pre-H terms
these are transparent decompositions, not extra terms to add again.

## Relation to the accepted ideal control

The earlier theorem requires clean/no-pending global start, instantaneous
coherent checks exactly one second apart and singleton-only clean-latch writes,
with its 31-other-bit pending event. Under precisely that narrower contract,
recomputing the frozen integrals recovers

    a_upper=0.0003098157772336203819978391463469440873
    b_upper=2528.1037181797039690725 s^-1
    Delta_star=6901842227663796180021608536530559127 /
               25281037181797039690725000000000000000000000 seconds.

The exact boundary gives a_upper+b_upper*Delta_star=.001. This is a separate
control, not the specialization of our coarser all-32-bit/all-slot union bound
forced into equality. In the new contract neither 240 ns<273 ns nor the smaller
pending window alone decides passage. The full U_exec above does.

## Transfer boundary

For a physical conclusion one still needs, on a common probability space,
E_cap,physical intersect V^c ⊆ E_exec,model, Pr(V)<=delta_joint and
U_exec+delta_joint<=.001. The positive slack is only an available numerical
budget, NOT an estimated delta_joint. Hidden ECC/parity, mixed pathways,
clock/controller/board timing failures, image trust, readiness and r_pre
qualification must be handled jointly, neither omitted nor charged twice.
This task constructs no such coverage contract and assigns no H_req/epsilon_req.
