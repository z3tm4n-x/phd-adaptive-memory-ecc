"""#457 per-map comparison: exact units and directed rounding of allowed rates."""
from fractions import Fraction as F
from math import ceil
import json
from build_model import CAL, CERT

def floor_decimal(x, places=12):
    scale=10**places
    n=(x*scale).__floor__()
    return ("-" if n<0 else "")+f"{abs(n)//scale}.{abs(n)%scale:0{places}d}"

def calculate(measured):
    # These are not fitted constants. Keep accepted post-stop and boundary terms.
    cal=json.loads(CAL.read_text())
    bank=json.loads(CERT.read_text())["131072"]
    model=bank["quarter_eligible"]
    pace=model["staircase"]; price=pace["price"]
    assert model["W_interval"]==[32768,44529] and pace["registration"]["top_rounds"]==256
    assert pace["registration"]["quiet_frames"]==[5,10,19,38,75,149,298,596]
    B=F(price["budget_X_for_twice_s"]); k=F(price["s_per_invalid_upper"])
    S=F(price["bus_read_repair_s_at_I0"]); lower=F(model["fixed"]["necessary_bus_s_if_nonempty"])
    assert (B,k)==(F("2850848.789"),F("34.016758")) and B==lower/2-S
    assert all(m["extra_port_ns"]==m["cut_install_protected_ns"]==m["between_scans_protected_ns"]==0
               for m in measured.values())
    # Scope of X=0: only launch can take the port, no off-calendar polls /
    # different SRAM startup, recovery transactions or extra false repairs.
    # The all-time argument for this interface, not just the samples, is in REPORT.
    X=F(0); T=315576000; A=65536
    L=F(A//4*cal["frame_ns"],10**9); assert L==F(bank["continuous"]["L_s"])
    xm=F(cal["xi_min"]); xp=F(cal["xi_max"]); j=F(cal["edge_jitter_ns"])/10**9
    h=xm*(256*L)-2*j
    M=ceil(F(T)/h)+2   # common-cell cuts, conservative two edges
    M_pass=ceil(F(T)/(xm*L-2*j))+2   # even if every possible pass is scheduled
    I=(B-X)/k; n=I.__floor__()
    assert X+k*n<=B<X+k*(n+1)
    span=F(60); b=1+ceil(span/h)
    return dict(T_s=T,A_x16=A,W=model["W_interval"],L_s=str(float(L)),
        top_nominal_s=pace["registration"]["period_local_s"],
        stop_Q_upper_from_457_not_measured=pace["stop_and_Q_upper"],
        full_scan_nominal_clean_ns=A*100,full_scan_nominal_one_repair_ns=A*100+100,
        final_release_to_cut_nominal_ns=140,cut_to_install_nominal_ns=200,
        install_to_next_possible_start_nominal_ns=100,
        cut_after_latest_release_conservative_margin_ns=floor_decimal(340*xm-2*j*10**9-(200*xp+3*j*10**9),6),
        install_to_start_conservative_margin_ns=floor_decimal(100*xm-2*j*10**9,6),
        lower_best_constant_per_same_map_s=price_string(lower),known_ladder_at_I0_s=price_string(S),
        X_upper_s_for_model=0,k_s=price["s_per_invalid_upper"],budget_s=price["budget_X_for_twice_s"],
        I_allow_exact=f"{I.numerator}/{I.denominator}",I_allow_down=floor_decimal(I),
        hard_integer_limit=n,left_at_limit_s=floor_decimal(k*n,6),
        left_at_one_more_s=floor_decimal(k*(n+1),6),
        bad_cells_per_second_down=floor_decimal(I/T,15),
        bad_cells_per_day_down=floor_decimal(I*86400/T),
        seconds_per_bad_cell_at_boundary_approx=round(float(T/I),9),
        common_cell_duration_lower_s=floor_decimal(h),max_cell_opportunities=M,
        uniform_per_cell_probability_sufficient_down=floor_decimal(I/M,15),
        max_pass_opportunities=M_pass,
        uniform_per_report_probability_sufficient_down=floor_decimal(I/M_pass,15),
        outage_60s_max_cells=b,outage_60s_episodes_per_day_down=floor_decimal(I*86400/(T*b)),
        management_tariff_not_measured=dict(all_frames_s=price["full_management_reserve_s"],
            active_frames_coefficient_s=price["s_per_invalid_including_active_management_upper"],
            active_frames_budget_s=price["budget_after_active_management_s"]),
        observed_operational_loss_rate=None)
def price_string(x): return floor_decimal(x,3)
