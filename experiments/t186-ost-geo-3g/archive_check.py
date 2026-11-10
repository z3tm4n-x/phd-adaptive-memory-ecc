"""Affine transfer of the frozen C1 H histories and their explicit gap completions."""

import json
import math
from fractions import Fraction


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def compare_histories(exp, tab, full, coverage):
    growth = load(exp / "c1-common-geo-20261109/growth.json")
    variation = load(exp / "c1-repeat-quota-20261109/variation.json")
    sepem = load(exp / "c1-geo-fixed-20261109/sepem.json")
    b0 = float(Fraction(coverage["b_s_inv"]))
    B0 = float(Fraction(coverage["B_s_inv"]))
    T, C = int(coverage["T_s"]), int(coverage["S1_cap"])
    g0, U0 = float(growth["g_s_inv2"]), variation["quota_s_inv"]
    beta0 = full["solar_LET"] / full["solar_H"]
    beta = tab["solar_LET"] / tab["solar_H"]
    assert math.isclose(beta0, sepem["HI_to_H"], rel_tol=1e-13)
    # H(t) remains the archived proton excess behind Al; only its synchronous
    # nonproton proxy changes. Scaling the previously constructed gaps gives
    # one admissible completion. The new static tables contain no time series.
    k = (1 + beta) / (1 + beta0)
    b = tab["b"]
    shift = b - b0

    def exposure(old_total):
        return b * T + k * (old_total - b0 * T)

    rows = {}
    for name, old in growth["profiles"].items():
        if name == "SEPEM_archive":
            old_S1 = coverage["SEPEM"]["max_S1_by_fsum"]
            old_J = variation["SEPEM"]["maxima"][variation["winner"]]["value_s_inv"]
        else:
            old_S1 = old["constructed_full_S1"]
            old_J = variation["GOES"][name.removeprefix("GOES_")]["reconstruction_J_s_inv"]
        row = {
            "S1_on_accepted_windows_or_gap_completion": exposure(old_S1),
            "peak_of_transferred_construction": b + k * old["constructed_max_excess_s_inv"],
            "max_upward_slope_inside_bins": k * old["constructed_max_slope_s_inv2"],
            "J_in_old_background_coordinates": shift + k * old_J,
        }
        if name == "SEPEM_archive":
            # Sliding by < one bin replaces at most one bin of bounded excess.
            row["S1_any_start_upper"] = exposure(old_S1) + sepem["dt_s"] * k * old["constructed_max_excess_s_inv"]
        elif old["witness_excess_on_gaps"] > 0:
            row["growth_bound_on_gap_ramps"] = k * g0
        rows[name] = row

    gap_budgets = {}
    for direction, entry in coverage["GOES"].items():
        spare = C - b * T - k * entry["observed_excess"]
        gap_budgets[direction] = {
            "observed_s": entry["covered_s"], "missing_s_including_tail": entry["unobserved_over_T_s"],
            "observed_S1": b * entry["covered_s"] + k * entry["observed_excess"],
            "allowed_excess_integral_on_gaps_above_new_b": spare,
            "allowed_mean_excess_on_gaps_s_inv": spare / entry["unobserved_over_T_s"],
        }

    # These are also upper bounds for affine images of ANY profile in the old
    # class. Account separately for unaligned starts of the SEPEM interpolation.
    max_S1 = max(exposure(C), rows["SEPEM_archive"]["S1_any_start_upper"])
    max_B = max(tab["B"], b + k * (B0 - b0))
    max_g = k * g0
    max_U = shift + k * U0
    fits = (b >= b0 and max_B <= B0 and max_S1 <= C and max_g <= g0 and max_U <= U0)
    for row in rows.values():
        fits = fits and (row["peak_of_transferred_construction"] <= B0
                         and row["S1_on_accepted_windows_or_gap_completion"] <= C
                         and row["max_upward_slope_inside_bins"] <= g0
                         and row["J_in_old_background_coordinates"] <= U0)

    no_rescaling = coverage["SEPEM"]["max_S1_by_fsum"] + shift * T
    return {
        "old_limits": {"b": b0, "B": B0, "S1": C, "S2": float(Fraction(coverage["S2_upper"])),
                       "F": C - b0 * T, "g": g0, "U": U0},
        "old_archive": {"SEPEM_S1_max": coverage["SEPEM"]["max_S1_by_fsum"],
                        "SEPEM_windows": coverage["SEPEM"]["windows"],
                        "SEPEM_peak_mean": coverage["SEPEM"]["peak_s_inv"],
                        "GOES_decisive_minute_slope": growth["s_obs_s_inv2"],
                        "max_J": variation["largest_reconstructed_J_s_inv"]},
        "beta_cosrad": beta0, "beta_ost_tabulated": beta, "excess_multiplier": k,
        "background_shift": shift, "background_shift_times_T": shift * T,
        "accepted_excess_quota_in_new_background_coordinates": C - b * T,
        "observed_max_upward_mean_slope_new": k * growth["s_obs_s_inv2"],
        "archives_on_transferred_profiles": rows, "GOES_5min_gap_budgets": gap_budgets,
        "conditional_class_covers": fits,
        "sufficient_joint_residual_budgets": {
            "peak_s_inv": B0 - max_B, "ten_year_expected_inversions": C - max_S1,
            "upward_slope_s_inv2": g0 - max_g, "initial_plus_positive_variation_s_inv": U0 - max_U,
        },
        "constant_uncovered_rate_budget_from_exposure_s_inv": (C - max_S1) / T,
        "if_only_background_replaced": {
            "SEPEM_S1": no_rescaling, "excess_over_accepted_S1": no_rescaling - C,
            "lower_integer_cap_required_by_these_windows": math.ceil(no_rescaling),
            "max_excess_multiplier_from_SEPEM_S1": (C - b * T) / (coverage["SEPEM"]["max_S1_by_fsum"] - b0 * T),
        },
    }
