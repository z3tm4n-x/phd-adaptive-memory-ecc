# RE-GOES-REAL-TEMPORAL-01 — derivation

## 1. Scope

This derivation implements only the accepted contract in
`docs/research_gates/GOES-REAL-TEMPORAL-PREEXECUTION-01.md`.
The physical/service slice is unchanged from reviewed Stage A: known
\(\rho=0\), data-only SEC over \(2^{19}\) logical words of 32 data bits,
R2-U sequential full-pass restoration, the frozen action grid \(U\), and
two 300-s decision blocks in a 600-s window.

GOES-19 is used only as a real chronological environmental reference and
as signal content for a hypothetical delayed external-information comparator.
It is not an assumed operational input to the target memory controller.

## 2. Information family and non-emptiness

For a given shielding case, let the accepted counterfactual ceiling be \(B\)
and let \(x_j\) denote the declared constant rate in five-minute bin \(j\).
The experimental family is

\[
0\le x_j\le B,\qquad |x_{j+1}-x_j|\le gB,\qquad 0\le g\le1.
\]

For delivered observations \(O=\{(i,y_i)\}\), define \(c=gB\).  On the
integer bin lattice, a necessary and sufficient consistency condition is

\[
0\le y_i\le B,\qquad |y_i-y_k|\le c|i-k|
\]

for every delivered pair \(i,k\).  The corresponding minimum admissible
variation parameter is therefore

\[
g_{\min}(O)=
\max_{i\ne k}\frac{|y_i-y_k|}{B|i-k|},
\]

with \(g_{\min}=0\) for zero or one numerical observation.  If an observation
lies outside \([0,B]\), the model is empty for all \(g\in[0,1]\).

The same pairwise criterion is used for the retrospective replay-membership
audit over all known valid bins in the 3600-s context plus 600-s window.
Fallback-derived reference values participate in this retrospective audit.
A missing reference bin is not filled; pairwise consistency of the known
anchors establishes existence of at least one completion.

## 3. Attainable componentwise upper envelope

For nonempty \(M(I)\), define

\[
u_j(g)=\min\left[
B,\ \min_{(i,y_i)\in O}\left(y_i+gB|j-i|\right)
\right].
\]

With no numerical observations, \(u_j=B\).

This is not merely a collection of independent pointwise upper bounds.
It is itself an element of \(M(I)\).

1. Each cone \(y_i+c|j-i|\) is \(c\)-Lipschitz on the bin lattice, and the
   constant \(B\) is also at most \(c\)-Lipschitz.
2. The pointwise minimum of functions sharing the same Lipschitz constant
   remains \(c\)-Lipschitz.
3. At an observed bin \(k\), the \(k\)-cone equals \(y_k\).  Pairwise
   consistency gives \(y_i+c|k-i|\ge y_k\) for every other observation,
   while \(B\ge y_k\).  Hence \(u_k=y_k\).
4. All terms are nonnegative, so \(0\le u_j\le B\).

Thus \(u\in M(I)\).  Conversely, every \(x\in M(I)\) obeys
\(x_j\le B\) and \(x_j\le y_i+c|j-i|\) for every observed \(i\), hence
\(x_j\le u_j\) componentwise.  Therefore \(u\) is a simultaneously
attainable componentwise maximum of the compatible family.

`envelope_segments.csv` records the active affine cone or ceiling on each
piecewise-linear \(g\)-region.

## 4. Why the envelope maximizes the retained Stage-A certificate

At \(\rho=0\), the direct term is zero.  For a fixed deterministic R2-U
schedule, every word/reset-interval exposure has the form

\[
E_J=\alpha_{J0}b_0+\alpha_{J1}b_1,\qquad
\alpha_{J0},\alpha_{J1}\ge0,
\]

where \(b_0,b_1\) are the two window-bin rates.  The Stage-A sufficient
certificate is

\[
Q={32\choose2}\sum_w\sum_J E_J^2.
\]

On the nonnegative rate domain, every \(E_J^2\) is nondecreasing in each
rate coordinate.  Since the upper sequence \(u\) is itself compatible,

\[
\sup_{x\in M(I)}Q(x;\tau_1,\tau_2)
=Q(u_0,u_1;\tau_1,\tau_2).
\]

There is therefore no relaxation gap introduced by maximizing the retained
certificate with the envelope.

For the reviewed R2-U phases, with
\(P=0.18874368\) s,
\(N_w=2^{19}\),
\(r_i=b_i/2^{24}\),
\(A_1=P(N_w-1)/2\), and
\(A_2=P^2(N_w-1)(2N_w-1)/(6N_w)\),

\[
\begin{aligned}
S={}&r_0^2(N_w\tau_1^2-2\tau_1A_1+A_2)
 +(300/\tau_1-1)N_w(r_0\tau_1)^2\\
&+N_w(r_1\tau_2)^2
 +2r_1\tau_2(r_0-r_1)A_1
 +(r_0-r_1)^2A_2\\
&+(300/\tau_2-1)N_w(r_1\tau_2)^2+r_1^2A_2,
\end{aligned}
\]

and \(Q=496S\).  The crossing term retains exposure on both sides of
\(t=300\); no simultaneous/free reset is inserted.

For fixed \((\tau_1,\tau_2)\), \(Q\) is a homogeneous quadratic form in
\((b_0,b_1)\).  On any envelope segment

\[
u_0=a_0+s_0g,\qquad u_1=a_1+s_1g,
\]

the certificate is therefore a quadratic polynomial in \(g\).
Production code uses this structure to locate candidate action transitions;
every reported selected certificate boundary is then independently bracketed
with 60-digit Decimal evaluation.  The released boundary brackets are no
wider than \(10^{-14}\).

## 5. Causal availability

A frozen GOES five-minute value stamped \(t_j\) represents the declared
average over \([t_j,t_j+300\text{ s})\).  For the delayed comparator it can
constrain \(M(I)\) only at

\[
t_j+300\text{ s}+L,
\]

with \(L\in\{0,300,900,1800\}\) s. Equality-time delivery is included before
the action.  Numerical observations using the retained historical high-energy
global-median fallback are suppressed, as are invalid central values.
The corresponding retrospective exposure is not deleted.

At \(t=0\), the freshest potentially available bins are respectively
\(-1,-2,-4,-7\) for the four \(L\) values.  At \(t=300\), they are
\(0,-1,-3,-6\), subject to fallback/missing masking.

The Ideal current-rate comparator instead receives exact frozen reference
rates through bin 0 at \(t=0\) and through bin 1 at \(t=300\).  This is an
information benchmark, not a physically available GOES average.  For the
selected window containing a missing reference bin, the exact Ideal replay
cost is marked unavailable; only compatible-set stress calculations are
retained.

## 6. Planning and one replan

At \(t=0\), each information class certifies all 144 pairs in \(U^2\) against
its current \(M(I)\).  The selected pair minimizes total pass count and then
lexicographically maximizes \((\tau_1,\tau_2)\).  Fixed is restricted to
\(\tau_1=\tau_2\).  Precomputed has no section-specific observations and
commits both periods.

Delayed and Ideal comparators execute the selected first period.  At
\(t=300\), \(\tau_1\) is retained and \(\tau_2\) is reselected to minimize
remaining passes, with the largest \(\tau_2\) breaking ties.

For a compatible update, \(M(I_{300})\subseteq M(I_0)\).  Consequently the
initially planned continuation remains certified; the replan may keep it or
reduce actuation.  The focused tests verify this for every reported certified
region.  An empty updated model is a contract violation, never permission to
relax restoration.

This rule is deliberately not claimed to be a globally optimal adaptive
policy tree.

## 7. Resource identities and interpretation of a replay violation

For a selected pair,

\[
N_{\rm pass}=300/\tau_1+300/\tau_2,
\]

\[
N_{\rm read}=N_{\rm write}=2^{21}N_{\rm pass},
\]

\[
t_{\rm occ}=PN_{\rm pass},\qquad
\mathrm{occupancy}[\%]=100\,t_{\rm occ}/600.
\]

These are R2-U actuation quantities only; acquisition, communication,
controller compute, workload latency and energy are not included.

A selected policy can be mathematically certified under an assumed \(g\) even
when the retrospective section requires a larger \(g\).  Such a row is
explicitly marked `replay_compatible=0`.  It is not practical evidence of
adaptation and is retained only to show where the assumed model family failed.
No selected window, \(g\), \(B\), or latency is retuned to remove this outcome.
