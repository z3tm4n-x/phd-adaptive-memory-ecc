"""Directed checks of the preparatory codec and cost calculation, not Q proofs."""
from dataclasses import replace
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib
import json
import random

from codec import Code, t187
from cost import (Work, packing, work_vector, affine_prices, evaluate, threshold,
                  allowable_delay, periodic_starts, clipped_busy, per_bit_moment_caps)
from cost import fast_fraction_cap
from parents import projected_groups, witness_coefficients, fixed_u_moment_terms


def run():
    checks = []
    correction_cases = 0

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def rejects(name, function):
        try:
            function()
        except (ValueError, ArithmeticError):
            checks.append(name)
            return
        raise AssertionError(name + " was not rejected")

    rng = random.Random(18620261022)
    payloads = [0, (1 << 32)-1, 0xAAAAAAAA, 0x55555555] + [1 << i for i in range(32)]
    payloads += [rng.getrandbits(32) for _ in range(8)]
    for t in (1, 2):
        code = Code(t)
        independent = t187.code_check(t)
        check(f"t{t}: H equals accepted construction", list(code.columns) == independent["columns"])
        check(f"t{t}: systematic dimension", code.k == 32 and len(code.generator) == 32)
        check(f"t{t}: all correctable syndromes distinct", sum(x is not None for x in code.table) == independent["distinct_correctable_syndromes"])
        errors = [0] + [sum(1 << i for i in inds) for weight in range(1,t+1)
                        for inds in combinations(range(code.n),weight)]
        for data in payloads:
            word = code.encode(data)
            if code.syndrome(word) != 0:
                raise AssertionError("encoder violates H")
            for error in errors:
                result = code.decode(word ^ error)
                if result["data"] != data or result["corrected_word"] != word or result["ERR"] != bool(error):
                    raise AssertionError((t,data,error,result))
                correction_cases += 1
        check(f"t{t}: all low-weight errors on zero, payload bases and fixed words", True)
        for data in payloads:
            word = code.encode(data)
            beats = list(code.pack16(word))
            # Independently check every physical code coordinate and the ignored padding.
            for bit in range(code.n):
                changed = beats.copy(); changed[bit//16] ^= 1 << (bit%16)
                if code.unpack16(changed) != word ^ (1 << bit):
                    raise AssertionError("x16 mapping")
            beats[-1] |= 65535 ^ ((1 << (code.n-32))-1)
            if code.unpack16(beats) != word:
                raise AssertionError("padding entered codeword")
        check(f"t{t}: x16 position mapping and padding", True)
        res = code.resources()
        check(f"t{t}: ROM charged including invalid addresses", res["lookup_bits"] == (1 << code.r)*(code.n+1))
        rejects(f"t{t}: oversized payload rejected", lambda: code.encode(1 << 32))
        rejects(f"t{t}: unmasked word rejected", lambda: code.decode(1 << code.n))
        rejects(f"t{t}: incomplete codeword read rejected", lambda: code.unpack16((0,0)))

    # A valid syndrome is not proof of a <=t corruption: keep the first-hit
    # event distinct from decoder status, including t2 miscorrection.
    code = Code(2)
    miscorr = next((tuple(inds) for inds in combinations(range(44),3)
                   if code.decode(sum(1 << i for i in inds))["corrected_word"] not in (None,0)), None)
    check("t2: beyond-radius event can have a correctable syndrome", miscorr is not None)

    a, b = packing(131072,39), packing(131072,44)
    check("common useful volume", a["useful_bits"] == b["useful_bits"] == 8*524288)
    check("integer bus allocation equal", a["allocated_bits"] == b["allocated_bits"] == 8*786432)
    check("padding is not code exposure", a["unused_bits_per_word"] == 9 and b["unused_bits_per_word"] == 4)
    check("full observed RMW six beats", a["observed_RMW_beats"] == b["observed_RMW_beats"] == 6)
    rejects("noninteger geometry rejected", lambda: packing(F(3,2),39))

    work = Work(*map(F, (11,7,5,3,2,19,13,100,12,31,17,2)))
    res = Code(2).resources()
    v = work_vector(work,44,res)
    check("all reads decoded including RMW", v["decodes"] == 23 and v["sram_read_beats"] == 69)
    check("RMW one final write, no duplicated repair", v["sram_write_beats"] == 30 and v["encodes"] == 5)
    check("payload directions counted once", v["payload_data_bytes"] == 48)
    check("captured lost/pending records still cost", v["source_record_bytes"] == 416 and v["processed_record_bytes"] == 384)
    p = affine_prices(v,10000)
    vals = dict(read_beat_ns=2,write_beat_ns=3,turnaround_ns=1,decode_bus_block_ns=4,
                encode_bus_block_ns=5,control_bus_ns_per_decision=6)
    expected = F(69*2+30*3+19+23*4+5*5+31*6,10000)
    check("full bus affine expression against manual sum", evaluate(p["SRAM_fraction"],vals) == expected)
    rejects("unknown cost cannot default to zero", lambda: evaluate(p["SRAM_fraction"],{}))
    check("zero work coefficient needs no unit cost", evaluate({"unknown":F(0)},{}) == 0)
    rejects("binary-float unit cost rejected", lambda: evaluate({"x":F(1)},{"x":0.1}))
    rejects("incorrect constant scale rejected", lambda: evaluate({"constant_one":F(10)},{"constant_one":0}))
    rejects("stop-at-A work rejected", lambda: work_vector(replace(work,scope="until_first_failure"),44,res))
    rejects("repair without read rejected", lambda: work_vector(replace(work,scrub_repairs=F(12)),44,res))
    rejects("codec geometry mismatch rejected", lambda: work_vector(work,39,res))
    # Full-started-work is conservative for a pending last operation, and
    # accounting continues after an arbitrary absorbing-event marker at 4.
    trace = [(F(0),F(3)),(F(5),F(8)),(F(9),F(12))]
    check("pending clipped at horizon, post-A retained", clipped_busy(trace,10) == 7)
    check("full started charge covers unfinished tail", sum(b-a for a,b in trace) >= clipped_busy(trace,10))
    rejects("overlapping serial reservations rejected", lambda: clipped_busy([(0,5),(4,6)],10))
    for start,step,H in [(0,3,10),(2,3,10),(0,3,9),(10,3,10),(12,3,10),(F(1,2),F(3,2),5)]:
        direct = sum(start+j*step < H for j in range(20))
        if periodic_starts(start,step,H) != direct:
            raise AssertionError("integer endpoint count")
    check("finite horizon and endpoints versus enumeration", True)
    check("switch threshold", threshold(1,2,7,0) == {"region":"0<=x<point","equality":F(3)})
    check("reversed switch", threshold(7,0,1,2) == {"region":"x>point and x>=0","equality":F(3)})
    check("identical prices do not imply strict winner", threshold(1,2,1,2)["region"] == "none")
    check("negative crossover excluded from nonnegative domain", threshold(7,2,1,0)["region"] == "none")
    check("constant strict dominance", threshold(1,2,3,2)["region"] == "all x>=0")
    check("allowable delay is remaining budget", allowable_delay(9,3,30) == {"feasible":True,"maximum":F(7)})
    check("negative timing margin cannot be hidden", allowable_delay(31,3,30)["feasible"] is False)
    check("zero operations do not imply zero allowed delay", allowable_delay(9,0,30)["maximum"] is None)
    # Small unrelated rational envelope is a unit check, not a comparison row.
    cfg = {"mission_s":4,"environment":{"kind":"conditional_independent_singleton_per_code_bit",
           "reference_words":2,"reference_bits":4,"reference_background_per_s":8,
           "reference_peak_per_s":24,"reference_solar_mass":16}}
    m = per_bit_moment_caps(cfg)
    check("per-bit moment normalization", m == {"M1":F(6),"M2":F(12),"M3":F(30),"peak_per_bit":F(3)})
    check("n-dependent exposure", (44*3)**2* m["M2"] / ((39*3)**2*m["M2"]) == F(44,39)**2)
    rejects("compound law cannot use singleton moment shortcut", lambda: per_bit_moment_caps({**cfg,"environment":{**cfg["environment"],"kind":"compound"}}))
    for N in range(2,8):
        for n in range(1,N+1):
            for size in range(1,N+1):
                actual=projected_groups(n,{size:F(1)},N)
                masks=list(combinations(range(N),size))
                oracle=[F(N,size)*F(sum(sum(x<n for x in mask)==j for mask in masks),len(masks)) for j in range(n+1)]
                if actual!=oracle:
                    raise AssertionError(("hypergeometric subset oracle",N,n,size))
    check("parent projection versus complete small subset enumeration",True)
    for n,t in ((39,1),(44,2)):
        single=projected_groups(n,{1:F(1)})
        check(f"n{n}: singleton active rate equals n*r",single[1]==n and sum(single[2:])==0)
        mixed=projected_groups(n,{1:F(1,2),2:F(1,3),3:F(1,6)})
        check(f"n{n}: conservation of bit hits",sum(j*v for j,v in enumerate(mixed))==n)
        coeff=witness_coefficients(n,t,mixed)
        exposure=F(7,11)
        if t==1:
            oracle=t187.phi(n,1,mixed[1]*exposure)
        else:
            oracle=t187.phi(n,2,mixed[1]*exposure,mixed[2]*exposure)
        check(f"n{n}: mixed polynomial equals T187 phi",coeff['quadratic']*exposure**2+coeff['cubic']*exposure**3==oracle)
        check(f"n{n}: projected direct retained",coeff['linear_direct']>0)
    rejects("parent bit shares must sum to one",lambda:projected_groups(39,{1:F(1,2)}))
    rejects("parent size above physical word rejected",lambda:projected_groups(39,{49:F(1)}))
    coeff=witness_coefficients(4,2,projected_groups(4,{1:F(1)},4))
    pieces=fixed_u_moment_terms(2,F(1,2),m,coeff)
    check("U algebra remains explicitly incomplete for E",pieces['cubic']==60 and pieces['E_window_term'] is None and pieces['initial_other_budget'] is None)
    check("extra confirmations can consume all FAST time",fast_fraction_cap(F(1,10),F(1))==1)
    check("additional veto not treated as another episode",v['extra_source_veto']==2 and p['CPU_fraction']['CPU_ns_per_extra_veto']==F(2,10000))
    rejects("veto count needs real records",lambda:work_vector(replace(work,extra_source_veto=F(14)),44,res))
    return {"status":"preparatory_implementation_checks_only", "count":len(checks), "checks":checks,
            "correction_cases":correction_cases, "payload_count_per_code":len(payloads),
            "beyond_radius_t2_miscorrection_example":list(miscorr),
            "comparative_probability_runs":0, "old_stage4_matrix_rerun":False,
            "independent_scientific_review":False}


if __name__ == "__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
