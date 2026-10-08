"""Independent addressed arithmetic checker. Does not import production helpers.

Common dependencies: source data, stated formulas, Python Fraction/Decimal.
Not an independent Scientific Review or physical-input qualification.
"""
import json
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def plateau_reference(T,B,b,FS,Fcap=None,Scap=None,Ecap=None,start=True):
    if not start:return None
    # Each affine resource is (intercept, slope, cap). Solve each directly.
    uses=[(F(0),B-b,FS),(b*T,B-b,Fcap),(b*b*T,B*B-b*b,Scap),
          (F(0),B*B-b*b,Ecap)]
    duration=T
    for intercept,slope,cap in uses:
        if cap is None:continue
        if cap<intercept:return None
        if slope>0:duration=min(duration,(cap-intercept)/slope)
    return duration if duration>0 else None


def lower_reference(W,n,B,L,c,P0,P1,de):
    if not 0<c<P0<=P1<L/2 or not 0<B*P1/W<1:return None
    z=F(n-1,2*n*W)*B*B*(L-2*P1)*(P0-c)**2/P0*(1-B*P1/W)
    j=L//P1+2; cell=(L-j*c)/(4*j); x=B*cell/W
    if not 0<x<1:return None
    zt=F(n-1,n)*W*j*x*x*(1-x)
    return max(F(0),1-1/(1+z)-de),max(F(0),1-1/(1+zt)-de)


def check_witness(w,T,B,b,FS,Scap=None):
    L=F(w['L']); expected=plateau_reference(T,B,b,FS,Scap=Scap)
    assert L==expected
    assert F(w['solar_exposure'])==(B-b)*L<=FS
    assert F(w['F'])==B*L+b*(T-L)
    assert F(w['S2'])==B*B*L+b*b*(T-L)
    assert F(w['S2_excess'])==((B-b)**2+2*b*(B-b))*L


def check_row(r):
    W,n,T,B,b,FS=r['W'],r['n'],F(r['T']),F(r['B']),F(r['b']),F(r['FS'])
    eps,budget=F(r['epsilon']),F(r['quiet_budget'])
    check_witness(r['witness'],T,B,b,FS)
    S2=min(B*B*T,B*min(B*T,b*T+FS),b*b*T+(B+b)*FS)
    assert F(r['environment_square_upper'])==S2
    c=F(n,r['R_eff_bit_s']); k=F(n-1,2*n*W); tick=F(r['tick'])
    if r['selected_tick'] is not None:
        P=r['selected_tick']*tick
        assert F(r['Q_upper'])==k*P*S2<=eps
        assert k*(P+tick)*S2>eps  # certified maximum, not actual optimum
        cost=W*c/P+2*c/T
        assert F(r['constant_quiet_upper'])==cost
        assert F(r['full_bus_quiet_upper'])==cost+F('.5')+F('1e-7')/T
        cfg=json.loads((ROOT/'experiments/t58-fixed-baseline-r0b/config.json').read_text())
        rc=cfg['reference_point_rule']['table_resources'];app=cfg['app_diagnostic']
        h,delay=F(rc['h_s']),F(rc['delay_s'])
        assert F(r['all_bus_peak_upper'])==F(r['resource']['peak_upper'])+(F(app['sigma_s'])+F(app['u'])*(h+delay))/h
        if r['status']=='constant_sufficient':assert cost<=budget
    floor=r['necessary_price']
    if floor['value'] is not None:
        P0,P1=F(floor['P0']),F(floor['split']); L=F(r['witness']['L'])
        q,tail=lower_reference(W,n,B,L,c,P0,P1,F(0))
        assert q==F(floor['Q_lower'])>eps and tail==F(floor['tail'])>eps
        prev=lower_reference(W,n,B,L,c,F(floor['predecessor']),P1,F(0))
        assert prev[0]<=eps
        assert F(floor['value'])==max(F(0),W*c/P0-2*W*c/T)
    # Independently bound the unrelaxed cell probability; Decimal is diagnostic
    # here, not the enclosure authority used by the fixed-period decisions.
    low=r['class_lower_at_budget']; L=F(r['witness']['L'])
    assert r['constant_excluded_T58']==(F(low['lower'])>eps)
    assert r['constant_excluded_candidate_T126']==(floor['value'] is not None and F(floor['value'])>budget)
    assert r['constant_excluded']==(r['constant_excluded_T58'] or r['constant_excluded_candidate_T126'])
    tmin=W*c/(budget+2*c/T); j=L//tmin+2
    cell=(L-j*c)/(4*j)
    assert F(low['tau_min'])==tmin and low['J']==j and F(low['ell'])==cell
    if cell>0:
        dec=lambda x:D(x.numerator)/D(x.denominator)
        with localcontext() as ctx:
            ctx.prec=100
            x=B*cell/W
            cells=-(-(W*L/cell-W*j*(c/cell+2)).numerator//(W*L/cell-W*j*(c/cell+2)).denominator)
            assert cells==low['N']
            p=D(n-1)/D(2*n)*dec(x)**2*(-dec(x)).exp()
            q=1-(-D(cells)*p).exp()
            assert dec(F(low['lower']))<=q+D('1e-90')
            assert q-dec(F(low['lower']))<D('1e-48')


def check_controls(rows):
    cfg=json.loads((ROOT/'experiments/t114-two-stage-err/config.json').read_text())
    accepted=json.loads((ROOT/'experiments/t114-two-stage-err/report.json').read_text())
    for r in rows:
        if r['family']!='T114_control' or r['constant_quiet_export'] is None:continue
        co=accepted['constant_E'][r['shield_g_cm2']]
        T,W,B,b,FS=map(F,(r['T'],r['W'],r['B'],r['b'],r['FS']))
        tq=F(cfg['price_contract']['quiet_fraction'])*T;kq=cfg['price_contract']['quiet_components']
        read=F('92.500920e-9');write=F('56.000560e-9');E=read+write
        pm,pp=F(co['period_min']),F(co['period_max']);q=F(co['risk_upper'])
        # Direct expansion of published rate/edge formulas, no constant() call.
        original=W*read/pm+write*(b+(1+kq*B*(pp+E))/tq+W*q/pm)+4*8*E*kq/tq
        ap=write*(b+kq*B*(pp+E)/tq)/W
        X=F('1e-4')+kq*(F('209e-9')+F('1e-4')*F('3e-6'))/tq
        ex=r['constant_quiet_export'];rho=F(r['application']['rate_upper'])
        offered=rho+kq*(1+rho*F('3e-6'))/tq
        obs=read if r['application']['observed_writes'] else F(0)
        assert F(ex['old_returning_cost'])==original
        assert F(ex['aperture_addend'])==ap and F(ex['X_addend'])==X
        assert F(ex['quiet_upper'])==original+ap+X+obs*offered
        assert F(ex['total_bus_quiet_upper'])==original+ap+X+F('217.002160e-9' if obs else '185.001840e-9')*offered
        assert F(r['constant_quiet_upper'])==F(ex['quiet_upper'])
        if r['proposed_admission']:
            assert F(r['quiet_gain_lower'])==F(r['constant_quiet_lower'])/F(r['adaptive_quiet_upper'])
    return True


def check_all(report):
    r0=[r for r in report['rows'] if r['family']=='R0B_grid']
    assert len(r0)==36 and len({r['id'] for r in r0})==36
    for r in r0:check_row(r)
    cy=[r for r in report['rows'] if r['family']=='CY_new_input']
    assert len(cy)==36 and len({r['example_group'] for r in cy})==1
    for r in cy:
        assert r['Dstar'] is None and r['Q_upper'] is None and r['status']=='unknown'
        b,FS=F(r['b']),F(r['FS'])
        assert abs(F(r['S2_mixed'])-2*b*FS)<F('1e-8')
        assert F(r['S2_solar_excess'])==F(r['S2_solar_squared'])+F(r['S2_mixed'])
        assert F(r['sigma_singleton_reference'])==F(r['n']-1,2*r['n']*r['W'])*F(r['P_min'])*F(r['S2_solar_excess'])/F(r['epsilon'])
    check_controls(report['rows'])
    for r in report['rows']:
        assert r['status']!='period_class_excluded'
        if r['status']=='adaptation_needed_and_sufficient':
            assert F(r['constant_quiet_lower'])>F(r['quiet_budget'])>=F(r['adaptive_quiet_upper'])
            assert F(r.get('Q_upper',r.get('risk_upper')))<=F(r['epsilon'])
    for case in report['necessary_checks']:
        pin=json.loads((ROOT/'experiments/t90-monitor-physical/outputs/pinned_inputs.json').read_text())
        p=next(x for x in pin if x['shield']=='3')['effective_T88_input'];e=p['environment'];s=p['service']
        T,B,b,FS=map(F,(e['T'],e['B'],e['b'],e['FS']));c=s['c_ticks']*F(s['tick_upper_s'])
        check_witness(case['witness'],T,B,b,FS,F(case['S2_fraction'])*(b*b*T+(B+b)*FS))
        q,tail=lower_reference(e['W'],e['n'],B,F(case['witness']['L']),c,F(case['P0']),F(case['P_split']),F(p['quotas']['delta_exec']))
        assert q==F(case['Q_lower_at_P0']) and tail==F(case['tail_Q_lower'])
        price=e['W']*s['c_ticks']*F(s['tick_lower_s'])/F(case['P0'])-2*e['W']*c/T
        assert price==F(case['constant_price_lower'])
    return {'r0b_rows':len(r0),'cy_rows':len(cy),'cap_witnesses':3,'constant_E_export_checked':True,
            'independence':'no production imports; common input bytes, formulas, Fraction/Decimal only',
            'not_scientific_review':True}


if __name__=='__main__':
    report=json.loads((HERE/'outputs/map.json').read_text(encoding='utf-8'))
    print(json.dumps(check_all(report),ensure_ascii=False))
