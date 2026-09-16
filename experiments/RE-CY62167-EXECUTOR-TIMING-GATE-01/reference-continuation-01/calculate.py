"""Exact, config-driven conditional reference bound. Standard library only."""
import csv, hashlib, io, json, subprocess
from datetime import datetime, timedelta
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
def configuration():
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
def rate_rows(c):
    raw = subprocess.check_output(["git", "show", c["rate_commit"]+":"+c["rate_path"]], cwd=REPO)
    assert hashlib.sha256(raw).hexdigest() == c["rate_sha256"]
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    assert len(rows) == 288
    rates = []
    for j, row in enumerate(rows):
        assert datetime.fromisoformat(row["timestamp_utc"]) == datetime.fromisoformat("2026-01-19T04:00:00+00:00") + timedelta(seconds=j*300)
        assert (row["duration_s"],row["shield_mm"],row["sigma_model"],row["direction_scenario"],row["scenario"],row["mapping"]) == ("300","10","main_loglog","central_mean","DREG","W32_seq")
        r = F(row["nu_C_bit_DREG_s_1"])/2**24
        assert r == F(row["r_bit_s_1"]) and r >= 0
        rates.append(r)
    return rates
def interval_ns(c,ticks,upper=True):
    ppm=F(c["ppm"])/10**6
    return F(c["base_period_ns"])*c["clocks_per_tick"]*ticks/(1-ppm if upper else 1+ppm) + (1 if upper else -1)*F(c["jitter_envelope_ns"])
def result(c=None):
    c=c or configuration()
    rates=rate_rows(c); N=c["words"]; S=c["slot_ticks"]; P=c["period_ticks"]
    D=interval_ns(c,S)/10**9
    pmin=interval_ns(c,P,False)/10**9
    pmax=interval_ns(c,P)/10**9
    Tpre=interval_ns(c,c["prep_lead_ticks"])/10**9
    # Last word is worst: floor increments >=190, preparation increments 24.
    first_gap_ticks=c["prep_lead_ticks"]+(N-1)*P//N-S*(N-1)
    L= max(pmax,interval_ns(c,first_gap_ticks)/10**9)
    I1=sum(rates)*300; I2=sum(r*r for r in rates)*300
    count=(F(300)+D)//pmin+1
    K=F(N*496)
    A=K*L*I2+32*N*D*count*sum(rates)
    B=32*N*D
    C=K*L*Tpre
    rpre=max(rates)
    untruncated=A+B*rpre+C*rpre*rpre
    # Bisection returns an exact certified interval, not rounded root equality.
    lo=F(0); hi=F(1)
    eps=F(c["epsilon_analysis"])
    if A<=eps:
        for _ in range(180):
            mid=(lo+hi)/2
            if A+B*mid+C*mid*mid<=eps: lo=mid
            else: hi=mid
    else: lo=hi=None
    ideal_a=K*I2
    # Preserve accepted upward grid for old control, not re-label exact a as a_upper.
    quantum=10**40
    ceil_a=F(-(-ideal_a.numerator*quantum//ideal_a.denominator),quantum)
    ideal_b=31*N*I1
    output_max=F(c["output_max_ns"]); flight=F(c["flight_max_ns"])
    skew=output_max+flight
    timing={
       "read_budget_ns":interval_ns(c,c["latch_tick"],False),
       "read_required_ns":skew+45+flight+F(c["input_setup_max_ns"]),
       "decode_budget_ns":interval_ns(c,c["decode_tick"]-c["latch_tick"],False),
       "oe_to_drive_min_ns":interval_ns(c,c["drive_tick"]-c["latch_tick"],False)-skew,
       "oe_high_z_max_ns":F(18),
       "we_pulse_min_ns":interval_ns(c,c["we_high_tick"]-c["we_low_tick"],False)-skew,
       "we_pulse_required_ns":F(35),
       "data_setup_min_ns":interval_ns(c,c["we_high_tick"]-c["drive_tick"],False)-skew,
       "data_setup_required_ns":F(25),
       "data_hold_min_ns":interval_ns(c,c["release_tick"]-c["we_high_tick"],False)-skew,
       "address_setup_to_end_min_ns":interval_ns(c,c["we_high_tick"],False)-skew,
       "address_hold_min_ns":interval_ns(c,S-c["we_high_tick"],False)-skew,
       "physical_write_end_from_s_upper_ns":interval_ns(c,c["we_high_tick"])+skew,
       "slot_end_from_s_lower_ns":interval_ns(c,S,False),
       "pending_latch_to_physical_end_upper_ns":interval_ns(c,c["we_high_tick"]-c["latch_tick"])+skew,
       "pending_latch_to_fence_upper_ns":interval_ns(c,S-c["latch_tick"]),
    }
    return {"status":"CONDITIONAL_MODEL_UPPER_NOT_PHYSICAL_WCET","tube_s":D,"period_min_s":pmin,"period_max_s":pmax,
      "first_gap_ticks":first_gap_ticks,"gap_max_s":L,"pre_span_s":Tpre,"block_tube_count_per_word":int(count),
      "I1":I1,"I2":I2,"r_pre_named":rpre,"constant_A":A,"linear_B":B,"quadratic_C":C,
      "pair_H":K*L*I2,"tube_H":32*N*D*count*sum(rates),"pair_pre":C*rpre*rpre,"tube_pre":B*rpre,
      "initial_gap_surcharge":K*(L-pmax)*I2,"clock_pair_surcharge":K*(pmax-1)*I2,
      "clock_block_tube_surcharge":32*N*(D*count/F(300)-F(S,10**8))*I1,
      "U_exec":min(F(1),untruncated),"signed_slack":eps-min(F(1),untruncated),
      "r_pre_limit_lower":lo,"r_pre_limit_upper":hi,"ideal_a_upper":ceil_a,"ideal_b":ideal_b,
      "ideal_delta_star":(eps-ceil_a)/ideal_b,"timing":timing,
      "scrub_reserved_fraction":F(N*S,P),"prep_ticks":N*S,
      "prep_finish_margin_ticks":c["prep_lead_ticks"]-N*S}
def encode(v):
    if isinstance(v,F): return {"exact":str(v),"decimal_approx":format(float(v),".17g")}
    if isinstance(v,dict): return {k:encode(x) for k,x in v.items()}
    return v
if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path);args=ap.parse_args()
    text=json.dumps(encode(result()),indent=2)+"\n"
    if args.output: args.output.write_text(text,encoding="utf-8",newline="\n")
    else: print(text)
