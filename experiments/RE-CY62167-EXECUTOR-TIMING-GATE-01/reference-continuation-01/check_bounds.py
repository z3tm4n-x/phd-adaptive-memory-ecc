"""Independent Decimal checker: no imports from calculate.py or witness.py."""
import csv, hashlib, io, json, subprocess
from decimal import Decimal as D, localcontext
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def verify():
    with localcontext() as ctx:
        ctx.prec=95
        c=json.loads((ROOT/"config.json").read_text())
        assert (c["words"],c["period_ticks"],c["slot_ticks"],c["prep_lead_ticks"])==(524288,100000000,24,20000000)
        raw=subprocess.check_output(["git","show",c["rate_commit"]+":"+c["rate_path"]],cwd=ROOT.parents[2])
        assert hashlib.sha256(raw).hexdigest()==c["rate_sha256"]
        records=list(csv.DictReader(io.StringIO(raw.decode())))
        assert len(records)==288
        r=[D(x["r_bit_s_1"]) for x in records]
        assert all(x>=0 for x in r)
        second=D(10)**9
        fastest=D(10)/D("1.00005")
        slowest=D(10)/D(".99995")
        duration=(24*slowest+D(".5"))/second
        minperiod=(100000000*fastest-D(".5"))/second
        maxperiod=(100000000*slowest+D(".5"))/second
        pre=(20000000*slowest+D(".5"))/second
        # Exhaustive first-gap and reservation-spacing enumeration, not a
        # closed-form endpoint assumption from the production calculator.
        prev=None; largest=0; minimum_space=100000000
        for w in range(524288):
            start=(w*100000000)//524288
            if prev is not None: minimum_space=min(minimum_space,start-prev)
            largest=max(largest,start+24-(-20000000+(w+1)*24))
            prev=start
        assert minimum_space>=24 and 100000000-prev>=24
        L=max(maxperiod,(largest*slowest+D(".5"))/second)
        # Independent packing/count argument via feasible start separation.
        count=1
        while D(count)*minperiod<=300+duration: count+=1
        integral_sq=sum(v*v*300 for v in r)
        integral=sum(r)*300
        factor=D(524288)*32*31/2
        a=factor*L*integral_sq+32*524288*duration*count*sum(r)
        b=32*524288*duration
        cc=factor*L*pre
        upper=a+b*max(r)+cc*max(r)**2
        out=json.loads((ROOT/"bounds.json").read_text())
        def value(key):
            f=Fraction(out[key]["exact"])
            return D(f.numerator)/D(f.denominator)
        for key,expected in {
          "tube_s":duration,"gap_max_s":L,"constant_A":a,"linear_B":b,
          "quadratic_C":cc,"U_exec":upper,"signed_slack":D(".001")-upper,
          "I1":integral,"I2":integral_sq,"r_pre_named":max(r)
        }.items():
            assert abs(value(key)-expected)<D("1e-70"),(key,value(key),expected)
        assert out["first_gap_ticks"]==largest
        assert out["block_tube_count_per_word"]==count==301
        lo=value("r_pre_limit_lower"); hi=value("r_pre_limit_upper")
        assert a+b*lo+cc*lo*lo<=D(".001")
        assert a+b*hi+cc*hi*hi>D(".001")
        assert 0<hi-lo<D("1e-50") and max(r)<lo
        # Independent exact accepted-control constants, not copied from bounds.
        ideal_a=Fraction("0.0003098157772336203819978391463469440873")
        ideal_b=Fraction("2528.1037181797039690725")
        threshold=(Fraction(".001")-ideal_a)/ideal_b
        assert Fraction(out["ideal_a_upper"]["exact"])==ideal_a
        assert Fraction(out["ideal_b"]["exact"])==ideal_b
        assert Fraction(out["ideal_delta_star"]["exact"])==threshold
        assert ideal_a+ideal_b*threshold==Fraction(".001")
        return {"status":"PASS","arithmetic":"Decimal 95 digits vs exact Fraction; tolerance 1e-70",
          "independent_scope":"all 524288 first gaps, spacing, coefficients, certified root bracket, accepted ideal control",
          "shared_inputs":"same hashed rate CSV, fixed config, declared proof; not independent scientific evidence",
          "minimum_word_spacing_ticks":minimum_space,"U_exec":str(upper),"signed_slack":str(D(".001")-upper)}
if __name__=="__main__":
    print(json.dumps(verify(),indent=2))
