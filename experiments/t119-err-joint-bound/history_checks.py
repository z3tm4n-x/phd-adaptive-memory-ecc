"""Addressed admissible histories, not a simulation or a class certificate.

All integrals use exact polynomials or outward exp primitives. Full-size
mandatory phases are retained. These checks diagnose the joint event; they
do not select parameters or replace the uniform proof.
"""
from fractions import Fraction as F
import joint as j
from intervals import I
from rule import Rule


def segment(l,r,a,k=F(0),exponential=False):
    return dict(l=F(l),r=F(r),a=a if isinstance(a,I) else I(a),
                k=F(k),exponential=exponential)


def integrate(segments,l,r,offset=F(1),slope=F(0)):
    """Enclose integral nu(t)*(offset+slope*t) on [l,r]."""
    total=I(0)
    for s in segments:
        left,right=max(l,s['l']),min(r,s['r'])
        if right<=left:continue
        a,k,base=s['a'],s['k'],s['l']
        c=offset+slope*base
        def primitive(x):
            xx=I(x)
            if s['exponential']:
                return a*(I(k)*xx).exp()*(I(c)/I(k)+I(slope)*(xx/I(k)-I(1)/I(k*k)))
            return a*I(c)*xx+(a*I(slope)+I(k*c))*xx*xx/I(2)+I(k*slope)*xx*xx*xx/I(3)
        total=total+primitive(right-base)-primitive(left-base)
    return total


def profiles(p):
    b,B,rho,ell=p['b'],p['B'],F('.048'),F('.001')
    linear_time=(ell-b)/(rho*ell)
    peak=I(ell)*I(90*rho).exp()
    assert peak.hi < I(B).lo
    def pulses(starts):
        ss=[];cursor=F(0);marks=[]
        for start in starts:
            start=F(start);end_linear=start+linear_time;end_ramp=end_linear+90;end=end_ramp+30
            ss.extend([segment(cursor,start,b),segment(start,end_linear,b,rho*ell),
                       segment(end_linear,end_ramp,ell,rho,True),segment(end_ramp,end,peak)])
            marks.extend([end_ramp-F(1),end_ramp+F(15),end+F(1)])
            cursor=end
        ss.append(segment(cursor,F(1600),b))
        return ss,marks
    first,marks=pulses([400])
    # Gap after the first decline exceeds original h+tau, independently of
    # whether a particular random sample actually generated a HOLD.
    second,marks2=pulses([400,800])
    initial=[segment(0,230,B),segment(230,1600,b)]
    return [('ramp_plateau_drop',first,marks),('repeat_after_hold',second,marks2),
            ('initial_peak',initial,[F(1),F(190),F(231)])]


def interval(z):return dict(lower=F(z.lo),upper=F(z.hi),width=F(z.hi)-F(z.lo))


def joint_probability(ss,c,stage,word,target):
    # Nominal clock (an admissible clock); conservative disclosure weights
    # and actual rounded timers remain those of the whole-clock proof.
    tick=F('1e-9');ka=c['ka'];ps=524288*c['g']*tick;pl=ka*ps
    phase=(8*c['g']*((ka*word)//8)+164*((ka*word)%8))*tick
    mandatory=phase+((target-phase)//pl)*pl
    u=mandatory+ps/2;v=mandatory+5*ps/2
    first,last=mandatory+ps-320*tick,mandatory+2*ps-320*tick
    startup=first<=c['h_upper']+c['tau']
    window=j.proof_window(c,stage);ph=j.phase_constants(c)
    r0=(1-ph['phi'])*ph['P']+ph['d'];r1=ph['P']+ph['d']
    oldest=first-window
    mass=I(0)
    if last-r1>oldest:mass=mass+I(ph['phi'])*integrate(ss,oldest,last-r1)
    l=max(oldest,last-r1);r=last-r0
    if r>l:mass=mass+integrate(ss,l,r,(last-r0)/ph['P'],-1/ph['P'])
    mass=I(max(0,mass.lo),max(0,mass.hi))
    old_mass=I(ph['phi'])*integrate(ss,first-window,first-c['tau']-2*j.accepted.JIT)
    factor=I(1)
    if stage==2:
        for a,b,k in j.proof_bands(c)[1:]:
            mu=I(ph['phi'])*integrate(ss,first-b,first-a)
            factor=factor*(I(0)-mu).exp()*(I(1)+mu)
    actual=(I(0)-mass).exp()*factor
    old=(I(0)-old_mass).exp()*factor
    if startup:actual=old=I(0)
    return dict(word=word,ka=ka,stage=stage,u=u,v=v,first_freeze=first,last_freeze=last,
                forced_startup=startup,zero_mass=interval(mass),
                joint_probability=interval(actual),first_freeze_probability=interval(old),
                refinement_confirmed=startup or actual.hi<old.lo)


def write_boundaries():
    """Causal semantics at freeze and observation-before-update; no new RTL."""
    checks=[]
    for kind in ('write16','write32'):
        for offset in (-1,0,1):
            r=Rule(8,3,20,60,4);r.cursor=10
            parent=99;freeze=100;available=freeze+offset
            tx=r.begin(3,kind)
            if available<=freeze:r.err(available,tx)
            decision=r.freeze(10,freeze)
            if available>freeze:r.err(available,tx)
            # New data become authoritative only AFTER the pre-update ERR.
            r.release(tx)
            assert decision==(offset<=0)
            assert r.decisions[10]==decision
            assert parent<=available and r.fast(101)
            # A subsequent accepted loss/recovery does not erase a skip,
            # clear a pending transaction, reset phase, or issue new epsilon.
            tx2=r.begin(4,kind);r.loss(102);r.recover(103)
            assert r.pending[0]==tx2 and r.cursor==11
            assert r.decisions[10]==decision and r.mission_budget_id=='one-lifetime-budget'
            assert r.fast(103+r.h+r.tau)
            checks.append(dict(kind=kind,availability_offset_ticks=offset,
                               decision=decision,immutable=True,same_budget=True))
    return checks


def run():
    p=j.accepted.old.environment(j.accepted.old.HANDOFF['rows'][0])
    pr=j.accepted.CFG['profiles'][2];gr=j.accepted.CFG['growth_classes'][0]
    cases=[]
    for name,ss,targets in profiles(p):
        fluence=integrate(ss,F(0),F(1600))-I(p['b']*1600)
        assert 0<=fluence.lo<=fluence.hi<I(p['FS']).lo
        rows=[]
        for ka in (3,33):
            c=j.accepted.calendar(p,pr,ka,gr)
            for stage in (2,1):
                for word in (0,p['W']//2,p['W']-1):
                    for target in targets:
                        row=joint_probability(ss,c,stage,word,target)
                        assert row['refinement_confirmed']
                        assert row['joint_probability']['width']<F('1e-35')
                        rows.append(row)
        cases.append(dict(name=name,horizon_s=1600,solar_fluence=interval(fluence),
                 admissible_growth='exact maximal H-slope .048 on rises, downward jumps only',rows=rows))
    return dict(cases=cases,write_freeze_boundaries=write_boundaries(),
                scope='explicit admissible histories only; not uniform risk or sampled ERR process')


if __name__=='__main__':
    import json
    out=run()
    print(json.dumps(j.accepted.old.serial(out),ensure_ascii=False,indent=2))
