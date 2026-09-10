"""Disjoint direct/accumulation interpolation for RE-CY62167-DIRECT-DECISION-BOUNDARY-01.

This module does not fit a physical probability or proprietary ECC mapping.  theta is a
controlled sensitivity parameter: the fraction of the declared DCLUSTER candidate
K>=2 parent-event population assigned to the immediate-direct class.
"""
from __future__ import annotations
import numpy as np


def candidate_mean_multiplicity(kbar, p_multi):
    """Return Kbar_M = (Kbar - (1-pM))/pM where pM>0; NaN otherwise."""
    k = np.asarray(kbar, dtype=float)
    p = np.asarray(p_multi, dtype=float)
    out = np.full(np.broadcast(k, p).shape, np.nan, dtype=float)
    kb, pb = np.broadcast_arrays(k, p)
    m = pb > 0
    out[m] = (kb[m] - (1.0 - pb[m])) / pb[m]
    return out


def partition_parent_density(r_bit, kbar, p_multi, theta, kbar_multi=None):
    """Apply the declared disjoint interpolation at parent-event level.

    Returns (r_direct_event, r_accumulation_bit, r_removed_direct_bits).
    Conservation invariant: r_bit = r_accumulation_bit + r_removed_direct_bits.
    """
    rb, kb, pm = np.broadcast_arrays(
        np.asarray(r_bit, float), np.asarray(kbar, float), np.asarray(p_multi, float)
    )
    th = float(theta)
    if not 0.0 <= th <= 1.0:
        raise ValueError("theta must be in [0,1]")
    km = candidate_mean_multiplicity(kb, pm) if kbar_multi is None else np.broadcast_to(np.asarray(kbar_multi, float), rb.shape)
    r_evt = rb / kb
    r_d = th * r_evt * pm
    multi_bits = np.where(pm > 0, pm * km, 0.0)
    r_c = r_evt * ((1.0 - pm) + (1.0 - th) * multi_bits)
    removed = r_evt * th * multi_bits
    return r_d, r_c, removed


def partition_from_bridge_endpoints(a0_acc, k1_direct, k1_acc, lec_direct, lec_acc,
                                    theta_low, theta_measured):
    """Exact endpoint-preserving repartition using frozen bridge rate arrays.

    dM/remM are the E>=0.9 MeV DCLUSTER candidate components (K1_only endpoint).
    dL/remL are the additional E<0.9 MeV components in low_energy_conservative.
    The formula is algebraically disjoint and reproduces D0, K1 and LEC endpoints.
    """
    tl, tm = float(theta_low), float(theta_measured)
    if not (0.0 <= tl <= 1.0 and 0.0 <= tm <= 1.0):
        raise ValueError("theta_low and theta_measured must be in [0,1]")
    a0 = np.asarray(a0_acc, float)
    dk = np.asarray(k1_direct, float); ak = np.asarray(k1_acc, float)
    dl = np.asarray(lec_direct, float); al = np.asarray(lec_acc, float)
    d_m = dk
    d_l = dl - dk
    rem_m = a0 - ak
    rem_l = ak - al
    direct = tm * d_m + tl * d_l
    accumulation = a0 - tm * rem_m - tl * rem_l
    removed_bits = tm * rem_m + tl * rem_l
    return direct, accumulation, removed_bits


def scalar_partition_from_bridge_endpoints(a0_acc, k1_direct, k1_acc, lec_direct, lec_acc,
                                             theta, low_energy_model):
    """Scalar theta branch required by the task contract."""
    th = float(theta)
    if low_energy_model == "K1_only":
        return partition_from_bridge_endpoints(a0_acc, k1_direct, k1_acc, lec_direct, lec_acc, 0.0, th)
    if low_energy_model == "low_energy_conservative":
        return partition_from_bridge_endpoints(a0_acc, k1_direct, k1_acc, lec_direct, lec_acc, th, th)
    raise ValueError(f"unknown low_energy_model: {low_energy_model}")
