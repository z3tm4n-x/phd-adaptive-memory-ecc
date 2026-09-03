from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

from event_partition import ADDRESS_BITS, COORD_BITS, FROZEN_COEFFICIENT_MASKS, word_id


def gf2_rref(rows: list[int], ncols: int):
    work = [int(v) for v in rows if v]
    r = 0
    pivots = []
    for col in range(ncols):
        q = next((k for k in range(r, len(work)) if (work[k] >> col) & 1), None)
        if q is None:
            continue
        work[r], work[q] = work[q], work[r]
        pivot = work[r]
        for k in range(len(work)):
            if k != r and ((work[k] >> col) & 1):
                work[k] ^= pivot
        pivots.append(col)
        r += 1
        if r == len(work):
            break
    return work[:r], pivots


def nullspace_basis(rows: list[int], ncols: int) -> list[int]:
    rr, pivots = gf2_rref(rows, ncols)
    free = [i for i in range(ncols) if i not in pivots]
    basis = []
    # RREF rows are paired to pivots in the same order.
    for f in free:
        v = 1 << f
        for row, p in zip(rr, pivots):
            if (row >> f) & 1:
                v |= 1 << p
        if any(((row & v).bit_count() & 1) for row in rows):
            raise AssertionError("invalid nullspace vector")
        basis.append(v)
    return basis


def linear_coordinate_masks() -> list[int]:
    # Frozen feature mask uses bit 0 as affine constant, and bits 1..24 for x0..x11,y0..y11.
    return [(int(c) >> 1) & ((1 << (2 * COORD_BITS)) - 1) for c in FROZEN_COEFFICIENT_MASKS]


def word_kernel_basis(p: int, q: int) -> list[int]:
    if not (0 <= p < q < ADDRESS_BITS):
        raise ValueError("0 <= p < q < 21 required")
    masks = linear_coordinate_masks()
    rows = [masks[j] for j in range(ADDRESS_BITS) if j not in (p, q)]
    basis = nullspace_basis(rows, 2 * COORD_BITS)
    if len(basis) != 5:
        raise AssertionError(f"expected 5-dimensional word kernel, got {len(basis)} for {(p,q)}")
    return basis


def all_subspace_vectors(basis: list[int]) -> list[int]:
    out = []
    for sel in range(1 << len(basis)):
        v = 0
        for i, b in enumerate(basis):
            if (sel >> i) & 1:
                v ^= b
        out.append(v)
    return sorted(out)


def min_abs_xor_delta(mask: int, width: int = COORD_BITS) -> int:
    if mask == 0:
        return 0
    # Exact finite-grid minimum; width=12, so this is cheap and avoids a metric shortcut.
    return min(abs(x - (x ^ mask)) for x in range(1 << width))


def minimum_spacing(p: int, q: int):
    basis = word_kernel_basis(p, q)
    vectors = all_subspace_vectors(basis)
    values = []
    for v in vectors:
        if v == 0:
            continue
        dx = v & ((1 << COORD_BITS) - 1)
        dy = (v >> COORD_BITS) & ((1 << COORD_BITS) - 1)
        ax = min_abs_xor_delta(dx)
        ay = min_abs_xor_delta(dy)
        values.append((ax + ay, math.hypot(ax, ay), max(ax, ay), dx, dy))
    l1 = min(t[0] for t in values)
    l2 = min(t[1] for t in values)
    linf = min(t[2] for t in values)
    return {"L1": l1, "L2": l2, "Linf": linf, "basis": basis, "vectors": vectors}


def mapping_id(p: int, q: int) -> str:
    return f"W_{p:02d}_{q:02d}"


def build_mapping_family():
    rows = []
    for p, q in itertools.combinations(range(ADDRESS_BITS), 2):
        spacing = minimum_spacing(p, q)
        # The original manuscript-compatible filter is recovered as minimum supplied-grid
        # spacing of 16. The three standard metrics are independently recorded; for this
        # family they give the same retained set, so no metric is selected post hoc.
        retained = spacing["L1"] >= 16 and spacing["Linf"] >= 16 and spacing["L2"] >= 16 - 1e-12
        rows.append({
            "mapping_id": mapping_id(p, q),
            "bit_p": p,
            "bit_q": q,
            "word_definition": f"pack(A bits except A{p},A{q})",
            "minimum_spacing": int(spacing["Linf"]) if float(spacing["Linf"]).is_integer() else spacing["Linf"],
            "spacing_metric": "supplied-grid minimum; L1/L2/Linf retained sets identical",
            "minimum_spacing_L1": spacing["L1"],
            "minimum_spacing_L2": spacing["L2"],
            "minimum_spacing_Linf": spacing["Linf"],
            "retained": bool(retained),
            "baseline_mapping": (p, q) == (0, 1),
        })
    return rows


def gaussian_binomial_21_2_direct() -> int:
    return ((2**21 - 1) * (2**21 - 2)) // ((2**2 - 1) * (2**2 - 2))


def gaussian_binomial(n: int, k: int, q: int = 2) -> int:
    # Independent dynamic-program recurrence: [n k]_q=[n-1 k]_q+q^(n-k)[n-1 k-1]_q.
    table = [[0] * (k + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        table[i][0] = 1
    for i in range(1, n + 1):
        for j in range(1, min(i, k) + 1):
            if j == i:
                table[i][j] = 1
            else:
                table[i][j] = table[i - 1][j] + (q ** (i - j)) * table[i - 1][j - 1]
    return table[n][k]


def baseline_word_equals_floor_div4(limit: int = 1 << 21) -> bool:
    # Packing all bits except A0,A1 is exactly A>>2.
    probes = [0, 1, 2, 3, 4, 7, 8, 1023, 1024, limit - 1]
    return all(word_id(a, 0, 1) == a // 4 for a in probes)

