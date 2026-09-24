# Pin, electrical and timing contract

SOURCE identifiers/actual-byte hashes are in source_manifest.json. Primary PDF
pinout and timing/DC pages were visually checked, not inferred from search
snippets. DESIGN requirements below are not datasheet guarantees for our board.

## Pin/address/packing check

pinmap.json contains all 73 point-to-point net bindings, J30 contact, FPGA ball,
HR bank, SRAM TSOP-II pin and UG952 page. make_pins.py independently joins UG952
Table 1-26 with AMD's xc7a200tfbg676 package file; all assigned banks are
12/15/16, supplied by VCCO_VADJ (UG952 p14). No duplicate ball, contact, net or
port; no conflicting onboard functional net is listed for these selected FMC
signals. This is a documented-net check, not PCB-layout verification.
reference_pins.xdc is a physical-port constraint fragment, not a complete
bitstream/XDC with invented front-end pin assignments.

A[18:0]=w, A19=0 on all three chips. The full 2^19-word address domain is used
once per preparation and once per period. Bus P0..15=M0.IO0..15,
P16..31=M1.IO0..15, P32..38=M2.IO0..6. Logical code positions for P32..38 are
1,2,4,8,16,32,39. P0..31 occupy the other positions in 1..38 in ascending order.
P39..47 are zero padding on writes, ignored on decode, not modeled data.
The 39-basis-bit permutation test rejects direct P[38:0] to the legacy decoder.
Capacity: 2 MiB useful / 3 MiB addressed / 6 MiB total installed SRAM.

Straps and supply pins are enumerated in pinmap.json (CY Figure5 p6).
Unused FMC signals: do not drive unassigned nets; retain AC701 board management,
presence/power-good and JTAG chain requirements (UG952 pp58–65,83).
This witness has no fabricated bitstream/programming or complete FMC-module
management implementation. A module must correctly declare presence, power
and JTAG bypass/chain, avoid contention on management nets, and qualify ready
before memory access. These are integration obligations, not addressed GPIO.

## Electrical scope and unresolved physical evidence

| Item | Source / result / required scope |
| --- | --- |
| SRAM | CY62167GE30-45ZXI, Rev*F, 2.2–3.6 V, industrial -40..85 C (pp1,7,16) |
| FPGA | AC701 Rev2 XC7A200T-2FBG676C; commercial junction 0..85 C, board ambient 0..45 C separately (UG952 pp7,91; DS181 pp2–3) |
| Common VADJ rail | DESIGN 2.375..2.625 V at actual pins, including ripple/droop; within SRAM low-voltage corner and FPGA 2.5 V ±5% |
| FPGA→SRAM DC | DS181 Table8: VOH>=VCCO-.4, VOL<=.4; CY p7 needs VIH>=1.8,VIL<=.6. Worst high margin .175 V, low .2 V before noise/ground offset |
| SRAM→FPGA DC | CY low-voltage VOH>=2.0,VOL<=.4 at ±.1 mA; DS181 LVCMOS25 VIH>=1.7,VIL<=.7: .3 V margins |
| Loads/leakage | FPGA input leakage max ±15 uA (DS181 p3); CY input ±1 uA. Disable input pulls/termination, bound total DC load <100 uA for SRAM output claim |
| AC load | CY p8 test output load 30 pF; CIN/COUT 10 pF at stated 25 C/1 MHz test, not a universal interconnect model. FPGA pad input cap 8 pF excludes package. Common address/control drive three SRAM inputs plus board traces |
| Slew/threshold | CY p10 note28: rise/fall <=3 ns and low-voltage timing reference VCC/2; actual load, crossings, skew, overshoot and ringing must preserve the stated budgets |
| Power-up | CY p7 note13 assumes a 100-us ramp from zero to Vmin and a 200-us wait after operational stabilization. It does not specify an allowable ramp interval; actual startup must meet/qualify this assumption, plus FPGA core/aux/I/O sequencing and ramps (DS181 pp2–9) |
| Power-good | UG952 p65 thresholds include off at 2.125 V; this is below SRAM Vmin. PG alone does NOT establish the tighter qualified rail range |
| Clock | UG952 p26 U51 200 MHz ±50 ppm. Additional all-interval ±.5 ns envelope is DESIGN, not quoted jitter performance |

No nominal-voltage equality is used as proof of full AC compatibility.
Pin/core supplies, current budget for three SRAMs, decoupling and sequencing,
unpowered-I/O isolation, temperature and noise margins require board qualification.
All these are explicit remaining physical conditions; no fabrication is authorized.

## Time envelope and reservation chronology

For d service ticks define l(d)=10*d/1.00005-.5 ns and
u(d)=10*d/.99995+.5 ns. The single 200-MHz domain advances FSMs by enable every
two clocks. No divided logic clock is introduced.

DESIGN bounds: launch edge to FPGA output package 0..8 ns; one-way board/FMC/
module 0..2 ns; FPGA input package to latch including setup <=5 ns.
For two different signal paths use the full 10-ns worst skew, not cancellation.
These bounds apply to all three chips, both polarities, PVT/load corners.

| Relative tick | Contract |
| ---: | --- |
| 0 | Fixed address, CE active, OE active for read, WE inactive, FPGA DQ high-Z |
| 8 | Capture all DQ and ERR, raise OE |
| 10 | Registered ECC decision and immutable corrected 48-bit write image |
| 12 | Drive image only for selected write; prep always writes trusted image |
| 13 | WE falls |
| 19 | WE rises (intended write-terminating edge) |
| 21 | Release FPGA data after hold |
| 24 | Fence/slot end, conditional completion, address may next change |

Write iff (corrected OR any latched ERR) AND NOT uncorrectable. Application
reads never write; prep never reads uninitialized SRAM. Fault is sticky and
cannot issue success for its slot. Unknown/invalid transfer cannot become
success merely because a counter reaches 24.

| Check | Conservative available vs source requirement |
| --- | --- |
| Read valid at latch | l(8)=79.4960 ns >=8+2+max(45,45,22,45)+2+5=62 ns |
| Decode/register | l(2)=19.4990 ns budget; logic/setup/clock skew must be proved by STA, not measured here |
| OE high→FPGA drive | l(4)-10=29.4980 ns >= tHZOE max18 ns |
| WE low pulse | l(6)-10=49.4970 ns >= tPWE min35 ns |
| Data stable→WE high | l(7)-10=59.4965 ns >= tSD min25 ns |
| WE high→data release | l(2)-10=9.4990 ns >= tHD min0 |
| Address/CE valid→WE high | l(19)-10=179.4905 ns >= tAW/tSCE min35 |
| Address→WE low | l(13)-10=119.4935 ns >= tSA min0 |
| WE high→address/CE change | l(5)-10=39.4975 ns >= tHA min0 |
| Read/write cycle duration | consecutive starts >=24 ticks; l(24)-10=229.4880 ns >= tRC/tWC min45 |
| Write end before fence | u(19)+10=200.5095 ns < l(24)=239.4880 ns |

Read latch hold needs a separate minimum-path STA check: OE is raised on the
capture edge and tHZOE is a MAX, not a guaranteed minimum data hold. Address
stays stable, so tOHA=10 ns does not by itself cover OE disable. Require the
minimum OE-disable/output-invalid propagation versus input latch hold to
close, or report this implementation condition unmet. No zero-minimum budget
is quietly converted into positive hold evidence.

Remaining CY p10 lines/notes explicitly accounted for:

- tDBE max45 is included in the read max; BLE/BHE strapped active and tBW min35
  trivially satisfied by the established active byte enables before write end.
- tOHA min10 covers address-change read hold only; not a substitute for the
  OE/latch check above.
- tLZOE min5, tLZCE min10, tLZBE min5: FPGA is already high-Z when reads start;
  earliest SRAM drive cannot contend. FPGA releases at21 before next start>=24.
- tHZCE/tHZBE max18: OE has already disabled output; CE/BE do not terminate our
  write early. CE rises at24 after WE high and all holds; BE stays active.
- tHZWE max18 and tLZWE min10: OE is HIGH throughout write and turnaround,
  so no simultaneous SRAM drive. Note34's tHZWE+tSD constraint is for OE-LOW
  write cycle1; this is OE-HIGH WE-controlled cycle5, Figure14 (p14).
- tPU min0/tPD max45 concern power/current transition, not qualified write ACK.
  Do not power-cycle/deselect mid-active write or treat standby as reset.
- Note29 describes same-device high/low-Z ordering; our proof uses separated
  max/min budgets instead of presuming cross-chip matching.
- Notes30–32 distinguish guaranteed characterization/design values and Hi-Z
  measurement. We require the actual loading/corner conditions, not extra tests
  by implication. Note33 write overlap: WE alone ends the write; data/setup/
  hold refer to that earliest terminating edge, address/CE/BE remain valid.

ERR is sampled like DQ, using tAA/tACE/tDOE at p10; p15 specifies corrected-read
flag and high-Z behavior, not a physical error counter or write acknowledgment.
No-automatic-write-back note2 motivates the ERR-only path.

## Pending, tube and completion

From latch8 to latest physical WE-end19: u(11)+10=120.5055002750 ns.
From latch8 to the qualified internal fence24:
Delta_pending<=u(16)=160.5080004000 ns.
All read/repair influences conservatively lie in [start0,fence24]:
D<=u(24)=240.5120006000 ns. Operations before latch are thus explicitly paid.

The numerical inequality Delta_pending<Delta_star holds exactly for these
conditional bounds, but is only a control: the new model decision uses U_exec.
SRAM has no external ACK; fence success is valid ONLY if these AC conditions,
logic correctness and transfer/readiness qualifications hold. The witness's
qualified/transfer_ok inputs express that obligation; they are not physical
signals available from SRAM nor a proof that an undetected failure is absent.

## Schedule/start/read/reset conditions

Reservations remain floor(w*100000000/524288)+k*100000000 ticks. Minimum spacing
190 ticks (191 on the remainder) exceeds 24; last-to-next-period gap is191.
Scrub reserves exactly 12.582912% of nominal tick time. Three chips and ECC do
not make this a free memory system. App accepts at most one read each48 ticks,
one outstanding, 24-tick reservation, and rejects starts crossing the next scrub.
No retry/backpressure/CDC/software is inside a scrub reservation.

Prep requires N*24=12582912 ticks; remaining lead before t0 is7417088 ticks.
Its worst span <=.200010001000025 s. Each sigma_w is separately accounted in
PROOF.md; no global clean assertion at t0. Trusted uint32 zero image used by
tests has 2097152 data bytes; its hash is in validation.json. This is not a
physical data-independence experiment. Production immutable image/hash and
source availability must be bound before a real epoch.

At t0 require all N qualified full-word writes completed, no outstanding work,
safe bus, qualified supply/clock, no fault and fixed phase. Missing image,
missed slot, failed commit or readiness invalidates, never delays epoch silently.
Soft reset forbids new requests and drains/fences accepted work. Hard reset or
loss of power/clock invalidates the epoch certificate; a reset cannot assert
clean memory. Controller corruption, fault detection completeness and reset
electrical behavior belong to future transfer evidence.
