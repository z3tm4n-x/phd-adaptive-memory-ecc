"""Independent window sums, phase and mask checks and explicit gap counterexample."""
import argparse
from fractions import Fraction as F
import json
import math
from pathlib import Path
import numpy as np
from observations import DT,T,WIDTH,HERE,setup,save
from strict import conflict_pairs,window_coverage,G_MAIN,G_STRICT


def feasible(v,R,g,step):
    U=R;a=g*step
    for mean in v:
        bound=U+a/2 if U+a<=R else R-(R-U)**2/(2*a)
        if mean>bound+1e-13:return False
        new=math.sqrt(2*a*mean) if mean<=a/2 else mean+a/2
        U=min(U+a,R,new)
    return True


def tiny():
    bad,_=conflict_pairs(np.array([0.,.8]),np.array([0,1]),1,3.,1.)
    assert bad==[(0,1)]  # Adjacent change <=g, but a rising bin from zero can average only g/2.
    rng=np.random.default_rng(413)
    for _ in range(50):
        v=rng.random(16)*.8;t=np.arange(len(v));rate=.19
        bad,_=conflict_pairs(v,t,1,1.,rate)
        for width in [2,4,7]:
            mask=window_coverage(len(v),width,bad)
            assert all(bool(fail)!=feasible(v[i:i+width],1.,rate,1) for i,fail in enumerate(mask))


def check(args):
    common,old=setup(args.common,args.previous)
    coverage=json.loads((common/'coverage.json').read_text(encoding='utf-8'))
    from coverage import sepem_series, environment
    nu,_,_,_,info=sepem_series(args.sepem_cache,old)
    m=nu-info['background_per_s'];z=np.r_[m[0],np.minimum(m[:-1],m[1:])];p=2*(m-z)
    result=json.loads((HERE/'variation.json').read_text(encoding='utf-8'))
    g=json.loads((HERE/'strict.json').read_text(encoding='utf-8'))
    U=F(result['quota_exact'])
    for kind,x in result['SEPEM']['maxima'].items():
        i=x['index']
        if kind=='bin_lower':value=m[i]+math.fsum(np.maximum(np.diff(m[i:i+WIDTH]),0.))
        else:
            start=z[i] if kind=='aligned_reconstruction' else z[i-1]+p[i-1]
            value=start+math.fsum(p[i:i+WIDTH])
        assert math.isclose(value,x['value_s_inv'],rel_tol=3e-15)
    # Also verify the common exposure for starts between bin edges.
    a=z[WIDTH:]-z[:-WIDTH];c=p[WIDTH:]-p[:-WIDTH]
    inside=(c<0)&(a>0)&(a<-c)
    phase=np.zeros(len(c));phase[inside]=-a[inside]/c[inside]
    with np.load(args.windows) as src:s1=src['S1']
    vals=s1[:-1]+DT*(a*phase+.5*c*phase**2)
    peak_id=int(np.argmax(vals));peak=max(float(vals[peak_id]),float(np.max(s1)))
    assert peak<187464
    assert g['SEPEM']['nominal']['windows_passing_exact']==len(s1)
    strict=g['SEPEM']['strict5']
    assert strict['windows_failing_exact']==strict['windows_with_adjacent_violation']==2656315
    assert sum(v['windows'] for v in g['strict_joint_witnesses'])==strict['windows_passing_exact']==657558
    assert all(F(v['exact'])<U for v in g['strict_joint_witnesses'])
    # A sparse strict mask is a distinct sensitivity input, not the full screened record.
    sums={d:sum(row['strict_adjacent_pairs'] for k,row in g['native_replay'].items() if k.endswith(d)) for d in ('1min','5min')}
    assert sums=={'1min':0,'5min':787}
    env,_,Fsun=environment();R=env['B']-env['b']
    assert R<U and all(v['headroom_after_reconstruction']>=0 for v in result['GOES'].values())
    # In the long initial GOES gap, prepend ramps from 0 to a and an allowed
    # downward jump; no measured value changes. This keeps peak, growth and exposure.
    amp=F(1,100);count=U//amp+1
    counter={}
    for gvalue in (G_MAIN,G_STRICT):
        rise=amp/F(str(gvalue));dur=count*rise;exposure=count*amp*rise/2
        # For nominal g, use the PR423 completion. For strict g this counterexample
        # refers to the strict-only G16 data, for which the same initial gap exists.
        assert dur<200*86400 and exposure<10000 and count*amp>U
        if gvalue==G_MAIN:
            bases=[]
            for name in ('East','West'):
                v=result['GOES']['composite_5min_'+name]
                total=float(env['b']*T)+coverage['GOES'][name]['observed_excess']+v['reconstruction_excess_integral_on_holes']
                bases.append((v['leading_gap_s'],total))
        else:
            cores=[v['strict_completion'] for v in g['native_replay'].values() if 'strict_completion' in v]
            bases=[(v['leading_gap_s'],v['total_S1']) for v in cores]
        assert len(bases)==2 and all(dur+86400<gap and initial+float(exposure)<187464 for gap,initial in bases)
        counter[str(gvalue)]={'pulses':int(count),'amplitude_s_inv':float(amp),'duration_s':float(dur),
                              'added_exposure':float(exposure),'added_variation_s_inv':float(count*amp)}
    return {'max_S1_arbitrary_phase':peak,'max_S1_start_bin':peak_id,'max_S1_phase_s':float(phase[peak_id]*DT),
            'variation_quota':float(U),'plateau_charge':float(R),'gap_counterexample':counter}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('common','previous','sepem-cache','windows'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--check',action='store_true');args=p.parse_args();tiny();r=check(args)
    save('checks.json',r,args.check)
    print('PASS: direct variation, independent binned feasibility, exact strict witnesses, phase/exposure and gap counterexample')
