"""Fixed schedules for the named finite SEPEM sample of 300 s step profiles."""
import argparse
import json
from fractions import Fraction as F

import fixed


def environment(source):
    # Width 10^-9 exceeds the rounding error in S1/S2 and B in the issued JSON.
    guard=F(1,10**9)
    maxima=source['maxima']
    s2=F(str(maxima['S2']['S2_s_inv']))
    return {'S1':F(str(maxima['S1']['S1']))+guard,'S2':s2+guard,
            'S2_lower':s2-guard,'B':F(str(source['whole_archive']['peak_s_inv']))+guard}


def tail(w,p0,env):
    # Use the actual max-S2 decade. Remove both 300 s boundary bins, including
    # startup. Split each remaining constant bin into three disjoint 100 s pieces.
    length=F(100)
    rate_factor=F(fixed.N,fixed.DREF)
    interior=max(F(0),env['S2_lower']-600*env['B']**2)
    m=length/p0+2
    free=max(F(0),length-m*fixed.DE)
    survival=1-rate_factor*env['B']*length
    assert survival>0
    z=w*F(fixed.N-1,2*fixed.N)*rate_factor**2*survival*interior*free**2/(length*(m+1))
    return max(F(0),z/(1+z)-fixed.DELTA)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    args=p.parse_args()
    source=fixed.read(fixed.HERE/'sepem.json')
    env=environment(source)
    data={'scope':'Finite SEPEM T141 set of complete 300 s step profiles; same service and mark caps',
          'max_S2_witness_start':source['maxima']['S2']['start_utc'],'environment':env,
          'rows':[fixed.row(res,eps,env,tail) for res in fixed.RESOURCE for eps in (F(1,1000),F(1,10000))]}
    text=fixed.table(data).replace('Условный вход T141, 3 г/см², D₁=0.',
        'Условная конечная выборка ступенчатых профилей SEPEM, 3 г/см², D₁=0.').replace(
        'См. [договор и вывод](README.md).','См. [область и расчёт](ARCHIVES.md).')
    outputs={'archive-fixed.json':json.dumps(data,default=str,indent=2,ensure_ascii=False)+'\n',
             'SEPEM-FIXED.md':text}
    for name,value in outputs.items():
        target=fixed.HERE/name
        if args.check:
            if target.read_text(encoding='utf-8')!=value:raise SystemExit('Mismatch: '+name)
        else:target.write_text(value,encoding='utf-8',newline='\n')
    print('PASS: eight fixed-schedule rows for the SEPEM sample')


if __name__=='__main__':main()
