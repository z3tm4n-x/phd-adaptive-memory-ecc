"""Separate Decimal arithmetic, not an independent scientific review.

Does not import reproduce.py or author modules from accepted packages.
Checks the two fixed rows via the equivalent rectangular S expression and ln.
"""
from decimal import Decimal as D, localcontext
from fractions import Fraction


def ratio_decimal(text):
    parts = text.split("/")
    return D(parts[0]) / D(parts[1]) if len(parts) == 2 else D(text)


def verify_decimal(cfg, result):
    with localcontext() as ctx:
        ctx.prec = cfg["arithmetic"]["verification_decimal_precision"]
        obj, srv, env = (cfg[x] for x in ("object", "service", "environment"))
        n, W, T = D(obj["n_code_bits"]), D(obj["W"]), D(obj["T_s"])
        d, eps = D(env["excess_equivalent_s"]), D(obj["epsilon"])
        c, delta = D(srv["c_s"]), D(srv["Delta_s"])
        b = D(env["background_reference_per_s"]) / D(env["D_ref_bits"]) * n * W
        B = D(env["B_over_b"]) * b
        # For this fixed E=(B-b)*d with d<T: the equivalent rectangular expression.
        S = (T - d) * b ** 2 + d * B ** 2
        tolerance = D("1e-100")  # Much wider than 120-digit evaluation roundoff.
        assert abs(S - ratio_decimal(result["shared_exact"]["S_A_per_s"])) < tolerance
        for row in result["rows"]:
            P = ratio_decimal(row["P_exact_s"])
            u = S * (n - 1) * (P + P / W + delta) / (2 * n * W)
            assert abs(u - ratio_decimal(row["U_C_exact"])) < tolerance
            assert abs(W * c / P - ratio_decimal(row["interface_fraction_exact"])) < tolerance
            assert P >= W * c / D(srv["rho_bus"]) and P / W >= c and P > delta
            for key in ("machine", "table"):
                cert = row[key]
                u_up, p = D(cert["U_C_upper"]), D(cert["p_D_allow_down"])
                assert u_up >= u and u_up + p <= eps
                assert D(cert["Lambda_D_first_moment_down"]) <= p
                log_cap = -(1 - p).ln()
                bounds = cert["log_at_issued_probability_interval"]
                assert D(bounds["lower"]) <= log_cap - tolerance
                assert log_cap + tolerance <= D(bounds["upper"])
                poisson = D(cert["Lambda_D_Poisson_down"])
                assert poisson <= log_cap
                assert u_up + 1 - (-poisson).exp() <= eps
            # The exact period is a decimal contract, even though binary64(17.2) differs.
            if row["calendar"] == "published_17_2":
                assert Fraction(row["P_exact_s"]) == Fraction(86, 5)
                assert Fraction(row["P_exact_s"]) != Fraction(17.2)
        assert len(result["rows"]) == 2
    return {"status": "PASS", "method": "separate Decimal rectangular-S and ln/exp evaluation",
            "precision": cfg["arithmetic"]["verification_decimal_precision"],
            "independent_scientific_review": False}
