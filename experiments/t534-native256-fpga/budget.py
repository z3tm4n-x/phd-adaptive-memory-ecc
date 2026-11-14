"""One common exception allocation, per-image residuals and SRAM time exposure."""
from decimal import Decimal as D, localcontext
import json
from pathlib import Path
import argparse

HERE=Path(__file__).resolve().parent
T=D(315576000)
DELTA=D("0.000006")
CUTOFF=D("12104627.312")
RESET_COST=D("57.866218")
CELL=D("5.8720256")
MIN_CELL=CELL*D(".99999")-D("1e-9")  # 128L, distinct physical edges
LONGEST_GAP=CELL*D("1.00001")+D("1e-9")
CFG_TICK=D("2e-8")*D("1.00001")
READ_TICK=D("1e-8")*D("1.00001")
SYNC_PAD=3*READ_TICK+D("1e-9")  # conservative level deassertion, timed clocks


def make_budget(digital):
    # Use the same input quantities as the certified comparison.
    accepted=json.loads((HERE.parent/"t525-two-phases/result.json").read_text(encoding="utf-8"))
    assert D(accepted["reset_bus_s_upper"])==RESET_COST
    assert D(accepted["twofold_extra_s_lower"])==CUTOFF
    assert D(accepted["price_s_upper"])==D("1973781.020")
    assert D(accepted["new_terms_upper"][0])==DELTA
    params={"horizon_s":str(T),"exception_allowance":str(DELTA),"exception_rate_if_all_other_zero_s-1":str(DELTA/T),
            "physical_common_cell_lower_s":str(MIN_CELL),"longest_committed_gap_upper_s":str(LONGEST_GAP),
            "status_pulse_extension_upper_s":str(SYNC_PAD),"ICAP_edge_peak_bytes_per_s_at_nominal_clock":200000000,
            "clean_ICAP_SRAM_transactions":0,"additional_SRAM_access_directly_from_SEM":0,
            "correctable_single_latency_upper_s_conditional":str((800000+61000)*CFG_TICK+SYNC_PAD),
            "crc_only_detection_upper_s_conditional":str(1600000*CFG_TICK+SYNC_PAD),
            "commissioning_boot_initialization_upper_s_conditional":str((11000000+2420000)*CFG_TICK),
            "I_upper_if_X_zero":int(CUTOFF//RESET_COST),
            "two_cell_short_episodes_whole_if_X_zero":int(CUTOFF//(2*RESET_COST)),
            "two_cell_short_episode_mean_rate_ceiling_if_X_zero_s-1":str(CUTOFF/(2*RESET_COST*T))}
    fields={}
    for k,v in digital["builds"].items():
        n=D(v["placement"]["placed_FF"]); m=D(v["essential_mask"]["marked_bits"])
        # Counting all resources with conditional consequence at most 1 is
        # a screening calculation. No finite per-bit physical rate is assumed.
        fields[k]={"placed_FF":int(n),"essential_CRAM":int(m),
            "one_FF_per_bit_s-1_IF_only_term_all_harmful":str(DELTA/(T*n)),
            "one_essential_CRAM_per_bit_s-1_IF_only_term_all_harmful":str(DELTA/(T*m)),
            "conditional_modeled_Q_with_execution_allocation":accepted["stop_upper_also_bounds_physical_Q"] if k[0]=="A" else "0.000999990641",
            "ten_year_port_upper_s_IF_extra_zero":accepted["price_s_upper"] if k[0]=="A" else accepted["sufficient_fixed_candidate_s_upper"],
            "physical_execution_probability_upper":"unknown","observed_flight_power_W":"unknown"}
    return {"conditions":params,"builds":fields}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--write",action="store_true")
    args=p.parse_args()
    with localcontext() as ctx:
        ctx.prec=32
        summary=make_budget(json.loads((HERE/"results/digital.json").read_text(encoding="utf-8")))
    name=HERE/"results/budget.json"
    if args.write:
        name.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    else:
        assert summary==json.loads(name.read_text(encoding="utf-8"))
    print(json.dumps(summary,indent=2))
