"""Independent scalar quadrature/arithmetic. No production calculate imports.

Shared evidence: the same tabulated ranges, response points and GOST cells.
Different implementation: Python scalar piecewise powers, scipy QUADPACK per
interval, Decimal resource arithmetic. This checks computation, not physics.
"""
import argparse
import bisect
import csv
from decimal import Decimal as D
import json
import math
from pathlib import Path
from scipy.integrate import quad

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/tNN-sepem-profiles'


def rows(path):
    with path.open(encoding='utf-8') as f:
        return list(csv.DictReader(f))


def power_interpolate(x, xs, ys):
    if x<xs[0] or x>xs[-1]:
        raise ValueError('Outside source support')
    j=min(len(xs)-2,max(0,bisect.bisect_right(xs,x)-1))
    return ys[j]*(x/xs[j])**(math.log(ys[j+1]/ys[j])/math.log(xs[j+1]/xs[j]))


def independent_gost_fold(rho, product):
    rt=rows(OLD/'inputs/nist_pstar_al.csv')
    es=[float(r['energy_mev']) for r in rt]; rs=[float(r['csda_range_g_cm2']) for r in rt]
    points=sorted((float(r['energy_mev']),float(r['sigma_bit_cm2_per_bit'])) for r in rows(ROOT/'experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv') if r['sigma_bit_cm2_per_bit'])
    se,ss=map(list,zip(*points))
    slope=(ss[1]-ss[0])/(se[1]-se[0]); zero=se[0]-ss[0]/slope
    def sigma(e):
        if e<se[0]: return max(0.,ss[0]+slope*(e-se[0]))
        if e>se[-1]: return ss[-1]
        return power_interpolate(e,se,ss)
    def inv(r):
        if r<=rs[0]: return 0.
        return power_interpolate(r,rs,es)
    coef={}
    source=rows(OLD/'inputs/gost_selected_coefficients.csv')
    for key in ('log10_c','break_energy_mev','gamma1','gamma2'):
        cells={int(r['n']):float(r['value']) for r in source if r['product']==product and r['parameter']==key}
        coef[key]=cells[64]+math.log(92.5548/64,2)*(cells[128]-cells[64])
    ek=coef['break_energy_mev']; amp=10**coef['log10_c']
    def flux(e):
        if e<ek: return amp*(e/ek)**(-coef['gamma1'])
        return amp*(e*(e+1876)/(ek*(ek+1876)))**(-coef['gamma2'])
    def integrand(e):
        residual=inv(power_interpolate(e,es,rs)-rho)
        return sigma(residual)*flux(e)
    cuts={5.,10000.,ek}
    cuts.update(e for e in es if 5<e<10000)
    for residual in [zero]+se+es:
        if residual>0 and residual<=es[-1]:
            r=rho+power_interpolate(residual,es,rs)
            if r<=rs[-1]:
                e=inv(r)
                if 5<e<10000: cuts.add(e)
    cut=sorted(cuts)
    result=math.fsum(quad(integrand,a,b,epsabs=1e-14,epsrel=1e-10,limit=100)[0] for a,b in zip(cut,cut[1:]))
    return result*19922944*(4*math.pi if product=='peak_flux' else 1)


def validate_unknown_upper(q, dstar):
    if dstar is None and q is not None:
        raise ValueError('Unknown Dstar cannot yield a full Q upper')


def check(out):
    resource=json.loads((out/'service.json').read_text())
    g=D(resource['g_ticks']); slow=D('1.00001e-9'); fast=D('0.99999e-9')
    p=D(524288)*g*slow
    assert abs(float(p)-resource['P_min_s'])<1e-15
    # Direct busy-time accounting, no production calendar/resource helpers.
    E=D('148.501480e-9'); app=D('217.002160e-9'); window=D('.001')
    ctrl=8*E*(window/(8*g*fast)+2)/window+D('.0001')+(D('209e-9')+D('.0001')*D('3e-6'))/window
    rate=(D('.8')-ctrl-app/window)/(app*D('1.003'))
    assert abs(float(rate)-resource['application_plus_X_rate_max_s'])<1e-7
    assert resource['joint_delay_upper_s']<=3e-6
    assert resource['g_ticks']==196 and not resource['candidates'][-2]['passes_declared_calendar_resource_test']
    calc=rows(out/'shield-conditional.csv')
    for row in calc:
        b,s=map(float,(row['b_s'],row['solar_peak_s']))
        square=315576000*b*b+115776*s*s+2*115776*b*s
        assert math.isclose(square,float(row['S2_total']),rel_tol=1e-13)
        # Independent Decimal evaluation of both accepted aperture alternatives.
        bd,sd,sq=map(D,(row['b_s'],row['solar_peak_s'],row['S2_total']))
        W=D(524288); T=D(315576000); B=bd+sd; fs=sd*D(115776)
        beta=D(1)/(2*W); eta=2*beta/W; plen=W*g*fast
        x1=beta*(E+p/W)*sq
        v=2*beta*E*(T/plen+1)
        x2=min(B*p,bd*T+fs)*min(B*v,bd*v+eta*fs,eta*(bd*T+fs))
        rest=D('.000003')+B*(p+E)/W+beta*p*sq+min(x1,x2)
        assert math.isclose(float(rest),float(row['Q_without_D_arithmetic']),rel_tol=1e-12)
        validate_unknown_upper(None if not row['physical_Q_upper'] else float(row['physical_Q_upper']), None)
        assert row['example_group']=='CY62167_full38_shield_curve'
    checks=[]
    for row in rows(out/'gost-proton-conditional.csv'):
        if row['response']!='pdi':continue
        rho=float(row['shield_g_cm2'])
        for product,field in [('fluence','N_solar_protons'),('peak_flux','peak_solar_protons_s')]:
            scalar=independent_gost_fold(rho,product); production=float(row[field])
            error=abs(scalar/production-1)
            assert error<.001,(rho,product,error)
            checks.append(dict(shield_g_cm2=rho,product=product,scalar=scalar,production=production,relative_difference=error))
    # Independent historical regression, not just agreement of reused functions.
    old=json.loads((OLD/'outputs/baseline_audit.json').read_text())
    row=next(r for r in calc if r['shield_g_cm2']=='3.0' and r['response']=='historical_HEP')
    for field,key in [('b_s','historical_nu_G_per_s'),('solar_peak_s','historical_nu_S_per_s'),('S2_total','historical_S2_sum_per_s')]:
        assert math.isclose(float(row[field]),float(old[key]),rel_tol=1e-11),(field,row[field],old[key])
    return dict(status='PASS_COMPUTATIONAL_CHECKS_ONLY', independent_quadrature=checks,
                not_checked=['physical response uncertainty','isotropic response qualification','full38 Dstar','GOST/RDS event population identity'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=HERE/'outputs');a=p.parse_args()
    result=check(a.out)
    (a.out/'independent-check.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))
