"""Independent checks at the registered point; no search over policies."""
from fractions import Fraction as F
import json
from math import ceil
from basis import HERE,verified


def history(events):
    """State at the next common boundary. An invalid report cannot cancel the current cell."""
    z=0
    modes=[]
    for valid,count in events:
        modes.append('slow' if z==730 else 'fast')
        z=min(z+1,730) if valid and count==0 else 0
    return modes


def check():
    src=json.loads((HERE/'result.json').read_text(encoding='utf-8'))
    fixed=verified('six.json')
    r=next(r for r in fixed['rows'] if r['W']==65536 and F(r['epsilon'])==F(1,1000))
    W=r['W'];T=F(fixed['T']);D=F(fixed['D']);L=F(196*W,10**9);P=32*L;ns=F(1,10**9)
    xm=F('0.99999');xp=F('1.00001');j=ns/2
    assert P==F(src['slow_step_s']) and 729*P<300<=730*P
    assert set(history([(False,0)]*2000))=={'fast'}
    modes=history([(True,0)]*730+[(False,0)]+[(True,0)]*731)
    assert modes[:730]==['fast']*730 and modes[730]=='slow'
    assert modes[731:1461]==['fast']*730 and modes[1461]=='slow'
    for bad in [(True,1),(False,0)]:
        modes=history(([(True,0)]*729+[bad])*3)
        assert 'slow' not in modes
    H=src['history_certificate']
    total=F('0.000006')+F('0.000222332599')+F('0.000439149335')+2*F('0.000092519858')
    assert total==F('0.000852521650') and F(ceil(total*10**9),10**9)==F(H['priced_q'])
    assert total+F(1,10000)<F(1,1000)<F(src['anchored_Q_upper'])
    broad=src['without_a_visibility_floor'];cert=H['numeric_replay']
    assert F(broad['joint_stops_upper_eq3'])==F('0.000006')+F(cert['fast_exact'])+F(cert['unweighted_slow_pairs'])
    assert F(broad['joint_stops_upper_eq3'])>F(broad['physical_Q_upper_from_core'])
    # Different thresholds use different ends of the same optimum enclosure.
    best_lower=F(r['necessary']['bus_lower_s'])
    best_upper=F(r['candidate']['price']['bus']['upper_s'])
    q=F(H['priced_q']);cap=F(r['necessary']['maximum_reads_upper'])
    rd=48*xp*ns+j;wr=56*xp*ns+j
    floor_reads=F(T//L*W)*48*ns
    assert floor_reads==F(src['persistent_invalid']['known_read_lower_s'])>best_upper/2
    frame_reads=8*((T/ns)//1568)
    assert floor_reads<=frame_reads*48*ns  # route includes eight real reads in each full frame
    dur=P*xp+2*j;minimum=P*xm-2*j;mu2=2*W*39*187464/D
    eta0=src['zero_invalid_budget']
    tf=min(T,L*xp+j+731*dur*(1+mu2)+q*T)
    assert tf==F(eta0['E_Tfast_upper_s'])
    cells=T/minimum+2
    passes=min(ceil(T/(L*xm-2*j))+2,cells+31*(tf/minimum+2))
    reads=min(cap,W*passes);repairs=min(reads,mu2+q*cap)
    primary=reads*rd+repairs*wr
    assert primary==F(eta0['known_primary_bus_upper_s'])
    assert best_lower/2-primary==F(eta0['signed_sufficient_extra_bus_s'])>0
    slot=src['bounded_full_service']
    frames=ceil((T+2*j)/(1568*xm*ns))+2
    reserved=frames*(64*xp*ns+j)
    assert F(slot['full_bus_upper_s'])==cap*rd+min(cap,mu2+q*cap)*wr+reserved
    assert floor_reads>(best_upper+reserved)/2
    # Independent outward comparison with the published C2 numerical replay.
    source=src['C2_general_hard_caps']
    assert F(source['eta0_primary_total_bus_s_upper'])<=F('6049126.074')
    assert F('1984875.853')<=F(source['eta0_full_extra_s_budget'])<F('1984875.854')
    assert F(source['extra_bus_s_per_invalid'])<=F('72.03006')
    assert F(source['eta0_E_Tfast_upper_s'])<=F('14721956.497')
    assert ceil(F(source['eta0_E_switch_upper_given_cell_command_cap']))==750728
    assert F(source['post_stop_word_visits_upper'])==q*cap and F(source['eta0_repairs_upper'])==mu2+q*cap
    N=T//P
    witness=src['prefix_witness'];count=witness['first_invalid_resets_proving_exclusion']
    def lower(i):return (N+31*min(N,(i+1)*730))*W*48*ns
    assert lower(count-1)<=best_upper/2<lower(count)==F(witness['word_read_bus_lower_s'])
    budget=src['eta_for_primary_only']
    def price(i):
        t=min(T,tf+731*dur*i)
        n=min(cap,W*(cells+31*(t/minimum+2)))
        return rd*n+wr*min(n,mu2+q*cap)
    assert price(budget['last_integer_meeting'])<=best_lower/2<price(budget['first_integer_exceeding'])
    assert F(src['peak']['all_slot_bus_upper_percent'])<F(src['peak']['all_slot_serial_upper_percent'])<80
    print('PASS: registered transitions, two price thresholds, risk, post-stop charges, I budgets and complete bus ceiling')


if __name__=='__main__':check()
