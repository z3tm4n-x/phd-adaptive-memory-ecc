"""Exact structural checks for t196-public-reserve-20261029.md.

The calendar and budgets below are synthetic proof checks, not a mission
input, a first_probe calculation, an execution model, or a numerical Q.
Only the standard library is used. No accepted result files are modified.
"""

from fractions import Fraction as F
from itertools import combinations, product
import json


def covering_cells(apertures, end):
    cells = [(F(0), min(end, apertures[0][1]))]
    for i, (start, _) in enumerate(apertures):
        stop = apertures[i + 1][1] if i + 1 < len(apertures) else end
        stop = min(stop, end)
        if start < stop:
            cells.append((start, stop))
    return cells


def first_mark_survives(birth, next_birth, execution):
    # Weak E removes births older than its actual start at its release.
    # Late births are retained, including a mark already pending at a read.
    return not any(
        birth < start and release < next_birth
        for start, release in execution
    )


def check_pair_cover():
    apertures = [(F(2), F(5, 2)), (F(5), F(11, 2)), (F(8), F(17, 2))]
    variants = [
        [(a, a), (a, b), ((a + b) / 2, (a + b) / 2), ((a + b) / 2, b)]
        for a, b in apertures
    ]
    horizons = [F(1), F(9, 4), F(5, 2), F(21, 4), F(10)]
    comparisons = witnesses = old_hits = 0
    for end in horizons:
        cells = covering_cells(apertures, end)
        # Odd eighths avoid an artificial convention for simultaneous events.
        births = [F(j, 8) for j in range(1, 80, 2) if F(j, 8) < end]
        for execution in product(*variants):
            for first, second in combinations(births, 2):
                comparisons += 1
                if first_mark_survives(first, second, execution):
                    witnesses += 1
                    assert any(a <= first < second <= b for a, b in cells)
            # An initial mark is cleared by the first completed main E.
            for hit in births:
                if all(release > hit for _, release in execution):
                    old_hits += 1
                    assert hit < min(F(5, 2), end)
    assert comparisons > witnesses > 0 and old_hits > 0
    return {
        "pair_execution_comparisons": comparisons,
        "covered_weak_E_witnesses": witnesses,
        "covered_initial_mark_hits": old_hits,
        "terminal_positions": len(horizons),
    }


PROFILE = [
    (F(0), F(1), F(2)),
    (F(1), F(3), F(1)),
    (F(3), F(4), F(3)),
    (F(4), F(7), F(0)),
    (F(7), F(10), F(2)),
]


def integral(left, right, power):
    return sum(
        max(F(0), min(right, b) - max(left, a)) * value**power
        for a, b, value in PROFILE
    )


def ceil_fraction(x):
    return -(-x.numerator // x.denominator)


def check_integral_cover():
    apertures = [(F(2), F(5, 2)), (F(5), F(11, 2)), (F(8), F(17, 2))]
    count = 0
    for end in [F(1), F(9, 4), F(5, 2), F(21, 4), F(10)]:
        cells = covering_cells(apertures, end)
        mass_squares = sum(integral(a, b, 1) ** 2 for a, b in cells)
        repeated_energy = sum(integral(a, b, 2) for a, b in cells)
        energy = integral(F(0), end, 2)
        overlaps = sum(integral(a, min(b, end), 2) for a, b in apertures if a < end)
        assert repeated_energy == energy + overlaps
        maximum_length = F(7, 2)  # period 3 plus outer E width 1/2
        assert all(b - a <= maximum_length for a, b in cells)
        assert mass_squares <= maximum_length * repeated_energy
        number_bound = ceil_fraction(end / 3) + 2
        peak_energy_overlap = 3**2 * F(1, 2) * number_bound
        assert overlaps <= peak_energy_overlap
        assert mass_squares <= maximum_length * (energy + peak_energy_overlap)
        count += 1
    return {"exact_integral_and_multiplicity_cases": count}


def residual_cap(mean, eta, words):
    assert mean >= 0 and 0 < eta < 1 and words > 0
    factorial_moment = mean
    for q in range(words):
        if factorial_moment <= eta:
            return q
        factorial_moment *= mean / (q + 2)
    return words


def check_quantile():
    count = capped = 0
    for mean, eta, words in product(
        [F(0), F(1, 4), F(3), F(10)],
        [F(1, 100), F(1, 10_000)],
        [2, 100],
    ):
        cap = residual_cap(mean, eta, words)
        # Directly recompute the factorial moment, independently of recurrence.
        if cap == words:
            capped += 1
        else:
            factorial = 1
            for j in range(1, cap + 2):
                factorial *= j
            assert mean ** (cap + 1) <= eta * factorial
            for smaller in range(cap):
                factorial_smaller = 1
                for j in range(1, smaller + 2):
                    factorial_smaller *= j
                assert mean ** (smaller + 1) > eta * factorial_smaller
        assert 0 <= cap <= words
        count += 1
    assert residual_cap(F(0), F(1, 100), 100) == 0
    assert capped > 0
    return {"factorial_quantile_cases": count, "deterministic_W_caps": capped}


def check_ledger():
    epsilon, delta, zeta = F(1, 10), F(1, 100), F(1, 100)
    initial_reserve = F(1, 50)
    local_price, next_reserve = F(1, 100), F(3, 200)
    debit = local_price + next_reserve
    initial_credit = epsilon - delta - zeta - initial_reserve
    max_attempts = 3
    # phase, j, free credit, all debits, executed action charges,
    # activated new reserve charges. No hidden K, survival or environment.
    initial = ("base", 0, initial_credit, F(0), F(0), F(0))
    frontier = {initial}
    seen = set()
    labels = set()
    transitions = 0
    two_executed = False
    for _ in range(11):
        following = set()
        for state in frontier:
            phase, j, credit, paid, used_local, used_reserve = state
            seen.add(state)
            assert credit >= 0 and paid + credit == initial_credit
            assert used_local + used_reserve <= paid
            assert delta + zeta + initial_reserve + used_local + used_reserve <= epsilon
            assert 0 <= j <= max_attempts
            if used_local == 2 * local_price:
                two_executed = True

            def add(label, new_phase, new_j=j, new_credit=credit,
                    new_paid=paid, new_local=used_local, new_reserve=used_reserve):
                nonlocal transitions
                labels.add(label)
                transitions += 1
                following.add((new_phase, new_j, new_credit, new_paid, new_local, new_reserve))

            if phase == "end":
                continue
            add("terminal_partial_no_refund", "end")
            if phase == "base":
                add("base_0", "base")
                add("restore_base_no_reset", "base")
                if j < max_attempts:
                    add("register_before_probe_0", "probe", new_j=j + 1)
            elif phase == "probe":
                for label in ["valid_decline_0", "invalid_0", "positive_C_0",
                              "loss_0", "restore_sticky_invalid_0", "late_before_debit_0"]:
                    add(label, "base")
                if debit <= credit:
                    add("authorized_1", "extended", new_credit=credit - debit,
                        new_paid=paid + debit, new_local=used_local + local_price)
                    add("late_after_debit_0_no_refund", "base", new_credit=credit - debit,
                        new_paid=paid + debit)
                else:
                    add("insufficient_credit_0", "base")
            else:
                assert phase == "extended"
                for label in ["finish_1_valid", "finish_1_invalid", "finish_1_loss_restore"]:
                    add(label, "base", new_reserve=used_reserve + next_reserve)
        frontier = following
    assert two_executed
    assert "late_after_debit_0_no_refund" in labels
    assert "finish_1_invalid" in labels and "restore_sticky_invalid_0" in labels
    assert "insufficient_credit_0" in labels
    assert any(state[1] == max_attempts and state[0] == "base" for state in seen)
    return {
        "public_states": len(seen),
        "branch_transitions": transitions,
        "branch_kinds": sorted(labels),
        "two_extensions_without_budget_reset": two_executed,
    }


def check_terminal_and_quota():
    # The finite-horizon reserve is explicitly zero at the terminal time,
    # rather than evaluating ceil(0 / period) + 2 as a spurious future cost.
    def future_mass_cap(remaining, total_mass, residual_peak):
        return min(total_mass, residual_peak * remaining)

    assert future_mass_cap(F(0), F(3), F(2)) == 0
    assert future_mass_cap(F(10), F(3), F(2)) == 3
    assert future_mass_cap(F(1), F(3), F(2)) == 2
    # Nonuniform p/r, short tail and a finite total quota: direct exact
    # integration verifies the secant used in the new suffix reserve.
    cells = [
        (F(1), F(1), F(2)),
        (F(2), F(3), F(0)),
        (F(1), F(2), F(1)),
    ]
    total_mass, residual_peak, p_peak = F(3), F(2), F(3)
    actual = sum(length * (p + r) ** 2 for length, p, r in cells)
    ip = sum(length * p**2 for length, p, _ in cells)
    mass = sum(length * r for length, _, r in cells)
    duration = sum(length for length, _, _ in cells)
    assert mass == total_mass
    bound = ip + (2 * p_peak + residual_peak) * future_mass_cap(
        duration, total_mass, residual_peak
    )
    assert actual <= bound
    assert bound < duration * (p_peak + residual_peak) ** 2
    return {"quota_and_terminal_checks": 5}


def main():
    result = {
        "scope": "synthetic exact structural checks; no first_probe Q or execution claim",
        "status": "PASS",
    }
    for check in [check_pair_cover, check_integral_cover, check_quantile,
                  check_ledger, check_terminal_and_quota]:
        result.update(check())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
