"""Independent checks of the new substitutions and the historical v4 row."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path
import sys
import fixed


def main():
    data=fixed.create(); env=data['environment']; T=fixed.T
    old=fixed.read(fixed.EXP/'mission-rise-rate-20261022/outputs/pilot.json')['limits']['fixed_candidates']['39']
    cfg=fixed.read(fixed.EXP/'t186-method-comparison/code-strength/common-input.json')
    sys.path.insert(0,str(fixed.EXP/'t186-method-comparison/code-strength'))
    import comparison
    times=comparison.service(cfg,39)['upper']; apps=comparison.count_apps(cfg)
    common=(apps['read']*times['app_read']+apps['write']*times['app_write']+cfg['words']*times['initial'])/(T*fixed.NS)
    hist=100*(F(old['cost']['core_SRAM_fraction_upper'])-common)
    assert old['k']==11 and round(float(F(old['period']['upper_ns'])/fixed.NS),6)==0.282594
    assert round(float(hist),6)==3.178505
    # A plateau in the registered class. Count wholly free cells for three distinct phases.
    with localcontext() as ctx:
        ctx.prec=65
        dec=lambda x: Decimal(x.numerator)/Decimal(x.denominator)
        for r in data['rows']:
            w=r['W']; c=r['continuous']; P=c['period_s'][0]*fixed.XP
            L=env['tau']; a=(T-L)/2; b=a+L
            lower_count=int(L/P)-1
            for j in (0,7,w-1):
                phase=F(1568*(j//8)+164*(j%8),fixed.NS)*fixed.XP
                start=(a+P-fixed.DE-phase)/P; stop=(b-phase)/P
                exact_count=stop.numerator//stop.denominator-(-(-start.numerator//start.denominator))+1
                assert exact_count>=lower_count
            mu=dec(39*env['B']/fixed.DREF*(P-fixed.DE))
            hazard=Decimal(w*lower_count)*Decimal(38)/78*mu*mu*(-mu).exp()
            independent_L=1-(-hazard).exp()-dec(fixed.DELTA)
            assert dec(c['Q_lower'])<=independent_L<=dec(c['risk']['total'])
            assert r['peak']['all_slot_serial_upper_percent'] < r['peak']['serial_limit_percent']
            need=r['necessary']; assert need['Q_lower_on_tail']>r['epsilon']
            if r['status']=='whole_class_excluded_conditional':
                assert need['required_reads_lower']>need['maximum_reads_upper'] or need['serial_lower_s']>need['available_serial_upper_s']
            for name in ('bus','serial'):
                cost=c['price'][name]; assert cost['lower_s']<=cost['upper_s'] and cost['upper_percent']==100*cost['upper_s']/T
            if r['candidate']:
                assert r['candidate']['price']['bus']['upper_s']>=need['bus_lower_s']
    print('PASS: v4, independent plateau free-cell check, class witnesses, resource ceilings and eight price intervals')


if __name__=='__main__':main()
