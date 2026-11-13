"""Inventory, non-statistical injection checks, and first-exception budget."""
import argparse
import csv
import json
import re
from collections import Counter
from decimal import Decimal as D, getcontext
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
T = D(315576000)
DELTA = D("0.000006")
L_NS = 11468800
WORDS = 32768
getcontext().prec = 36

# Each routed FF belongs to one initiating group, regardless of its fanout.
GROUPS = {
    "count": "core/count core/policy/stored_count",
    "history": "core/policy/quiet core/policy/quiet_inv core/policy/initialized core/policy/spoiled",
    "period": "core/policy/proposed core/policy/proposed_parity core/policy/issued core/installed core/policy/command_strobe",
    "wait": "core/wait_rounds core/wait_parity core/active",
    "completeness": "core/seen core/sealed core/report_send core/scan_bad core/policy/received core/policy/invalid core/policy/closed",
    "phase": "core/frame core/epoch core/phase_a core/phase_inv core/phase_parity core/running core/visit_token",
    "err_capture": "core/sampled_err",
    "dq_image": "core/repair_image",
    "obligation": "core/repair_a core/repair_b core/sampled core/committed core/damaged core/protect_owner",
    "port": "core/address core/pad_address core/selected core/reading core/writing core/drive core/drive_next core/dq_out core/pad_t_n core/pad_select_n core/pad_oe_n core/pad_we_n",
    "application_startup_monitors": "app_addr app_rest core/app_candidate core/app_data core/app_grant core/app_owner core/app_valid core/execution_fault fault_led lock_sync locked_led observed startup",
}

def inventory():
    owner = {n: k for k, names in GROUPS.items() for n in names.split()}
    rows = list(csv.DictReader((HERE / "registers.tsv").read_text().splitlines(), delimiter="\t"))
    by_group = Counter()
    sites = Counter()
    places = {}
    for row in rows:
        name = row["cell"]
        stem = name.split("_reg", 1)[0]
        by_group[owner[stem]] += 1
        sites[row["site"].split("_")[0]] += 1
        places[name] = (row["site"], row["bel"])
    assert len(places) == len(rows) == len(set(places.values())) == sum(by_group.values()) == 326
    assert sites == {"SLICE": 273, "ILOGIC": 1, "OLOGIC": 52}
    assert places["core/repair_a_reg"][0] == places["core/repair_b_reg"][0] == "SLICE_X104Y77"
    assert places["core/sampled_err_reg"][0] == "ILOGIC_X1Y116"
    return {"FF_groups":dict(sorted(by_group.items())), "FF_by_site_type":dict(sites), "total_FF":len(rows)}

def traces(path):
    lines = path.read_text().splitlines()
    obs = [dict((k, int(v)) for k, v in re.findall(r"(\w+)=(-?\d+)", s)) for s in lines]
    assert [r["case"] for r in obs] == list(range(15))
    # Each row fixes a physical expectation independently of the RTL. L means
    # no second start checked if a previously measured command already set it.
    good = 0xA5BF
    expected = [
        # report, zero, issue, physically next at L, data before write end
        (0,1,1,0,-1), (1,0,0,1,good), (0,1,1,0,-1), (1,0,0,1,good^1),
        (-1,0,0,1,good), (-1,0,0,1,good), (0,0,0,1,-1), (0,0,0,1,-1),
        (0,1,0,1,-1), (0,1,1,0,-1), (-1,0,0,1,-1), (1,0,0,1,good^1),
        (0,1,0,1,-1), (-1,0,0,1,-1), (0,1,1,0,-1)]
    for r, goal in zip(obs, expected, strict=True):
        assert r["reads"] == WORDS
        assert (r["report_count"],r["zero"],r["install_code"],r["addr0_at_L"],
                r["data_5ns_before_WE_rise"]) == goal, r
        assert r["sample_ns"] == (-1 if r["case"]==10 else L_NS-580)
        assert r["write_ns"] == (L_NS-480 if goal[4]!=-1 else -1)
        assert r["report_ns"] == (-1 if goal[0]<0 else L_NS-(440 if goal[0] else 540))
    assert obs[9]["addr0_at_2L"]==0 and obs[9]["first_start_L"]==8
    assert obs[14]["addr0_at_2L"]==1 and obs[14]["fault_ns"]-obs[14]["incident_ns"]==5
    return len(obs)

def encode_period(code):
    # Extended Hamming (8,4), even parity; bit 8 checks the first seven.
    word=[0]*9
    for i,pos in enumerate((3,5,6,7)):
        word[pos]=(code >> i) & 1
    for mask in (1,2,4):
        word[mask]=sum(word[p] for p in range(1,8) if p&mask)%2
    word[8]=sum(word)%2
    return tuple(word[1:])

def decode_period(raw):
    word=[0,*raw]
    syndrome=0
    for p in range(1,8):
        if word[p]: syndrome^=p
    odd=sum(word)%2
    if syndrome and not odd:
        return None
    if odd: word[syndrome or 8]^=1
    level=sum(word[pos]<<i for i,pos in enumerate((3,5,6,7)))
    return level if level<10 else None

def capture_vote(lanes):
    # A lane returns the 17-bit sampled ERR/DQ word, or None for no valid
    # capture. Agreement must cover the complete word for a two-lane vote.
    valid=[word for word in lanes if word is not None]
    if len(valid)==3:
        a,b,c=valid
        return (a&b)|(a&c)|(b&c), len(set(valid))!=1
    if len(valid)==2 and valid[0]==valid[1]:
        return valid[0], True
    return None, True

def allowed_period(request, proof):
    # Zero denotes prearmed FAST. This decision is taken before commit.
    both_complete, matching_tag, count_zero, saw_no_write, history_ok, on_time=proof
    if all((both_complete,matching_tag,count_zero,saw_no_write,history_ok,on_time)):
        return request
    return 0

def protected_spec():
    # Local specification only. These properties assume a valid common input,
    # distinct capture/storage replicas, intact local voter and physical WE.
    checked = 0
    for err, value in product((0,1),(0x0000,0xa5bf,0xffff)):
        for channel in range(3):
            for upset in range(17):  # one independent replica, one bit
                hits = [err]*3
                images = [value]*3
                if upset == 16: hits[channel] ^= 1
                else: images[channel] ^= 1 << upset
                received=[(hit<<16)|image for hit,image in zip(hits,images,strict=True)]
                assert capture_vote(received)==((err<<16)|value,True)
                checked += 1
    missing=0
    for err,value,absent in product((0,1),(0x0000,0xa5bf,0xffff),range(3)):
        word=(err<<16)|value
        lanes=[word]*3
        lanes[absent]=None
        assert capture_vote(lanes)==(word,True)
        lanes[(absent+1)%3]^=1
        assert capture_vote(lanes)==(None,True)
        missing+=2
    assert capture_vote([None,None,0])==(None, True)
    proof_cases=0
    for proof in product((False,True),repeat=6):
        for request in range(10):
            issued=allowed_period(request,proof)
            assert issued==(request if sum(proof)==6 else 0)
            proof_cases+=1
    single=double=0
    for code in range(10):
        encoded=encode_period(code)
        assert decode_period(encoded)==code
        for i in range(8):
            received=list(encoded)
            received[i]^=1
            assert decode_period(received)==code
            single+=1
            for j in range(i):
                received[j]^=1
                assert decode_period(received) is None
                received[j]^=1
                double+=1
    # Common input stuck low with physical ERR high: the voter cannot
    # distinguish the resulting word from a genuine clean input.
    # The shared pad should have carried ERR=1 and data=0xa5bf.
    wrong,alarm=capture_vote([0xa5bf]*3)
    common_wrong=wrong!=0x1a5bf and not alarm
    assert common_wrong
    return {"single_replica_cases":checked, "missing_capture_combinations":missing,
            "precommit_guard_cases":proof_cases,"single_installed_command_corrected":single,
            "double_installed_command_rejected":double,"invisible_common_ERR_witness":common_wrong}

def budget(register_rate, permission_only_rate, other, common):
    if min(register_rate,permission_only_rate,other,common)<0:
        raise ValueError("negative intensity or mission probability")
    total = T*(register_rate+permission_only_rate)+other+common
    return {"union_upper":str(min(D(1),total)), "reserve":str(DELTA-total),
            "sufficient":total<=DELTA}

def evaluate(log):
    inv=inventory()
    threshold=DELTA/T
    conditional=budget(D("5e-15"),D("5e-15"),D("1e-6"),D("1e-6"))
    assert conditional["sufficient"] and D(conditional["union_upper"])==D("0.000005155760")
    assert not budget(threshold,threshold,D(0),D(0))["sufficient"]
    assert budget(D(0),D(0),DELTA,D(0))["sufficient"]
    # Uniform upper on per-bit intensity at every physical instant, including
    # bad weather. End correction covers one incomplete calendar on either end.
    # Include data hold through driver release at +180 ns.
    xi_low,xi_high,J = D(".99999"),D("1.00001"),D(".5")
    t_ns=T*D(10)**9
    full_scan_bound=((t_ns+2*J)/(D(L_NS)*xi_low)).to_integral_value(rounding="ROUND_CEILING")+1
    windows={}
    for name,width in (("ERR",10),("repair_image",120)):
        window=width*xi_high + 2*J
        per_bit_seconds=full_scan_bound*WORDS*window/D(10)**9
        windows[name]={"nominal_ns":width,"upper_physical_ns":str(window),
                       "upper_active_s_per_bit":str(per_bit_seconds),
                       "maximum_duty_over_T":str(per_bit_seconds/T),
                       "sole_path_pointwise_per_bit_rate_ceiling":str(DELTA/(per_bit_seconds*(16 if name=="repair_image" else 1)))}
    return {"basis":"conditional bounds, not mission measurements",**inv,"verified_traces":traces(log),
            "proposal_specification":protected_spec(),"T_s":int(T),"delta":str(DELTA),
            "all_budget_dangerous_rate_ceiling_per_s":str(threshold),
            "all_budget_dangerous_FIT":str(threshold*D("3.6e12")),
            "uniform_raw_rate_ceiling_326_FF_p_equals_1":str(threshold/inv["total_FF"]),
            "upper_possible_active_scans":str(full_scan_bound),"single_path_limits":windows,
            "illustration":conditional,
            "conditional_register_rate_ceiling_after_1e_6_other_and_common_each":str(D("4e-6")/T),
            "illustrative_hot_CLB_FF_150MeV_only":{
                "count":273,"plot_estimate_cm2_per_bit":"1e-14",
                "budget_flux_ceiling_cm-2_s-1_if_all_273_FFs_dangerous":str(threshold/(273*D("1e-14")))},
            "GEO_physical_dangerous_rate_upper":None,"physical_delta_established":False,
            "recovery_price_seconds_per_additional_cell":"20.397479",
            "next_eligible_common_cell_ns":512*L_NS,
            "rebuild_three_full_clean_cells_ns":3*512*L_NS}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--traces",type=Path,default=HERE/"observations.txt")
    p.add_argument("--write",type=Path)
    a=p.parse_args()
    result=json.dumps(evaluate(a.traces),indent=2,sort_keys=True)+"\n"
    if a.write: a.write.write_bytes(result.encode("utf-8"))
    elif result!=(HERE/"results.json").read_text(): raise SystemExit("Result differs")
    print(result)
