"""Check the three observation contracts using the accepted #448 and #453 ledgers."""

import json
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path

HERE = Path(__file__).resolve().parent
GE = HERE.parent / "t186-advisor-ge30-20261110"
EPS = HERE.parent / "t186-ge30-epsilon"
NS = F(1, 10**9)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rounded(value, digits, *, up):
    scale = 10**digits
    units = (ceil if up else floor)(value * scale)
    integer, decimal = divmod(abs(units), scale)
    return f"{'-' if units < 0 else ''}{integer}.{decimal:0{digits}d}"


def steps(reports, required, slow):
    """A report at the end of a common cell controls only the next cell."""
    quiet = 0
    for report in reports:
        yield slow if quiet == required else 1
        quiet = min(required, quiet + 1) if report == "zero" else 0


def check_recovery(required, slow):
    prefix = ["zero"] * required
    for count in (1, 3):
        reports = prefix + ["invalid"] * count + ["zero"] * (required + 1)
        chosen = list(steps(reports, required, slow))
        assert chosen == [1] * required + [slow] + [1] * (count - 1 + required) + [slow]
    assert set(steps(["invalid"] * (required + 2), required, slow)) == {1}
    for reset in ("invalid", "corrected"):
        reports = ["zero"] * (required - 1) + [reset, "zero"]
        assert set(steps(reports, required, slow)) == {1}


def nominal_continuous_reads(cal):
    """Charge all word operations starting in [0,T), including the final partial pass."""
    mission_ns = cal["mission_s"] * 10**9
    full, tail = divmod(mission_ns, cal["L_ns"])
    frames, tail_phase = divmod(tail, cal["frame_ns"])
    offsets = cal["word_slots_ns"]
    tail_reads = len(offsets) * frames + sum(offset < tail_phase for offset in offsets)
    total = full * cal["W"] + tail_reads
    # Count visits independently for each phase of a complete scan.
    visits = 0
    for rank in range(cal["W"]):
        frame, slot = divmod(rank, len(offsets))
        phase = frame * cal["frame_ns"] + offsets[slot]
        visits += 1 + (mission_ns - 1 - phase) // cal["L_ns"]
    assert total == visits
    return full, tail_reads, total


def main():
    cal = read_json(GE / "calendar.json")
    ledger = read_json(GE / "bounds.json")
    epsilon_results = read_json(EPS / "result.json")
    fixed = epsilon_results["rows"]["0.001"]
    rule = ledger["binary_split"]["32"]
    required, slow = rule["quiet_cells"], rule["frame_multiple"]
    assert (required, slow) == (205, 32) and fixed["fixed_candidate"]["k"] == 1
    check_recovery(required, slow)

    mission = F(cal["mission_s"])
    scale_min, scale_max = F(cal["xi_minus"]), F(cal["xi_plus"])
    edge = 2 * F(cal["J_ns"]) * NS
    aperture = F(cal["aperture_upper_ns"]) * NS
    cell = slow * cal["L_ns"] * NS
    frames = ceil((mission + edge + aperture) / (cal["frame_ns"] * NS * scale_min)) + 2
    assert frames * len(cal["word_slots_ns"]) == ledger["read_hard_cap"]
    start, end = cal["management_ns"]
    reserve = frames * ((end - start) * NS * scale_max + edge)

    # Issued upper costs and lower allowance; keep their rounding directions.
    base = F(epsilon_results["adaptive"]["known_price_upper_at_I0"]["seconds"])
    coefficient = F(epsilon_results["adaptive"]["seconds_per_invalid_upper"])
    total_budget = F(fixed["sufficient_X_plus_cI_budget_s_floor"])
    allowance = total_budget - reserve
    max_cells = floor(allowance / coefficient)
    slack = allowance - max_cells * coefficient
    half_class = F(ledger["exact_two_word_class"]["half_lower_s"]["exact"])
    assert max_cells == 216540 and 0 <= slack < coefficient
    assert base + reserve + coefficient * max_cells <= half_class
    assert base + reserve + coefficient * (max_cells + 1) > half_class

    full, tail_reads, total = nominal_continuous_reads(cal)
    nominal_reads = total * cal["read_port_ns"] * NS
    fixed_upper = F(fixed["fixed_candidate"]["known_price_upper"]["seconds"])
    assert nominal_reads > (fixed_upper + reserve) / 2
    print("cell, clean recovery, recovery from first of three invalid closes (nominal s):",
          *(rounded(v, 7, up=True) for v in (cell, required * cell, (required + 2) * cell)))
    print("single-reset time allowance upper (s):", rounded((required + 1) * (cell * scale_max + edge), 9, up=True))
    print("Q upper, full/recognized/persistent:",
          epsilon_results["adaptive"]["Q_upper"], epsilon_results["adaptive"]["Q_upper"],
          fixed["fixed_candidate"]["Q_upper"])
    print("frames:", frames, "reserve upper (s):", rounded(reserve, 6, up=True))
    print("outside + reset budget lower (s):", rounded(allowance, 6, up=False))
    print("I cutoff:", rounded(allowance / coefficient, 9, up=False), "integer:", max_cells)
    print("outside budget at cutoff and +1 (s):",
          rounded(slack, 6, up=False), rounded(slack - coefficient, 6, up=False))
    for name, cost in (("I=0 with reserve", base + reserve),
                       ("I=216540 with reserve", base + reserve + coefficient * max_cells),
                       ("all invalid: fixed L with reserve", fixed_upper + reserve)):
        print(name, "upper:", rounded(cost, 3, up=True), "s,", rounded(100 * cost / mission, 6, up=True), "% of T")
    print("nominal continuous passes:", full, "full +", tail_reads, "words, total reads:", total)
    print("nominal read-only port (s):", nominal_reads, "outward decimal lower:", rounded(nominal_reads, 6, up=False))
    print("half fixed upper incl. reserve (s):", rounded((fixed_upper + reserve) / 2, 3, up=True))
    print("fixed extra outside reserve below this excludes 2x (s):",
          rounded(2 * nominal_reads - fixed_upper - reserve, 3, up=False))


if __name__ == "__main__":
    main()
