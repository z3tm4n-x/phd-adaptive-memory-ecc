# STAGE-A-INFORMATION-INTERFACE-01 — analytical derivation

## 1. Scope

This task changes only the Stage-A information interface.  It keeps `rho=0`, the
two-level `L/H` paths, the 600 s horizon, the action set `U`, the R2-U sequential
restoration semantics, and the reviewed Stage-A sufficient certificate `Q`.

No practical sensor, estimator, scenario probability, report-error probability,
new ECC model, or new reliability requirement is introduced.

The two action times remain

\[
t_0=0,\qquad t_1=300\ {\rm s}.
\]

Measurements have timestamps

\[
0\le s_1<300,\qquad 300\le s_2<600
\]

and a common nonnegative delivery latency \(\ell\).  A report delivered exactly at
an action time is available before that action.  There are no pre-window
observations.

## 2. Timing equivalence is finite

Define three Boolean availability predicates:

\[
A_0 =
\mathbf 1\{\text{update 1 enabled},\ s_1=0,\ \ell=0\},
\]

\[
A_1 =
\mathbf 1\{\text{update 1 enabled},\ s_1+\ell\le300\},
\]

\[
A_2 =
\mathbf 1\{\text{update 2 enabled},\ s_2=300,\ \ell=0\}.
\]

`A0` means the first-block report is available for the action at 0 s; `A1`
means it is available by the action at 300 s; and `A2` means the second-block
report is available for the action at 300 s.

Because \(A_0\Rightarrow A_1\), only six signatures are possible:

| Class | `(A0,A1,A2)` | Information available at decisions |
|---|---|---|
| T000 | `(0,0,0)` | none |
| T001 | `(0,0,1)` | only current second-block report at 300 s |
| T010 | `(0,1,0)` | delayed first-block report by 300 s |
| T011 | `(0,1,1)` | first- and second-block reports both available at 300 s |
| T110 | `(1,1,0)` | first-block report available at 0 and retained at 300 s |
| T111 | `(1,1,1)` | current report at both action times |

The equality \(s_1+\ell=300\) belongs to `A1=1`.  Likewise, a second-block
measurement can affect the 300 s action only at the exact boundary
\(s_2=300,\ell=0\).

For the aligned enabled interface \(s_1=0,s_2=300\),

\[
\ell=0\Rightarrow T111,\qquad
0<\ell\le300\Rightarrow T010,\qquad
\ell>300\Rightarrow T000.
\]

Thus this Stage-A timing contract cannot produce a smooth latency response.
Positive latencies within the same availability region are information-equivalent.

## 3. Binary bounded-error equivalence has one threshold

Let

\[
\Delta=b_H-b_L>0
\]

and let a delivered measurement satisfy

\[
|y-b(s_i)|\le\eta\Delta.
\]

For a true low level, the possible measurement interval is

\[
[b_L-\eta\Delta,\ b_L+\eta\Delta],
\]

and for a true high level it is

\[
[b_H-\eta\Delta,\ b_H+\eta\Delta].
\]

These intervals are disjoint exactly when

\[
2\eta\Delta<\Delta
\quad\Longleftrightarrow\quad
\eta<\frac12.
\]

Therefore:

- `E_EXACT`: \(0\le\eta<1/2\). Every valid delivered report identifies the
  true binary level and its compatible set is a singleton.
- `E_AMBIG`: \(\eta\ge1/2\). A report compatible with both levels is allowed.
  At the boundary \(\eta=1/2\), \(y=(b_L+b_H)/2\) already gives the compatible
  set \(\{b_L,b_H\}\).

For \(\eta\ge1/2\), singleton reports are still possible, but the study is
robust over *all* allowed errors.  Hence an ambiguous report must remain in the
policy tree and cannot be assigned zero probability.

Combining six timing signatures and two eta classes gives 12 timing-by-eta
parameter cells but only **11 distinct report-history interfaces**.  In both
`T000_E_EXACT` and `T000_E_AMBIG` no report is available at either decision, so
the eta class cannot alter any observed history.  The two existing identifiers
are retained as separate parameter-cell labels even though their observation
histories are identical.

## 4. Reuse of Stage-A feasible sets

The implementation does not rerun the Stage-A production search.

For every Stage-A `rho=0` case with nonempty Precomputed and Causal classes, it
decodes the retained `causal_roots` and second-action masks from
`passing_sets.json.gz.b64`.  These masks provide, for each true path and each
admissible first action, the exact Stage-A set of second actions already
classified by the reviewed certificate.

At a first-decision information history \(h_0\), one first action must be shared
by all indistinguishable true paths.

At a second-decision history \(h_{300}\), let \(\mathcal P(h_{300})\) be the set
of true paths compatible with that history and let \(a_1\) be the already
selected first action.  The admissible second actions are

\[
A_2(h_{300};a_1)=
\bigcap_{p\in\mathcal P(h_{300})}
A^{\rm StageA}_{2,p}(a_1).
\]

A first-action map is rejected if this intersection is empty for any reachable
second-decision history.  Otherwise the largest action in the intersection is
selected for that history.  This is valid under the inherited Stage-A ordering:
distinct actions in `U` have distinct second-block pass counts, so the largest
feasible period strictly minimizes that local pass count and also wins the
period-maximizing tertiary tie-break.

The remaining enumeration is only over distinct first-decision histories, at
most three (`{L}`, `{H}`, `{L,H}`), not over the old physics/action matrix.

## 5. Selection rule and certificate

The inherited selection order is extended robustly:

1. minimize the worst pass count over true paths and all allowed report histories;
2. lexicographically minimize the four pathwise worst-report pass counts in
   `LL,LH,HL,HH` order;
3. lexicographically maximize realized periods with report histories ordered by
   timestamp and compatible-set order `{L}`, `{H}`, `{L,H}`.

For each selected path/report realization, the implementation calls the unchanged
Stage-A production `cert()` function with the *actual preceding first action* and
second action.  This is a shared-code consistency check, not a new independent
validation of the Stage-A physical/certificate model.

Because reports are exogenous to Poisson arrivals and memory state, conditioning
on a true path and an allowed report history makes the selected action sequence
deterministic.  The reviewed Stage-A scenario-wise certificate therefore remains
applicable.  This argument would not automatically extend to an internal
error-count controller whose observations depend on the random upset process.

## 6. Analytic endpoint consequences

### 6.1 Ideal action

Across all five certified `rho=0` Stage-A cases, the selected Ideal Causal tree
uses different first actions for low and high first-block levels and different
second actions for low and high second-block levels.

Consequently the complete selected Ideal tree is representable only in

\[
\boxed{T111\_E\_EXACT}.
\]

In every other region at least one action history merges paths on which the
selected Ideal tree requires different actions.

### 6.2 Ambiguous uncertainty

For every timing class with \(\eta\ge1/2\), a common all-ambiguous/no-report
history is allowed on **every** one of the four true paths.  Consider the two
actions taken by any certified imperfect-information policy on that common
history.  Because the same history occurs on every path, those actions form one
single action pair that is feasible for all four paths; therefore it is an
all-path-feasible Precomputed pair.

Let \(P\) be the optimal Precomputed pass count.  The pass count of the common
ambiguous-history pair cannot be below \(P\), so for each true path \(p\), its
worst-report cost satisfies

\[
C_{\rm imperfect}^{\rm worst}(p)\ge P.
\]

Conversely, the imperfect-information class may ignore every report and execute
the optimal Precomputed pair, which gives cost \(P\) on every path.  Hence an
optimal minimax imperfect-information policy has every path component at most
\(P\).  Combining the lower and upper bounds yields the stronger pathwise
result

\[
\boxed{C_{\rm imperfect}^{\rm worst}(p)=P
\quad\text{for }p\in\{LL,LH,HL,HH\}}.
\]

Thus the guaranteed pathwise collapse is not inferred from scalar class
inclusion alone.  The committed per-path ordering check is only a bounded check
of the **selected policies in these finite cells**, not a general theorem that
pathwise cost vectors must be ordered whenever policy classes are nested.

Singleton reports can still produce lower report-conditioned costs.  They are
reported as achievable values, not guaranteed savings.

## 7. Exact timing results for eta < 1/2

The pathwise worst-report pass vectors are:

| Case | T000 | T001 | T010 | T011 | T110 | T111 |
|---|---|---|---|---|---|---|
| d=3 mm, eps=1e-2 | `(2100,2100,2100,2100)` | `(601,2100,601,2100)` | `(1200,1200,2100,2100)` | `(601,1200,601,2100)` | `(601,601,2100,2100)` | `(2,601,601,2100)` |
| d=3 mm, eps=1e-1 | `(210,210,210,210)` | `(61,210,61,210)` | `(120,120,210,210)` | `(61,120,61,210)` | `(61,61,210,210)` | `(2,61,61,210)` |
| d=5 mm, eps=1e-3 | `(900,900,900,900)` | `(301,900,301,900)` | `(600,600,900,900)` | `(301,600,301,900)` | `(301,301,900,900)` | `(2,301,301,900)` |
| d=5 mm, eps=1e-2 | `(90,90,90,90)` | `(31,90,31,90)` | `(60,60,90,90)` | `(31,60,31,90)` | `(31,31,90,90)` | `(2,31,31,90)` |
| d=5 mm, eps=1e-1 | `(10,10,10,10)` | `(6,10,6,10)` | `(7,7,10,10)` | `(6,7,6,10)` | `(3,3,10,10)` | `(2,3,6,10)` |

Order is `(LL,LH,HL,HH)`.

Two non-Ideal patterns are especially informative:

- `T010` (the aligned positive-latency class) retains LL/LH savings but no
  guaranteed HL saving.
- `T011` retains positive guaranteed savings on all three `LL/LH/HL` paths even
  though there is no information for the first action.

For `T011`, the minimum retained fraction across `LL/LH/HL` is:

| Case | minimum retention (approx.) |
|---|---:|
| d=3 mm, eps=1e-2 | 0.600400266845 |
| d=3 mm, eps=1e-1 | 0.604026845638 |
| d=5 mm, eps=1e-3 | 0.500834724541 |
| d=5 mm, eps=1e-2 | 0.508474576271 |
| d=5 mm, eps=1e-1 | 0.428571428571 |

The displayed retention decimals are rounded.  Exact threshold queries use the
integer savings \(G=p_P-p_D^{worst}\) and \(D=p_P-p_I\).  For \(D>0\) and a
rational target \(\gamma=a/b\), \(b>0\), evaluate \(bG\ge aD\); decimal targets
must be parsed as exact decimal rationals rather than binary floats.  When
\(D=0\), retention is not applicable.

Thus exact first-action information is necessary for the *full Ideal tree*, but
not for a substantial fraction of its pathwise saving.  A current second-block
report at the second action is load-bearing for preserving guaranteed savings
simultaneously on `LL`, `LH`, and `HL` in this two-decision model.

## 8. Scope of any latency statement

No number in this study is a maximum permissible latency of a real radiation
sensor.

The sharp aligned boundary at \(\ell=0\) for access to the current second-block
level follows from three special Stage-A assumptions:

1. no observations before the artificial clean-start window;
2. measurements only at the declared `s1,s2`;
3. actions only at 0 and 300 s.

A continuously operating real sensor can carry information from before the
window and can have a different update/action cadence.  Those cases belong to
the next real-temporal-interface study.
