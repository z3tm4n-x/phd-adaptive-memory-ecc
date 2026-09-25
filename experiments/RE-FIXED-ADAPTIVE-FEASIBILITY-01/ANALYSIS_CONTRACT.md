# Analysis contract fixed before verification

Task: RE-FIXED-ADAPTIVE-FEASIBILITY-01. Execution base `59603d231b923ee7426056cb62779a5ad16c8413`.

## Evidence status

SOURCE: ESA Common DPU slides 14--16 give 4/8/16/32 MiB SRAM configurations, 32 data + 7 EDAC bits, an SRAM SEU error-rate figure 7.3e-7 errors/bit-day, and 50 MHz prototype timings with one wait state at 4 MiB and two at 32 MiB. GR712RC UM 2.17 section 5.4 gives two data cycles plus 0--3 wait states for SRAM reads and minimum three cycles plus wait states for writes. GRLIB-AN-0004 section 3 states that a correctable access is corrected on the bus and that hardware MEMSCRUB uses a locked read/write cycle when a correctable error is found. ECSS-Q-ST-60-15C Rev.1 section 5.3 requires SEE consequences to be assessed against mission specifications; it supplies no universal numeric allocation used here.

ASSUMPTION: the ESA scalar error-rate applies uniformly to all 39 protected bit cells. The normalized temporal shape of the already recorded 2021--2025 project row is transferred to this scalar mean without claiming physical calibration to JUICE. The 8/16 MiB service timing uses the slower 32 MiB timing. The 2 MiB case is control only and borrows 4 MiB timing.

UNKNOWN: exact flight workload, exact mission allocation for E_cap, exact relation of E_cap to system failure, future-environment envelope beyond the transferred row, hardware WCET and actual write fraction under conditional-write scrubbing.

## Level I model and fixed lower bound

For W codewords of n=39 bits, each array event has a uniform word and bit mark. For a fixed sequential scan period tau, each word is checked once per tau. In a constant-rate hour, irrespective of scan phase, each word has at least floor(3600/tau)-1 complete inter-check intervals lying wholly within the hour. If an interval has word-arrival mean lambda, the event "exactly two arrivals on distinct bits" has probability exp(-lambda)*lambda^2/2*(n-1)/n and is a subset of E_cap. Independence of split Poisson word processes and disjoint intervals gives a phase-independent lower bound on F_A. A second Cauchy lower bound using the total mean and an upper bound on interval count covers long tau. The maximum of the two bounds is used. A Fixed policy is proved insufficient at a resource budget B only if every tau compatible with B has F_lower(tau)>epsilon. Read time alone is used as the Fixed resource lower bound, so optional writes cannot make Fixed look worse artificially.

## Level I causal witness

The witness receives only the completed previous-hour external rate estimate. It scans continuously at r(t)=nu_hat(t)/C full-array traversals per hour; no current or future hour is used. For every inter-check interval I, integral_I r dt = 1. Cauchy gives (integral_I nu dt)^2 <= integral_I nu^2/r dt. Therefore

F_A <= (n-1)/(2 n W) * C * integral(nu^2/nu_hat) dt + delta_RMW.

The recorded lag-1 shape factor eta=(integral nu_hat)(integral nu^2/nu_hat)/(integral nu)^2 is reused. Since the final sample is not required, integral nu_hat is bounded below by integral nu + nu_0 - nu_max. C is chosen so the analytical pair bound consumes 95% of epsilon. The read-to-logical-completion contribution is bounded separately by (integral nu dt)*nu_max*Delta/(3600 W), with Delta=max(read,write). No whole-memory reset is inserted at hour boundaries.

For hard resource admission, every visited word is charged read+write even though the target semantics writes only corrected words. Thus the resource result is conservative with respect to conditional-write savings. A scrub word may hold the interface for at most read+write. The 1 s peak-window utilization is computed from the largest delayed estimate. The application delay bound is a declared research contract, not a sourced flight requirement.

## Level II

The gate opens only after a primary 4/8/16/32 MiB Level-I witness is saved. Strong Precomputed may use only preparation-time information, not the realized verification trajectory. The old simple counter policy may be used only as a diagnostic starting point; its old single-seed pass status is not imported as a new guarantee. RES-003 is admitted to an equal comparison only if its stochastic law, full 39-bit word, horizon and conditional-write execution can be transferred without changing the scientific model. Otherwise the exact incompatibility is reported instead of scoring it as a loss.

A shortened binary BCH candidate (44,32,d>=5) is checked as a separate architecture variant. It is not a drop-in claim about the documented 39-bit SRAM; the purpose is to test whether stronger ECC can erase the SEC-DED adaptation need.

## Stop rules

If no primary documented Level-I region is found, Level II stops and no additional model complexity is added. If Level I is positive, Level II stops at the first method in the ordered set {admissible Precomputed, simple external lag-1 contour, counter-only simple, RES-003} that has an established full-contract witness; later methods are still dispositioned but are not promoted by default. RES-004 is never executed in this task.
