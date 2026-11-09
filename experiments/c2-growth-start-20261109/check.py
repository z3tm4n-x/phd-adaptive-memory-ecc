"""Replay the C2 start-window and two-period tests on the frozen C1 inputs."""
import argparse
import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timedelta, timezone
from fractions import Fraction as F
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
C1 = "c944c91a2c20a207516824333e02711aaf34898f"
C1_GROWTH = "9eacc8fa8ed1860936b0ca68d3ad07c80548b011"
EPOCH = datetime(1974, 7, 1, tzinfo=timezone.utc)
STEP = 300
HORIZON = 315576000
REF = 38 * 524288
EXP = ROOT / "experiments"


def frozen_file(commit, directory, name):
    locator = f"{commit}:experiments/{directory}/{name}"
    raw = subprocess.check_output(["git", "show", locator], cwd=ROOT)
    return json.loads(raw)


def stamp(index):
    return (EPOCH + timedelta(seconds=STEP * int(index))).strftime("%Y-%m-%d %H:%M")


def bound(value, digits, upper=False):
    scaled = value * 10**digits
    rounded = math.ceil(scaled) if upper else math.floor(scaled)
    return f"{rounded // 10**digits}.{rounded % 10**digits:0{digits}d}"


def area_ceiling(initial, growth, duration, cap):
    if growth == 0:
        return initial * duration
    rise = min(duration, (cap - initial) / growth)
    return initial * rise + growth * rise**2 / 2 + cap * (duration - rise)


def next_ceiling(initial, mean, growth, duration, cap):
    """Upper attainable endpoint for a bin; None means inconsistent."""
    if not 0 <= mean <= cap or mean * duration > area_ceiling(initial, growth, duration, cap):
        return None
    mass_slope = growth * duration
    endpoint = (math.sqrt(2 * mass_slope * mean)
                if mean <= mass_slope / 2 else mean + mass_slope / 2)
    return min(cap, initial + mass_slope, endpoint)


def verify_cadence():
    directory = "c1-common-geo-20261109"
    cadence = frozen_file(C1_GROWTH, directory, "cadence.json")
    checked = frozen_file(C1_GROWTH, directory, "growth.json")
    maxima = [product["nu_slope_s_inv2"]["slope"]
              for series in cadence["native"].values() for product in series.values()
              if product["nu_slope_s_inv2"]]
    matched = cadence["matched"]["G19_East"]
    peak = matched["minute"]
    assert peak["slope"] == max(maxima) == checked["s_obs_s_inv2"]
    assert not peak["both_strict"]
    rounded = math.ceil(2 * F(str(peak["slope"])) * 10**9) / 10**9
    assert rounded == float(checked["g_s_inv2"])
    assert all(p["exact_feasible"] in ("True", True) and p["constructed_feasible"]
               for p in checked["profiles"].values())
    return dict(g_per_s2=rounded, minute_max=peak["slope"], pair_start=peak["from_utc"],
                five_min_native=matched["native_five_minutes"]["slope"],
                five_min_aggregated=matched["mean_five_minutes"]["slope"],
                cadence_ratio=matched["minute_to_mean_maximum_ratio"])


def verify_archive(cache, archive, background, peak, adopted_g):
    bands_file = cache / "bands.npy"
    expected = archive["source_cache"]["arrays_sha256"]["bands.npy"]
    with bands_file.open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != expected:
            raise ValueError("T141 response array hash mismatch")
    bands = np.load(bands_file, mmap_mode="r")
    solar = (1 + archive["HI_to_H"]) * np.maximum(bands[:, 1, :].sum(axis=1) - archive["H_p10"], 0)
    rates = background + solar
    width = HORIZON // STEP
    count = len(rates) - width + 1
    assert count == archive["window_count"]
    # A decade may start at any catalog bin, including the middle of an event.
    active = np.zeros(count, dtype=bool)
    starts = np.zeros(count, dtype=bool)
    identities = {}
    catalog = EXP / "tNN-sepem-profiles/outputs/events.csv"
    with catalog.open(encoding="utf-8", newline="") as handle:
        for event in csv.DictReader(handle):
            start, end = int(event["start_index"]), int(event["stop_index_exclusive"])
            if start < count:
                active[start:min(end, count)] = True
                starts[start] = True
                identities[event["event_id"]] = (start, end)
    high = np.flatnonzero(rates[:count] > (peak + background) / 2)
    records = []
    for i in high:
        event = next(e for e, (lo, hi) in identities.items() if lo < i < hi)
        records.append(dict(utc=stamp(i), event=event, mean_per_s=float(rates[i])))
    secants = np.maximum(np.diff(rates), 0) / STEP
    up = int(np.argmax(secants))
    observed = float(secants[up])
    g_seed = math.ceil(2 * observed * 1e9) / 1e9
    # Bin j rises from min(m[j-1],m[j]) to m[j]+(m[j]-m[j-1])_+.
    peaks = solar.copy()
    peaks[1:] += np.maximum(np.diff(solar), 0)
    assert peaks.max() < peak - background
    assert np.isclose(observed, archive["whole_archive"]["max_upward_bin_slope_s_inv2"])
    maximum = float(rates[:count].max())
    assert np.isclose(maximum, archive["whole_archive"]["peak_s_inv"])
    # With r(0)=0 and this large first mean the saturating ramp hits R.
    highest_mean = maximum - background
    cap = peak - background
    assert highest_mean > cap / 2
    quiet_g_tangent = 2 * highest_mean / STEP
    quiet_g_capped = cap**2 / (2 * STEP * (cap - highest_mean))
    assert abs(area_ceiling(0, quiet_g_capped, STEP, cap) / STEP - highest_mean) < 1e-14
    first_capacity = background + area_ceiling(0, adopted_g, STEP, cap) / STEP
    assert first_capacity > maximum
    endpoint = cap
    for index, mean in enumerate(solar):
        endpoint = next_ceiling(endpoint, float(mean), adopted_g, STEP, cap)
        if endpoint is None:
            raise ValueError(f"Unreachable SEPEM bin {index}")
    return dict(
        sha256_bands=expected, bins=len(rates), full_decades=count,
        active_at_left=int(active.sum()), strictly_inside=int((active & ~starts).sum()),
        exactly_at_catalog_begin=int(starts.sum()), high_first=records,
        max_secant_per_s2=observed, secant_start=stamp(up),
        g_seed_sepem_per_s2=g_seed, highest_constructed_rate=background + float(peaks.max()),
        quiet_g_uncapped_per_s2=quiet_g_tangent, quiet_g_capped_per_s2=quiet_g_capped,
        quiet_first_capacity_at_adopted_g=first_capacity,
        max_S1=archive["maxima"]["S1"]["S1"],
    )


def menu_and_physics(fixed):
    env = fixed["environment"]
    b, peak = F(env["b"]), F(env["B"])
    cap = peak - b
    excess = 187464 - b * HORIZON
    plateau = excess / cap
    old = F(env["tau"])
    speed = F(39, REF) * peak
    aperture = F(fixed["aperture_s"])
    jitter = F(fixed["jitter_s"])
    xmin, xmax = map(F, fixed["clock"])
    s2 = b**2 * HORIZON + (2 * b + cap) * excess

    def v_lower(words, h, slow=True, duration=plateau):
        round_s = F(196 * words, 10**9)
        n_upper = (4 + duration / (4 * h * round_s) if slow
                   else 2 + duration / (h * round_s))
        return F(words, 2) * speed**2 * duration**2 / n_upper

    def physical(words, block_rounds=32):
        round_s = F(196 * words, 10**9)
        length = block_rounds * round_s
        blocks = math.floor(plateau / length)
        empty_factor = 1 - words * speed * length
        assert empty_factor > 0
        # Following a quiet full scan the last positive report holds FAST for <=2 rounds.
        complete_slow = (block_rounds - 7) // 4 - 1
        sq_slow = complete_slow * (4 * round_s - aperture)**2
        # At h>=2 all actual visits of this word are >=2L apart in the nominal executor.
        apertures = math.ceil((length + aperture) / (2 * round_s))
        sq_any = (length - apertures * aperture)**2 / (apertures + 1)
        assert length > apertures * aperture
        def lifetime(squares):
            hazard = blocks * F(38, 78) * words * empty_factor * speed**2 * squares
            return hazard / (1 + hazard)
        return dict(full_blocks=blocks, empty_factor_lower=bound(empty_factor, 9),
                    slow_cells=complete_slow, max_apertures=apertures,
                    Q_lower_h1=bound(lifetime(sq_slow), 9),
                    Q_lower_h_ge2=bound(lifetime(sq_any), 9))

    def compressed(words, h):
        round_s = F(196 * words, 10**9)
        span = 4 * h * round_s * xmax + 2 * jitter
        passage = h * round_s * xmax + 2 * jitter
        dstar = h * round_s * xmin
        overlap = math.floor(span / dstar) + 1
        count = math.ceil((HORIZON + 2 * jitter) / dstar) + 2
        return words * F(39, REF)**2 * (
            (span + overlap * passage / 2) * s2 + 2 * jitter * count * span * peak**2)

    # On the high plateau every complete S edge with a complete next S edge
    # gives an extra Ws_n A_n in addition to the squared term.
    words = 65536
    round_s = F(196 * words, 10**9)
    scans = math.floor((plateau - 3 * round_s) / (4 * round_s)) - 1
    min_passage = round_s - F(420, 10**9)
    lower_carry = scans * words * speed**2 * ((4 * round_s)**2 / 2 + 4 * round_s * min_passage)
    worst_mass_per_round = 131072 * speed * F(196 * 131072, 10**9)
    return dict(
        exposure_F=bound(excess, 11), old_solar=bound(cap * old, 8),
        plateau_s=bound(plateau, 9), S2_max=bound(s2, 9, upper=True),
        old_T141_V_slow_05=bound(v_lower(131072, 1, duration=old), 9),
        old_T141_V_fast_05=bound(v_lower(131072, 2, False, old), 9),
        new_V_slow_05=bound(v_lower(131072, 1), 9),
        new_V_fast_05=bound(v_lower(131072, 2, False), 9),
        new_V_slow_025_h1_with_carry=bound(lower_carry, 9),
        new_V_slow_025_h2=bound(v_lower(65536, 2), 9),
        new_V_slow_0125_h1=bound(v_lower(32768, 1), 9),
        new_V_fast_0125_h19=bound(v_lower(32768, 19, False), 9),
        early_false_05_h1_lower=bound(1 - 3 * worst_mass_per_round, 9),
        early_false_h_le18_all_lower=bound(1 - 54 * worst_mass_per_round, 9),
        V_upper_0125_h1=bound(compressed(32768, 1), 9, upper=True),
        physical={str(words): physical(words) for words in (32768, 65536, 131072)},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--t141-cache", type=Path, required=True)
    args = parser.parse_args()
    fixed = frozen_file(C1, "c1-geo-fixed-20261109", "fixed.json")
    archive = frozen_file(C1, "c1-geo-fixed-20261109", "sepem.json")
    cadence = verify_cadence()
    b = float(F(fixed["environment"]["b"]))
    peak = float(F(fixed["environment"]["B"]))
    results = dict(c1_head=C1, growth_head=C1_GROWTH, cadence=cadence,
                   sepem=verify_archive(args.t141_cache, archive, b, peak, cadence["g_per_s2"]),
                   plateau=menu_and_physics(fixed))
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
