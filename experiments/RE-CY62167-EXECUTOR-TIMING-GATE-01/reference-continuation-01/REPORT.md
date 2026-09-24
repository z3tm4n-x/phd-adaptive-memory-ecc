# RE-CY62167 executor timing — reference continuation 01

2026-09-16. Research Engineer. OWN RESULT, submitted to Orchestrator; independent
Scientific Review and acceptance have not occurred.

## Outcome

**CONDITIONAL PROJECT CERTIFICATE / PHYSICAL WCET NOT_ESTABLISHED.**

For the exact selected reference organization, unchanged 24-tick schedule and
explicitly assumed pre-H rate case, a sufficient model upper has positive slack:

    U_exec = 0.000962653442214173738773…
    epsilon_analysis - U_exec = +0.000037346557785826261227…

This is a constructive conditional result, not a repeat of Stage 0, not a
physical timing-gate PASS and not a claim that .001 is a project requirement.
The analytic domain is exactly PROOF.md, with all physical/implementation
conditions in TIMING.md. No excluding electrical contradiction was found in
the sourced pin/DC checks; absence of such a contradiction is not board proof.

| Question | Separate disposition |
| --- | --- |
| Timing under assigned implementation envelope | Conditional sufficient bound: latch→qualified fence <=160.5080004000 ns; physical WE end <=120.5055002750 ns after latch |
| Whole read/repair tube | <=240.5120006000 ns, including pre-latch operations, ERR-only writes and fence |
| Comparison with old exact Delta_star | Conditional pending bound is below the exact old boundary; NOT the decision criterion for the extended chronology |
| Start | Each word clean only at its own qualified preparation endpoint; subsequent age and pre-H risk are included. No global clean at t0 is asserted |
| No pending at t0 | Conditional full N-word load, fixed deadline, safe bus/fence/readiness; logical checks exercised; physical assurance remains conditional |
| Combined new model decision | U_exec<=.001 exactly; positive sufficient domain for r_pre, no universal sufficiency or necessary-limit claim |
| Physical timing/start/device | NOT_ESTABLISHED: routed min/max/hold, actual board/clock/load/power, trust and joint transfer evidence absent |

## Controlling inputs and implementation

Continue branch research/cy62167-executor-timing-gate-01 from
003c2346c4135b3d2f24dac0981e60cb2f179384. Additional controlling input is
d59de85eb46ae1fa254f3b936ce6fa64c28bcff0, not silently substituted as branch parent.
Preregistration/config/source commit:
2d349dc2cf5ba5007c589652bf760a9a7682a057. Delivery is its child; exact published
delivery SHA is supplied with this report, avoiding a circular self-hash.

Selected AC701 Rev2 / XC7A200T-2FBG676C / 3×CY62167GE30-45ZXI / 48-bit bus /
SEC-DED(39,32) and 2 MiB useful immutable data image are unchanged.
The source manifest distinguishes primary component facts, fixed design
requirements, added model assumptions and unknown physical transfer.

The executable witness implements packed-code conversion, one-domain enable,
fixed read/latch/decode/conditional-write/fence phases, ERR-only write,
uncorrectable suppression, preparation validity, hard/soft reset and read
arbitration. Clock/readiness/transfer qualification are explicit INTERNAL
environment/integration obligations, not extra ACK wires on asynchronous SRAM.
No application writes, stalls within scrub, phase adaptation or additional
controller policy have been introduced. The witness is not a board bitstream.

## Result basis

PROOF.md supplies an event inclusion and one pair-plus-service-tube upper.
Distinct pairs are bounded over per-word histories starting at their own
preparation endpoints. The all-hit tube event includes every reserved slot
and all 32 modeled bits; it protects against non-atomic read/commit chronology
without pretending the three chips make an instantaneous snapshot.

Clock envelope and block-edge counting give at most 301 potentially intersecting
tubes per word per 300-s rate block; no old duty=Delta/tau identity is reused.
Initial maximum gap is 107416921 ticks, exhaustively verified. Pre-H dependence
is explicit A+B*r_pre+C*r_pre^2. The named r_pre=max(frozen r) is ASSUMED,
not measured. The certified allowed endpoint is approximately
7.833153909485812e-7 per data bit per second. Coefficients, exact fractions,
component terms and root bracket are in bounds.json.

The old ideal-case constants and exact Delta_star are recovered separately
under their narrower original contract. The new bound is intentionally
coarser and is not forced to equal the earlier 31-other-bit pending formula.

## Verification actually executed

| Verification | Result / scope |
| --- | --- |
| Fixed-input identity | SHA256 frozen CSV matched; all 288 timestamps/scenario fields/normalization checked; no transport rerun |
| Independent numerical checker | PASS; Decimal95 vs Fraction, tolerance1e-70; no calculator import; all524288 first gaps and word spacing, root bracket, exact ideal boundary |
| Primary-source pin expansion | PASS; 73 unique nets/balls/J30 contacts, HR banks12/15/16, packing basis and straps |
| Python deterministic suite | 16 tests PASS; source-independent bit positions, all39 singleton and741 double masks for five images, clock/block edges, early initial contamination, reset/fence and inside-tube first-passage sentinel |
| Python compileall | PASS |
| RTL front-end | pyslang9.1.0: zero diagnostics for both production witness modules |
| Actual RTL slot simulation | Icarus13.0: 3955 vectors PASS, including clean, ERR-only, correction, double fault, immutable latch, prep, pending, missing trusted image, failed transfer, soft/hard reset |
| Integrated calendar/slot simulation | PASS: first5 preparation launches, 1024 fixed scrub slots with3069 saturated legal reads; explicit state injection at epoch boundary (not a full524288-write RTL run) |
| RTL mutation sentinels | Both rejected: direct bus→codeword and omitted ERR-only write compile but fail the same testbench |
| Routed timing / analog / hardware | NOT_RUN; no Vivado/board evidence claimed |

The independent checker shares the declared math and frozen inputs; it is
independent implementation verification, not an independent scientific review
or qualification of input rates. Digital SRAM stubs do not test analog AC,
hidden ECC or radiation transfer. Complete-array address/gap enumeration is
not mislabeled as a complete 24-h RTL trajectory.

Actual versions, command logs, duration and memory are in validation.json,
rtl_results.json and test_results.txt. Peak working set covers the validation
runner only, not native simulator children. Generated vectors/tool binaries/PDFs
remain in workspace tmp outside Git; hashes/URLs allow reconstruction.

## Conditions and limitations still required

1. Prove chosen FPGA implementation meets decode deadline, package I/O bounds,
   same-edge OE/latch minimum hold, clock skew and full min/max corner timing.
   No unconstrained XDC port or arbitrary multicycle exception can substitute.
2. Qualify real interconnect, three-chip loading, slew/noise, supply current,
   startup sequencing/ramp, 2.375..2.625 V rail, thermal limits and read/write
   bus turnaround. Board PG thresholds alone are insufficient.
3. Establish the absolute clock envelope including the additional jitter bound,
   correct epoch-to-UTC anchoring and its admissible coupling to arrivals.
4. Bind actual immutable image/hash and trusted timely source; establish N-write
   completion/drain/ready and invalidation on failures. The zero-image test is
   not data-independence evidence.
5. Supply one future joint physical-transfer inclusion/coverage budget covering
   hidden inner ECC/parity, revision/mapping/registration issues, mixed paths,
   controller/clock violations, preparation trust and r_pre qualification.
   The available numeric slack is not an estimate of that joint probability.

These are explicit implementation/transfer conditions, not unresolved changes
to the fixed scientific question. No full-device claim, new RES/HYP, new
transport, adaptation claim or hardware build is made. Issue15 stays open.
Whether this conditional certificate merits the next joint-contract effort
is for Orchestrator after separate Scientific Reviewer review.

## Deviations, development failures and preservation

No change to topology, period, slot subdivision, frozen rates/seeds, H, W32_seq,
DREG or epsilon_analysis. Only the authorized new subdirectory is committed;
the five Stage-0 files remain byte-identical (before/after hashes in MANIFEST).
Main, DEC004, concept, previous RE/SR and chapter4 were not edited.

Development issues were resolved rather than hidden:

- PDF text needed UTF-8; Poppler emitted ancillary Unicode-map warnings but
  relevant pin/timing/DC pages rendered and were visually checked.
- pyslang DLL load required approved unsandboxed execution; absolute Cyrillic
  filename handling failed, resolved with ASCII relative filenames.
- Icarus upstream release had no Windows asset; MSYS2 portable packages were
  verified by published SHA256. One download timed out and was retried; child
  compiler DLL discovery required process-local PATH.
- Two integrated-test observations initially sampled before registered ACK
  propagation/clear; monitors now wait the appropriate base-clock edge.
  Accepted work is allowed to ACK at a soft-reset drain fence, as contracted.
  No scientific assumption or slot phase was changed to make tests pass.
- Icarus warns that always_comb constant-select sensitivity is widened to
  all source bits; simulations passed. It is not a synthesis/timing diagnostic.

Four unrelated old CSVs appear modified in ordinary git status because their
committed CRLF bytes conflict with current eol=lf attributes. Their raw bytes
equal their HEAD blobs; they are neither edited nor staged. This report does
not falsely claim a globally clean ordinary status. The delivered subdirectory
is clean after commit, and MANIFEST records the unchanged raw hashes.
