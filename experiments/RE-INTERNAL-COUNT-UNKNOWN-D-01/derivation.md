# Unknown mission-constant D: derivation and numerical contract

Task: RE-INTERNAL-COUNT-UNKNOWN-D-01. Engineering derivation for Scientific Review;
no PASS, RES promotion, or literature-novelty conclusion.
Base: 529709f1b98d12a5f5a2c7b71ee1ff9f53210c97.
Implementation: 11d9462d768e9f537865efbbd63db79b950191a7.

## 1. Fixed physical experiment

W=524288 words, n=32 data bits, H=3600 seconds, sequential pass P=0.18874368 s.
Array rates bL=2.8886786e-5 and bH=6.1249308 s^-1. The hidden environment has
Q(a)=[[-a,a],[a,-a]], initial mixture (1/2,1/2), a=1/D. One unknown a applies
to the entire mission, a in [1/3000,1/30]. Conditional arrivals are Poisson,
with independent uniform word/bit marks. Unconditional word independence is
not assumed after mixing over the hidden environment.

The original twelve periods are unchanged. At the end of a pass, action tau
places the next pass on [t+tau-P,t+tau]; word w resets at its own offset
(w+1)P/W. Only t=0 is globally clean. First passage to two distinct wrong bits
in a word is irreversible in the reliability accounting. It is not identified
with DUE, SDC or a decoder-visible event. A terminal incomplete interval retains
its exposure. True D, current environment and hidden survival are not inputs.

## 2. Auxiliary coupling and interval risk

In the RES-003 auxiliary system each arrival is counted at its word's next
scan. K at a completed pass is the number of arrivals after their individual
word scans. Before the first repeated hit in an uncleared word, real and
auxiliary counters agree and consequently generate the same actions. A same-bit
cancellation also breaks this coupling and is conservatively charged. Real
capability exceedance is contained in this first-repeat event.

Let Bh=integral_0^h b_Z(s)ds, m1_z=E_z Bh and m2_z=E_z Bh^2. For an initial
mode z and k pending arrivals, a sufficient one-interval probability bound is

    r_h(z,k) = [k m1_z(h) + m2_z(h)/2]/W.                 (1)

It counts old-new and new-new pairs. Each new uniform word mark matches a
specified old/new word with probability 1/W. Ignoring some intervening resets
only enlarges this count. Before coupling failure, old arrivals occupy distinct
words; the bound is valid for any distribution of their positions. It also
covers an incomplete final interval.

With kappa=2a, m=(bL+bH)/2, d=(bH-bL)/2, A=(1-exp(-kappa*h))/kappa and
B=(h-A)/kappa,

    m1_L,H = m*h -/+ d*A,
    m2_L,H = m^2*h^2 + 2*d^2*B -/+ 2*m*d*h*A.            (2)

Small arguments use the explicit series in model.py. Cancellation is bounded
against the positive absolute scales bH*h and bH^2*h^2, not a vanishing low-mode
moment. No count/tau plug-in or fitted D appears in (1)-(2).

## 3. Six-coordinate closure of the allowed observation

Use Y=1{own correction count C>0}. This coarsens the allowed numeric count;
it adds no observation. For each generator retain

    q0_z=Pr(Z=z,K=0), qplus_z=Pr(Z=z,K>0),
    mu_z=E[K 1{Z=z}], z=L,H.                             (3)

The first four coordinates are probabilities, the last two are first moments.
There is no K truncation. Every old pending arrival enters the next complete
auxiliary count. Thus K_old>0 forces Y=1; if K_old=0 the new observed arrivals
determine Y. New K depends on the future environment and starting mode but not
on the value of old K conditional on the starting mode.

For a given environment path, observed and pending births are conditionally
independent Poisson counts with means c,k. The six needed coefficients are

    e^-c e^-k, e^-c(1-e^-k), (1-e^-c)e^-k,
    (1-e^-c)(1-e^-k), k e^-c, k(1-e^-c).                 (4)

These are probabilities C0K0/C0K+/C+K0/C+K+ and moments E[K;C0], E[K;C+].
Integrating the path and final mode and composing with the idle segment gives
a 4-by-6 matrix K_j,tau[y]. Let v=q_probability K_j,tau[y]. Then

    ell_j=sum(v[0:4]), q'_j=v/ell_j.                     (5)

Old pending moments do not enter likelihood; they enter (1) linearly. This
establishes the closure, not only an empirical approximation. Normalization
is of the auxiliary law, not physical mass conditioned on non-failure.
Conditional pending mean is at most mu_max=bH*P/2: conditioning on Y only mixes
paths whose independent pending Poisson means obey that bound.

## 4. Finite kernels and the paid model error

Idle evolution is a four-state CTMC (mode, zero/positive observed births).
During a scan the actual scanned fraction is floor(W*s/P)/W. Its approximation
max(s/P-1/(2W),0) has primitive error at most 1/(8W^2). Scan paths with zero,
one and two environment switches are integrated explicitly; use 512 midpoint
nodes for one switch and 128-by-128 for two, after ordered-times substitution
(u,u+(1-u)v) with density 2(1-u). The omitted Poisson switch mass is replaced
by a specified same-mode/no-birth transition, never silently removed.

Set nu=P*a, v=(bH-bL)*P, p1=exp(-nu)*nu, p2=p1*nu/2. A uniform row-TV bound is

    e_j = Pr{Pois(nu)>=3}
        + p1*(4*v+4*v^2)/(24*512^2)
        + p2*(40*v+40*v^2)/(24*128^2)
        + P*(bH+nu*(bH-bL))/(4*W^2),
    delta_model,j = 18000*e_j.                          (6)

Poisson law first-derivative L1 norm is at most 2 and second/mixed derivative
norm at most 4. Chain rule gives the stated one-switch and transformed
 two-switch bounds, including the density derivatives. Primitive error and
integration by parts pay for the terminal level and expected mode jumps.
These are the accepted RES-003 scan bounds; projecting to binary counts cannot
increase TV. K is unbounded and no pending-overflow allowance is needed.

The reference finite kernel still represents a full probability law on the
unbounded pending count, with (3) its exact sufficient statistics. TV is used
for a stopped-event coupling, not to transfer an unbounded reward expectation.
The largest model allowance is approximately 0.001012 over the full horizon.

## 5. Continuous a: a whole-mission probability interpolation

For any fixed causal policy which does not receive the true a, the number of
switches over the whole mission is Poisson(aH). Conditional on n switches,
the ordered switch times are uniform order statistics, independent of a.
The initial mixture and conditional marked-arrival law also no longer depend
on a. All endogenous observations/actions can therefore be included in fixed
coefficients f_n in [0,1]:

    F(a)=exp(-aH) sum_{n>=0} f_n (aH)^n/n!.               (7)

For l<=a<=u, write a=l^(1-t)*u^t. Holder's inequality for the nonnegative
series (first finite, then monotone convergence) gives

    F(a) <= exp(H*((1-t)*l+t*u-a))
            * F(l)^(1-t)*F(u)^t.                        (8)

Limits cover zero endpoint probabilities. Linear-interpolation error for exp
on [log l,log u] is at most u*log(u/l)^2/8. Since log r<=(r-1)/sqrt(r),

    exp(H*((1-t)*l+t*u-a)) <= exp(H*(u-l)^2/(8*l)).        (9)

Use exact rational a_j=(32+9*j)^2/(3000*32^2), j=0,...,32. All 32 directed
Decimal interval bounds in (9) are below G=1.064. Consequently,

    all node F(a_j)<=theta=0.1/G  implies
    all a in [1/3000,1/30] have F(a)<=0.1.               (10)

This is neither an empirical endpoint maximum nor a grid substituted for the
continuum. The theorem is applied to the physical whole-mission event. It
cannot simply be applied to the approximate scan model as though that model
had the original whole-mission switch law. It also applies to a fixed event
of exact auxiliary observation history. The known-D diagnostic changes policy
with true a and is not automatically covered by this fixed-policy argument.

## 6. Anytime exclusions and retained cells

L_j,i is the likelihood of the policy's own binary observations under auxiliary
node j and its actual past actions. Keep the fixed test mixture
M_i=(1/33)*sum_j L_j,i over ALL nodes, including rejected nodes. This mixture
is a mathematical test, not a physical prior or a risk average. The process

    E_i(j)=M_i/L_j,i                                    (11)

is a nonnegative martingale under law j: actions are predictable from the
history and next-observation probabilities sum to one. E_0(j)=1. With
beta0=0.005/G, stopping at the first crossing yields Ville's inequality

    Pr_j{some i: E_i(j)>1/beta0}<=beta0.                  (12)

There is no renewed beta at each observation. No multiplicity penalty across
all possible true parameters is needed for this pointwise-in-true-parameter
requirement. Persistent rejection uses log(E)>log(1/beta0)+0.001; the arithmetic
margin is justified below.

Remove a CLOSED cell [a_j,a_(j+1)] only after both endpoint tests have rejected.
Retain the union of the other cells, transformed by D=1/a. All endpoints of
remaining cells remain required by the risk controller, even if an individual
endpoint test has rejected but the neighboring cell still needs it. Thus a
node can cease to be required only on its own test-crossing event. Empty set
means execute the one-second backup without resetting any risk budget; for
each node this continuation already lies inside the charged exceptional event.
Uncertified exclusion is not authorized; deterministic preflight must establish
the bounds. Frozen disables exclusions and keeps all node constraints forever.

Equation (12) is NOT unconditional coverage for the real correction counter.
For an exact-auxiliary cell-removal event, endpoint crossing bounds plus paid
kernel errors can be transferred through (8). In real memory the likelihood
may differ after coupling failure. The unified argument in section 8, not a
separate claim of 99.5% physical-parameter coverage, is essential.

## 7. Vector remaining-risk potentials

For each fixed node j let the one-second backup's expected auxiliary reward
be V_j(R,z,k)=c_j(R,z)+k*f_j(R,z). Below one second it equals (1). Otherwise

    f_j(R)=m1_j(1)/W,
    c_j(R)=m2_j(1)/(2W)+T_j,1*c_j(R-1)+J_j,1*f_j(R-1),   (13)

where T is mode transition and J[z,z']=E_z[K_new 1{Z'=z'}] from the same kernel.
Four coefficients are stored per remaining-time tick. Initialize

    B_j,0=theta-beta0-delta_model,j-delta_num,
    s_j,0=B_j,0-q_j,0*V_j(H), delta_num=0.001.             (14)

The common one-second backup passes: maximum initial V is about 0.07654 and
minimum initial slack about 0.01165. The domain/model were not narrowed.
For h=min(tau,R), each currently required node must satisfy

    Delta_j=q_j*(r_j,h+P_j,tau*V_j(R-h))-q_j*V_j(R)
           <=s_j*h/R,
    s'_j=s_j-Delta_j.                                   (15)

The future term is zero in an incomplete final interval. Choose the largest
period in the original U. Backup has Delta=0 by (13), so feasible continuation
is preserved and exact slack stays nonnegative. Observation updates q, not the
already spent risk. Define B_i^j=q_i^j*V_j(R_i)+s_i^j. Summing every Y branch,

    q_i^j*r_i+E_j[B_(i+1)^j | history_i]=B_i^j.           (16)

Stop this identity when node j is first removed or at mission end. Nonnegative
stopped terminal potential yields E_j sum(r before removal)<=B_j,0. Rare
histories can have conditional potential above epsilon; that does not violate
the overall probability requirement. Each j retains one constant generator
and its own q/slack. Intersecting action constraints is conservative but does
not silently replace the physical model by an adversarially reselected D.

Frozen updates the hidden mode and pending state from its own observations at
every node. It never uses likelihood scores as hidden D weights in the risk.
It retains the same beta reserve to isolate exclusion; this is not an optimum
among every conceivable robust controller with separately reallocated reserves.

## 8. One combined stopped-event argument

Fix node j. Couple physical and exact auxiliary evolution up to the first
repeated uncleared-word hit, and the exact and approximate auxiliary kernels
with row discrepancy at most e_j. Retaining only matched, unrepeated trajectories
produces a subkernel dominated by the full approximate auxiliary kernel.
Inductively, the surviving matched mass in history and full pending state is
no larger than the corresponding full auxiliary mass. Conditional loss in a
step is at most (1) plus the kernel discrepancy. Stop when j is removed.

This domination bounds the reward-weighted loss before removal by the full
auxiliary stopped reward sum. Removal costs at most beta0 by (12). Every first
loss or exclusion is charged once; the argument does not apply a TV bound to
an unbounded cumulative cost and does not normalize away absorbed probability.
Thus

    F_physical(a_j)
      <= E_aux,j sum(r before removal)+delta_model,j+beta0
      <= B_j,0+delta_num+delta_model,j+beta0=theta.        (17)

The log-test arithmetic guard is needed in beta0 as well as in control.
Terminal exposure has its reward but needs no extra observation kernel.
Equations (10) and (17) give the declared uniform whole-horizon bound. After
continuum transfer the exclusion allocation is exactly G*beta0=0.005. Model
and numerical errors are separate from Monte Carlo confidence intervals.

## 9. Conditional numerical realization

Assume IEEE binary64, nearest basic-operation rounding, and exp/expm1/log
within four ulp. No compiler/hardware or universal math-library certification
is claimed. certify.py encloses every one of 19008 coefficients using directed
60-digit Decimal operations, exact rational rate/quadrature nodes and literal
decimal physical parameters. Correctly rounded Decimal.exp is bracketed by
adjacent decimal numbers. Positive uniformization through 64 terms, an explicit
positive geometric tail bound and interval squaring enclose the idle CTMC.
Every structural zero is checked; every positive coefficient meets the relative
contract k0=1e-12. Full witnesses are regenerated and included in the archive.

Positive operators do not expand max/min componentwise relative distortion;
normalization preserves that ratio. All four probability coordinates are
positive after a reachable observation, with lower support derived from the
coefficient bounds. The next likelihood is bounded through their products;
-log ell<80, so probability-filter underflow is excluded. Pending moments are
bounded by mu_max=bH*P/2. Tiny dropped log-sum-exp terms have negligible total
absolute mass while the largest score is always zero.

For u=2^-53, gamma_m=m*u/(1-m*u), N=18000, Nb=3600, use

    Vmax=(H+1)*(mu_max*bH+bH^2/2)/W,
    Rsum=H*(mu_max*bH+bH^2*max(U)/2)/W,
    eta=expm1(4*N*(k0+gamma_128)),
    eV=8*(gamma_(512*Nb)+Nb*k0)*Vmax.

The ledger covers filtering by (2*N*Vmax+Rsum)*eta, value recursion by 2*N*eV,
action arithmetic by N*gamma_4096*(4*Vmax+2*Rsum)+N*1e-13, positive-kernel
guard by 8*N*k0, slack summation by gamma_(2*N)*(epsilon+Rsum+2*N*Vmax), and
slack comparisons by N*gamma_32*(epsilon+Rsum+2*N*Vmax). Absolute moment scales,
initial potential, subtraction in Delta and max(0,slack-Delta) are paid.
Coefficients c,f are stored directly, not recovered by subtracting neighboring V.
The computed total is below the allocated delta_num=0.001.

Scaled log scores require more than local log error. The explicit bound is

    e_log=4*N*(k0+gamma_128)+2*gamma_(4*N+256)*N*80.

It accounts for accumulated subtraction of score scales. Twice this bound is
below 0.001, so implemented rejection cannot precede the exact permitted test.
This declared arithmetic contract, the operation-count bounds and the actual
interval enclosures are separate review objects, not empirical residual claims.

## 10. Baselines, independent checks and boundaries

For exogenous Fixed/Precomputed schedules, use the accepted RES-003 first-passage
brackets: E[Q] upper and the conditional exactly-two-distinct-bits/chord lower.
Directed intervals evaluate all 12+144 schedules at all 33 nodes. G*max upper
certifies the continuum; one node lower above epsilon excludes a schedule from
the uniform class. Optima are Fixed 1 s/3600 passes and two-block 2/1 s/2700.
All 9 and 97 cheaper candidates are excluded; no general open-loop optimum.

The small physical oracle independently constructs a killed generator on
(mode, erroneous-word mask), chronological resets and actual correction counts,
without the auxiliary observation helper. Its physical mass is unnormalized.
The short toy learning/frozen policies coincide; that test is not sold as a
numerical learning-effect test. A separate complete adaptive likelihood tree,
all-branch budget checks, independent all-word event scanner, numeric witnesses
and full-scale paired simulations test the other interfaces.

Held-out uses five D values and 20000 missions each, six policies, own counters.
PA-DOM is the declared (10)->(9) adaptation with one pilot-selected setting for
the entire range. Its finite-point Monte Carlo evidence is not a uniform theorem.
Known-D has stronger information and different count coarsening/reserves; its
cost difference is not an isolated price of unknown D. The principal matched
contrast is learning versus frozen uncertainty, not count-disabled RES-003.

Martingale testing, Ville and Holder inequalities are not claimed as new
mathematical principles. The candidate result is their explicit integration
with endogenous counts, residual arrivals, one unknown constant generator and
the first-passage budget. No equal-risk dominance, global policy optimality,
unknown levels, drift, MCU, physical environment identification, energy result
or flight-hardware guarantee is asserted. RES-003 remains unchanged.
