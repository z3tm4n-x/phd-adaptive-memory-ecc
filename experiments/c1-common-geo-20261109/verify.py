"""Independent rational checks of all class tails, upper witnesses and lifetime bus prices."""
import json
from fractions import Fraction as F
from math import ceil
from pathlib import Path

HERE=Path(__file__).resolve().parent


def check():
    data=json.loads((HERE/'six.json').read_text(encoding='utf-8'))
    cov=json.loads((HERE/'coverage.json').read_text(encoding='utf-8'))
    growth=json.loads((HERE/'growth.json').read_text(encoding='utf-8'))
    assert all(v['exact_feasible'] is True and v['constructed_feasible'] and v.get('within_exposure_quota',True)
               for v in growth['profiles'].values())
    T=F(data['T']);D=F(data['D']);b=F(cov['b_s_inv']);B=F(cov['B_s_inv']);Fsun=F(data['F'])
    tau=Fsun/(B-b); S1=F(cov['S1_cap']); S2=(T-tau)*b*b+tau*B*B
    assert S2==F(data['S2_max']) and b*T+Fsun==S1
    assert (F(cov['old_S1'])<F.from_float(cov['SEPEM']['max_S1_by_fsum'])<S1)
    assert cov['SEPEM']['above_T141']==706163 and not cov['SEPEM']['above_cap']
    for direction,v in cov['GOES'].items():
        k='GOES_composite_5min_'+direction
        assert abs(v['S1_obs']+v['allowed_unobserved_total']-S1)<1e-8
        assert growth['profiles'][k]['witness_excess_on_gaps']<=v['allowed_unobserved_excess']<v['peak_only_excess_ceiling']
    xm=F(99999,100000);xp=F(100001,100000);j=F(1,2*10**9)
    aperture=F(124,10**9)*xp+3*j
    delta=F(3,500000)
    def low(w,p):
        pieces=ceil((tau-1)/120);L=(tau-1)/pieces
        m=L/p+2;word=39*B/D
        z=pieces*w*F(38,78)*(1-word*L)*word**2*max(0,L-m*aperture)**2/(1+m)
        return max(0,z/(1+z)-delta)
    for r in data['rows']:
        w=r['W'];eps=F(r['epsilon']);c=r['continuous'];n=r['necessary'];a=r['candidate']
        period=F(w*196,10**9);factor=F(39*38*w,2*D**2)
        def upper(k):return min(1,delta+factor*((period*k*xp+j+aperture)*S2+2*B*aperture*S1))
        assert F(c['risk']['total'])==upper(1) and F(c['Q_lower'])==low(w,period*xp)
        left,right=map(F,n['witness_threshold_bracket_s'])
        assert low(w,left)<=eps<low(w,right) and right-left<=F(1,10**11)
        need=(1-delta)*w*(T/(right+j)-2)
        assert F(n['required_reads_lower'])==need
        assert F(n['bus_lower_s'])==need*(48*xm/10**9-j)
        if a:
            k=a['k'];q=upper(k)
            assert q==F(a['risk']['total'])<=eps<upper(k+1)
            available=F(n['maximum_reads_upper']);reads=min(available,w*(T/(period*k*xm-j)+2)+delta*available)
            repairs=min(reads,2*39*w*S1/D+q*available)
            bus=reads*(48*xp/10**9+j)+repairs*(56*xp/10**9+j)
            assert F(a['price']['bus']['upper_s'])==bus>=F(n['bus_lower_s'])
        else:assert need>F(n['maximum_reads_upper'])
    small=[r for r in data['rows'] if F(r['epsilon'])==F(1,1000)]
    assert [r['candidate']['k'] for r in small]==[18,4,1]
    assert F(small[0]['candidate']['price']['bus']['upper_percent'])<5<F(small[1]['necessary']['bus_lower_percent'])
    strict=data['rows'][1]
    assert F(strict['k2']['Q_all_k_ge2_lower'])<F(strict['epsilon'])<F(strict['k2']['Q_k2_upper'])
    print('PASS: exposure, all six probability tails, lifetime prices, 5% and unresolved k=2')


if __name__=='__main__':check()
