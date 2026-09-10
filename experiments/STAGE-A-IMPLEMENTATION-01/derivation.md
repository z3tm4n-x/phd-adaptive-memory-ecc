# STAGE-A-IMPLEMENTATION-01 — derivation

## 1. Scope and status of the model

This derivation implements only the accepted Stage A conditional post-`W` model from
`docs/research_gates/STAGE-A-PREEXECUTION-01.md`.  It is not a calibrated mission model,
not an identification of proprietary `W`, and not a proof of physical optimality.

The declared data-only organization is

- `N = 2^24 = 16,777,216` data bits;
- `n = 32` data bits per logical word;
- `N_w = 2^19 = 524,288` logical words;
- SEC correction threshold: one erroneous data bit per word.

At full-array erroneous-bit intensity `b(t)`, the declared parent streams are

\[
\nu_C(t)=(1-\rho)b(t),\qquad
\nu_D(t)=\frac{\rho b(t)}{2},
\]

so that exactly

\[
\nu_C(t)+2\nu_D(t)=b(t).
\]

Here `rho` is the fraction of *erroneous-bit intensity* allocated to same-word two-bit
parent events.  It is not a parent-event probability.

## 2. Why the sufficient certificate has the stated form

### 2.1 Direct same-parent contribution

A declared direct parent event targets two data bits of one logical word.  Under the
reviewed coupling, the Stage A surrogate absorbs on such an event.  The corresponding
physical toggle process can sometimes cancel a pre-existing error, but the absorbing
surrogate cannot; therefore the surrogate first-passage indicator upper-bounds the
corresponding toggle first-passage indicator under the same marks and restoration
schedule.

For a fixed scenario path over `[0,T]`, the mean number of direct parents is

\[
\Lambda_D=\int_0^T \nu_D(t)\,dt.
\]

Hence

\[
P(\hbox{at least one direct parent})=1-e^{-\Lambda_D}\leq \Lambda_D.
\]

Stage A deliberately uses this additive upper term.  It does **not** use the
independent-thinning product formula as the control certificate.

For the two 300 s blocks,

\[
\Lambda_D=\frac{\rho}{2}\left(300b_1+300b_2\right).
\]

This term is action-independent, which justifies the required direct-budget pruning
before any policy enumeration.

### 2.2 Accumulation contribution within one restoration interval

After uniform thinning over all data bits, each data bit receives singleton events at
instantaneous rate

\[
r(t)=\frac{\nu_C(t)}{N}.
\]

Consider one logical word and one interval `J` between two credited restorations of
that word.  For each of its 32 data bits the integrated Poisson mean is

\[
x_J=\int_J r(t)\,dt.
\]

A residual first passage beyond SEC within `J` requires that at least two distinct data
bits of the word have each received one or more singleton arrivals since the previous
credited restoration.  For any unordered pair of distinct bits `(i,j)`, Poisson
thinning gives

\[
P(N_i(J)\ge 1,\,N_j(J)\ge 1)
=(1-e^{-x_J})^2\le x_J^2.
\]

Union-bounding over the `C(32,2)=496` unordered bit pairs, over words, and over their
restoration intervals gives

\[
P(\hbox{residual first passage})
\le {32\choose2}\sum_w\sum_J\left(\int_J r(t)\,dt\right)^2.
\]

The construction is intentionally first-passage conservative: it does not attempt to
credit later toggle cancellation after the word has already crossed the SEC threshold.

### 2.3 Combined Stage A certificate

A final union bound between the direct and accumulation mechanisms gives

\[
Q = \min\left\{1,
\Lambda_D+{32\choose2}\sum_w\sum_J
\left(\int_J r(t)\,dt\right)^2\right\}.
\]

Certification in this task means `Q <= epsilon` under the exact frozen decimal inputs.
Failure of this sufficient upper certificate is not physical infeasibility.

## 3. R2-U word phases and the boundary at t=300 s

A full R2-U pass consists of `2^21` reads and `2^21` unconditional writes at 45 ns per
operation, hence

\[
P=0.18874368\ {\rm s}.
\]

For word `w=0,...,N_w-1`, the credited restoration occurs after its four-address group,
with offset

\[
u_w=\frac{w+1}{N_w}P
\]

from pass start.  Define

\[
a_w=P-u_w=P\frac{N_w-w-1}{N_w}.
\]

If a pass in a block ends at `k tau`, the word is restored at `k tau-a_w` relative to
that block start.

Let the first and second 300 s block rates be `r_1,r_2`, and their selected periods be
`tau_1,tau_2`.  Since every accepted `tau` divides 300, write

\[
m_1=300/\tau_1,\qquad m_2=300/\tau_2.
\]

Starting clean at `t=0`, the squared-exposure contributions for word `w` are exactly:

1. initial interval: `[r_1(\tau_1-a_w)]^2`;
2. `m_1-1` first-block interior intervals: `(m_1-1)(r_1\tau_1)^2`;
3. the interval crossing `t=300`:
   \[
   [r_1a_w+r_2(\tau_2-a_w)]^2;
   \]
4. `m_2-1` second-block interior intervals: `(m_2-1)(r_2\tau_2)^2`;
5. final tail to `t=600`: `(r_2a_w)^2`.

The crossing interval explicitly contains old-level exposure before 300 s and new-level
exposure after 300 s.  There is no free reset at the block boundary.

The two phase sums needed to avoid looping over all words are

\[
A_1=\sum_w a_w=P\frac{N_w-1}{2},
\]

\[
A_2=\sum_w a_w^2
=P^2\frac{(N_w-1)(2N_w-1)}{6N_w}.
\]

Therefore the exact production sum is

\[
\begin{aligned}
S={}&r_1^2(N_w\tau_1^2-2\tau_1A_1+A_2)
 +(m_1-1)N_w(r_1\tau_1)^2\\
&+N_w(r_2\tau_2)^2
 +2r_2\tau_2(r_1-r_2)A_1
 +(r_1-r_2)^2A_2\\
&+(m_2-1)N_w(r_2\tau_2)^2+r_2^2A_2.
\end{aligned}
\]

The accumulation term in `Q` is `496 S`.

## 4. Stationary reduction

For constant `b`, identical periods `tau_1=tau_2=tau`, and collapsed simultaneous word
phases `P -> 0`, there are exactly `T/tau` restoration intervals over `T=600 s`.  The
accumulation term reduces to

\[
{32\choose2}N_w\frac{T}{\tau}
\left(\frac{\nu_C\tau}{N}\right)^2
=\beta\tau T\nu_C^2,
\]

with

\[
\beta=\frac{31}{2\,2^{24}},
\]

which is the reviewed stationary `Q_U` accumulation expression.  The focused tests
verify this identity exactly with rational arithmetic.

## 5. Applicability to the causal comparator

For a fixed complete path (`LL`, `LH`, `HL`, `HH`), the Stage A causal controller sees
only the exogenous current level at each block boundary.  It does not observe Poisson
arrivals or word state.  Conditioning on a complete scenario path therefore turns its
selected restoration schedule into a deterministic schedule.  The same first-passage
certificate above applies path-by-path without an event-dependent stopping rule.

Causality is enforced by construction:

- `LL` and `LH` share the same first action;
- `HL` and `HH` share the same first action;
- the second action may depend on the observed two-level prefix;
- no first action is selected using the second level.

## 6. Policy-class inclusion and selection

The finite accepted classes satisfy constructively

\[
\mathrm{Fixed}\subseteq\mathrm{Precomputed}\subseteq\mathrm{Causal}.
\]

A Fixed action `tau` is the Precomputed pair `(tau,tau)`.  Any Precomputed pair
`(tau_1,tau_2)` is represented causally by using the same first action for both first
levels and the same second action for all four prefixes.

Among robustly certified policies the accepted selection rule is applied exactly:

1. minimize worst-case total pass count over `LL,LH,HL,HH`;
2. lexicographically minimize the path pass-count vector in that order;
3. lexicographically maximize realized periods in path/time order.

No scenario probabilities or weighted mission costs are introduced.

## 7. Structural reason for the zero Precomputed-to-Causal minimax gap

For a fixed action pair, every exposure integral is a nonnegative linear function of
`b_1,b_2`, and `Lambda_D` is also nondecreasing in both block rates.  Therefore

\[
Q(LL)\le Q(LH),Q(HL)\le Q(HH)
\]

in the componentwise sense needed here, with `HH` the required dominating path for the
same action pair.

Take the action pair used by any certified causal policy along its `HH` branch.  That
same pair, if applied precomputed to all four paths, certifies all four paths because
none has rates exceeding `HH`.  Its pass count is exactly the causal `HH` pass count.
Conversely, Precomputed is a subset of Causal.  Hence the optimum worst-case pass count
of the two classes is equal in this accepted model.

This does **not** make current information worthless: Causal can use much longer periods
on `LL`, `LH`, and `HL` while retaining the same `HH` branch.  It means only that the
required `HH` scenario prevents current information from lowering the minimax pass-count
scalar.  Without scenario probabilities, those pathwise savings must not be converted
into an expected mission gain.
