"""Independent rational interface/schedule bounds for the integrated design.

No timing helpers from reference.py/RTL. This is an arithmetic check of the
conditional service assumptions, not their physical qualification.
"""
from fractions import Fraction as F


def check_contract():
    xi_min, xi_max = F("0.99999"), F("1.00001")
    frame_min = 1568*xi_min
    read_e = F("148.501480")
    app = F("217.002160")
    window = F(10**6)  # ns
    # A bus owner intersecting a window started in its E-extended predecessor.
    # Add .5ns for the difference of the two edge errors; count whole owners
    # even for partial intersections, hence this is a conservative upper.
    extended = window + read_e + F("0.5")
    periods, remainder = divmod(extended, frame_min)
    start = lambda j: (1568*(j//8) + 164*(j%8))*xi_min
    extra = max(sum(start(a+k)-start(a) <= remainder for k in range(8)) for a in range(8))
    owners = 8*int(periods) + extra
    x_work = F(209) + F("0.0001")*window
    control_x = (owners*read_e + x_work)/window
    offers = F(1)+180000*F("0.001003")
    peak = control_x + app*offers/window
    # Explicit extra source-domain sampling from physical first VALID, absent
    # from the earlier component-to-component bound. The actual1568xi frame
    # pays it; do not silently call it part of the4-core request crossing.
    front = F("10.500100")
    request = F("16.500160")
    frame = 1568*xi_max + F("0.5")
    response = F("40.500400")
    backpressure = F(100)
    response_with_margin = (front+request+frame+app+response+backpressure)*F(11, 10)
    credit_return = F("16.500160")+F("40.500400")
    spacing = F(10**9, 180000)
    # b=1 implies separation>=1/rho between distinct offers (limit of a small
    # interval containing both). Even a reused lane returns its credit first.
    assert response_with_margin + credit_return < spacing
    assert peak < F(4, 5) and response_with_margin < 3000
    # All cycles including the frame boundary. Independent of W and skip mode.
    gaps = [(0, 164), (1148, 1312), (1312, 1568)]
    durations = [read_e, read_e, app]
    placement = [F(b-a)*xi_min-F("0.5")-d*F(11, 10)
                 for (a, b), d in zip(gaps, durations)]
    assert min(placement) > 0
    return {"type": "conditional rational upper, not measured WCET",
            "control_owners_intersecting_1ms_upper": owners,
            "control_plus_X_upper": str(control_x), "whole_bus_peak_upper": str(peak),
            "whole_bus_peak_upper_float": float(peak),
            "physical_first_VALID_response_ns_upper_with_10pct": str(response_with_margin),
            "response_ns_float": float(response_with_margin),
            "credit_return_ns_upper": str(credit_return),
            "minimum_joint_offer_spacing_ns": str(spacing),
            "placement_margin_ns": [str(v) for v in placement]}
