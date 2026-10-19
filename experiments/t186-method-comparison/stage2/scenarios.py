"""Frozen synthetic episodes; not a fitted radiation process or full Theta."""
import hashlib
import json
import math
from pathlib import Path
import random

NS = 1_000_000_000


def dumps(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n'


def save(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(dumps(value),encoding='utf-8',newline='\n')


def digest(value):
    return hashlib.sha256(dumps(value).encode('utf-8')).hexdigest()


def segments(ep, env):
    b,B = float(env['background_per_s']),float(env['peak_per_s'])
    H = ep['horizon_s']
    if ep['shape']=='quiet':
        return [(0,H,b,b)]
    out=[]
    if ep['shape']=='initial_peak':
        h,f=ep['initial_hold_s'],ep['fall_s']
        return [(0,h,B,B),(h,h+f,B,b),(h+f,H,b,b)]
    starts=[ep['peak_start_s']]
    if ep['shape']=='repeat_rise':
        starts.append(ep['repeat_start_s'])
    last=0
    for s in starts:
        r,h,f=ep['rise_s'],ep['hold_s'],ep['fall_s']
        assert s>=last and s+r+h+f <= H
        out += [(last,s,b,b),(s,s+r,b,B),(s+r,s+r+h,B,B),(s+r+h,s+r+h+f,B,b)]
        last=s+r+h+f
    out.append((last,H,b,b))
    return out


def rate(t, parts):
    for a,b,x,y in parts:
        if a<=t<b:
            return x if x==y else x*math.exp(math.log(y/x)*(t-a)/(b-a))
    return 0.


def generate(ep,cfg):
    rng=random.Random(ep['seed'])
    uniform=lambda:(rng.getrandbits(53)+1)/(2**53+1)
    B=float(cfg['environment']['peak_per_s'])
    parts=segments(ep,cfg['environment'])
    t=0.; marks=[]; candidates=0
    while True:
        t += -math.log(uniform())/B
        if t>=ep['horizon_s']:
            break
        candidates += 1
        if uniform() <= rate(t,parts)/B:
            marks.append(dict(t=math.ceil(t*NS),word=rng.randrange(cfg['memory']['words']),
                              bit=rng.randrange(cfg['memory']['bits'])))
    ap=cfg['application']
    apps=[dict(arrival_ns=t*NS,word=ap['word']) for t in range(ap['first_s'],ep['horizon_s'],ap['period_s'])]
    return dict(episode=ep['id'],split=ep['split'],horizon_ns=ep['horizon_s']*NS,seed=ep['seed'],
                candidate_count=candidates,marks=marks,applications=apps)


def benchmark_marks(n,horizon_s,seed,words=524288):
    rng=random.Random(seed)
    H=horizon_s*NS
    return sorted([dict(t=rng.randrange(H),word=rng.randrange(words),bit=rng.randrange(38)) for _ in range(n)],
                  key=lambda x:x['t'])
