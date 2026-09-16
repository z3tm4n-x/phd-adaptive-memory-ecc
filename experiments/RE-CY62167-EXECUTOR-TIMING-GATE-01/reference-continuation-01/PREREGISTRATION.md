# Preregistration — reference continuation 01

Base 003c2346c4135b3d2f24dac0981e60cb2f179384; additional controlling input
d59de85eb46ae1fa254f3b936ce6fa64c28bcff0. Preserve Stage-0 bytes and ancestry.
This lock precedes calculation of U_exec and implementation tests.

Use exactly the selected AC701 / three GE30 / 48-bit organization and 24-tick
schedule. No slot subdivision change is planned. No phase/outcome-dependent
shift, no change of H/r/epsilon or routing search. Zero image is only a test
input, never proof of data independence. Clock/board/I/O bounds remain conditions.

## Predeclared proof route and acceptance

For each deterministic clock trajectory satisfying the stated interval envelope,
pay the probability of any data-bit arrival in every preparation and scrub
service tube (even clean or ERR-only). Each tube starts at its reservation and
ends at tick 24. Prove pin timing completes by that deadline conditionally.
Outside this bad event and the future physical transfer violations, singletons
are repaired and clean/ERR-only writes retain a clean image at every tube end.
Bound distinct pairs in intervals between these clean endpoints, starting at
each word's own preparation completion. Include pre-t0 exposure and unsafe t0.

Use Cauchy-Schwarz with the largest initial/periodic gap, exact CSV integrals,
and explicit pre-H rate upper. Bound the number of tubes intersecting each
300-second block from the minimum period and maximum tube duration; no old
duty identity. Overcount boundary tubes rather than omit them.
Show constant + linear + quadratic dependence on r_pre, and a certified
bracket for its permitted maximum if the upper can pass. Uniform deterministic
clock bounds are not an unqualified claim for radiation-dependent time changes.

Separate pending duration, full tube, initial exposure, clock/block count penalty,
U_exec and signed slack. Recover the previous ideal case with its own narrower
31-bit pending-event argument; do not force equality with the coarser any-hit
tube theorem. Positive iff the exact rational upper <= 0.001 under all named
model and implementation conditions; never label physical WCET established.
If upper fails, distinguish certificate failure from an excluding lower.

## Falsification and delivery

Check data/parity permutation, all single/double error masks, ERR-only and clean
branches, timing minima/maxima/skew, inside-tube arrival, preparation-age failure,
block-edge/ppm counts, saturation of the allowed application reads, no scrub
phase movement, pending/reset/failed completion, source and preserved-byte hashes.
Independent checker must not import the main numerical calculator or obtain
expected values from it. Shared source/config/model assumptions disclosed.

Provide mathematical proof, rational calculation, source/pin/packing/timing
tables, minimal RTL/XDC and bounded executable tests. If a required tool is
unavailable, state NOT_RUN, retain a partial result and its exact unmet gate.
No fabricated STA or hardware execution. Source retrieval failures are recorded.
No joint coverage/transport/MC, device or mission claims, no new RES, no Issue close.
