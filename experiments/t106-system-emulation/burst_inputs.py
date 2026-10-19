"""Declared R0-A-amplitude / T67-temporal-shape stand input, not calibration."""
import argparse
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import random
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
BG=0.000154704
SOLAR=0.244528
BOUND=BG+SOLAR
SEED=10620261014


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def growth_bound(rates):
    """Sup H_l'(nu)*nu' on each affine segment, also BELOW ell."""
    return max((max(0,b-a)/60/max(a,0.001) for a,b in zip(rates,rates[1:])),default=0)


def derive():
    source=HERE/'outputs/t67-profile.json.gz'
    audit=json.loads((HERE/'outputs/t67-profile.json').read_text())
    assert sha(source)==audit['profile_sha256']
    with gzip.open(source,'rt') as f:raw=json.load(f)
    records=raw['records'];assert len(records)==6065 and raw['duration_s']==60
    assert all(b[0]-a[0]==60 for a,b in zip(records,records[1:]))
    assert all(v is not None and math.isfinite(v) and v>=0 and ok for _,v,ok in records)
    peak=max(v for _,v,_ in records)
    solar=[SOLAR*v/peak for _,v,_ in records]
    rates=[BG+s for s in solar]
    rates.append(rates[-1]);solar.append(solar[-1])
    exposure=math.fsum(30*(a+b) for a,b in zip(rates,rates[1:]))
    solar_exposure=math.fsum(30*(a+b) for a,b in zip(solar,solar[1:]))
    square=math.fsum(20*(a*a+a*b+b*b) for a,b in zip(rates,rates[1:]))
    # H_l: relative growth at the smallest eligible rate on a rising segment.
    rel_growth=growth_bound(rates)
    assert max(rates)<=BOUND*(1+2e-15)
    assert solar_exposure<=28310.473728
    assert rel_growth<=0.048,('H_l input does not close',rel_growth)
    horizon=60*len(records)
    rng=random.Random(SEED);t=0;events=[];proposals=0
    while True:
        t+=-math.log1p(-rng.random())/BOUND
        if t>=horizon:break
        proposals+=1;i=min(int(t//60),len(records)-1);u=(t-i*60)/60
        rate=rates[i]+u*(rates[i+1]-rates[i])
        if rng.random()*BOUND>=rate:continue
        # Ceiling to relative2 mod4 ns, never move an event earlier.
        ns=2+4*math.ceil((t*1e9-2)/4)
        assert 0<=ns-t*1e9<4.1 and ns<horizon*1_000_000_000
        word=rng.getrandbits(19)
        bit=rng.getrandbits(6)
        while bit>=38:bit=rng.getrandbits(6)
        events.append(dict(at_ns=ns,word=word,bit=bit,parent=len(events)+1))
    table=dict(utc_start=records[0][0],duration_s=60,rate_per_array_s=rates,
               interpolation='linear adjacent bin-start knots; final bin constant')
    stimulus=dict(scenario='burst',horizon_ns=horizon*1_000_000_000,
        initial_data='0xa5a50000 XOR word',initial_errors=0,injections=events,applications=[],
        false_ERR_interval_ns=[0,0],loss_slow_interval_ns=[0,0],ready_low_ns=80,ready_period_ns=340)
    report=dict(scope='declared digital R0-A envelope subcase; NOT physical response calibration',
        source_sha256={p.relative_to(REPO).as_posix():sha(p) for p in
            (source,HERE/'outputs/t67-profile.json',HERE/'burst_inputs.py',HERE/'BURST.md',
             REPO/'theory/t135-demo-operating-point.md')},
        horizon_s=horizon,peak_rate_per_s=max(rates),solar_expected_parents=solar_exposure,
        expected_parents=exposure,integral_rate_squared_per_s=square,
        max_H_l_relative_growth_per_s=rel_growth,seed=SEED,proposals=proposals,
        generated_parents=len(events),python=sys.version,policy_execution=False,
        unknowns=['physical calibration of this normalized temporal shape','mission Q(T)','hardware ARM time'])
    return table,stimulus,report


def blob(value):
    out=io.BytesIO()
    with gzip.GzipFile(fileobj=out,mode='wb',mtime=0,filename='') as f:
        f.write((json.dumps(value,separators=(',',':'))+'\n').encode())
    return out.getvalue()


def verify(record=False):
    table,stimulus,report=derive()
    for name,value in (('burst-rate',table),('burst-stimulus',stimulus)):
        p=HERE/f'outputs/{name}.json.gz';content=blob(value)
        if record:p.write_bytes(content)
        else:assert p.read_bytes()==content,('input changed',p.name)
        report[name+'_sha256']=sha(p)
    p=HERE/'outputs/burst-input.json'
    if record:p.write_text(json.dumps(report,indent=2)+'\n')
    else:
        old=json.loads(p.read_text());old.pop('python');report.pop('python');assert old==report
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();verify(a.record)
