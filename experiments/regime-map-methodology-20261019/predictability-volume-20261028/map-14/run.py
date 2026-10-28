"""Registered 14-cell map; reuse accepted c00 and evaluate only 13 new cells.

No accepted file is written. --stage first writes four priority cells; --stage
remaining extends that same result with nine cells. Default replays all 13 new
cells and only loads the accepted c00. Times are separate from scientific data.
"""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=BASE.parents[2]
sys.path.insert(0,str(BASE))
import first_point as accepted


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def encoded(value):
    return accepted.encoded(value)


def load():
    c=json.loads((HERE/'inputs.json').read_text('utf-8'))
    for path,sha in c['source_sha256_LF'].items():
        assert digest(ROOT/path)==sha,path
    cells=c['cells']
    keys={(x['words'],F(x['alpha']),F(x['epsilon'])) for x in cells}
    assert len(cells)==len(keys)==14
    assert sum(x['stage']=='accepted_reuse' for x in cells)==1
    assert len([x for x in cells if x['stage']=='first'])==4
    return c


class GridPoint(accepted.Point):
    def __init__(self,cell):
        registered=load()['cells']
        assert cell in registered and cell['stage']!='accepted_reuse'
        # Accepted constructor verifies source files and loads the service;
        # it does NOT run the accepted comparison point or resource preflight.
        super().__init__()
        self.W=cell['words']; self.alpha=F(cell['alpha']); self.eps=F(cell['epsilon'])
        assert self.W*4==cell['useful_bytes']
        self.a=(1-self.alpha)*self.a0
        self.R,self.Fr=self.B-self.b-self.a,self.alpha*self.Fs
        e=self.c['environment']
        self.g=F(e['rho'])*F(e['ell'])-self.a/F(e['template']['rise_s'])
        self.pmax=self.b+self.a
        self.IH=self.LH*(self.b**2+self.b*self.a+self.a**2/3)
        self.Ip=self.IH+self.IL
        self.box=self.LH*self.pmax**2
        self.K=F(self.W*39*38,2*self.D**2)
        self.Fparents=F(39*self.W,self.D)*(self.b*self.T+self.Fs)
        self.resource=next(accepted.numeric(row) for row in json.loads((BASE/'resource-result.json').read_text('utf-8'))['rows'] if row['words']==self.W)
        self.Nmax=self.resource['calendar']['necessary_class_maximum_reads_upper']

    def witnesses(self):
        # At alpha=0 there is no nonempty residual-plateau witness.
        return [w for w in super().witnesses() if w['length_s']>0]


def price_key(row,label):
    c=row['prices'][label]['coordinates']
    return c['serial']['protection_upper_s'],c['bus']['protection_upper_s'],row['pair']


def lower_for_account(fixed):
    if fixed['excluded_from'] is not None:
        return fixed['excluded_from']
    return dict(P0_s=None,reads_lower=F(0),cost={x:dict(lower_s=F(0),lower_fraction=F(0)) for x in ('bus','serial')},
                class_excluded_by_resource=False,basis='trivial nonnegative lower only; registered witnesses did not give a positive price bound')


def comparisons(price,lowerF,bestF,T):
    out={}
    for coord,c in price['coordinates'].items():
        U=c['all_known_upper_s']
        commonlo=c['app_s']['lower']+c['init_s']['lower']
        L=lowerF['cost'][coord]['lower_s']+commonlo
        x=dict(class_ratio_lower_known=L/U,class_extra_management_budget_per_s=(L-U)/T,
               protection_extra_budget_per_s=(lowerF['cost'][coord]['lower_s']-c['protection_upper_s'])/T)
        if bestF:
            f=bestF['coordinates'][coord]
            x.update(candidate_ratio_lower_known=f['all_known_lower_s']/U,
                     candidate_extra_management_budget_per_s=(f['all_known_lower_s']-U)/T,
                     ratio_of_sufficient_uppers=f['all_known_upper_s']/U,
                     difference_of_sufficient_uppers_per_s=(f['all_known_upper_s']-U)/T)
        out[coord]=x
    return out


def pack(cell,data,brackets,management,source):
    """One action record per identical execution; certificate prices stay distinct."""
    rows=data['candidates']['rows']; selected=data['candidates']['selected']
    lookup={tuple(r['pair']):r for r in rows}
    constants=[r for r in rows if r['pair'][0]==r['pair'][1] and r['risks']['F']['upper']<=F(cell['epsilon'])]
    best=min(constants,key=lambda r:price_key(r,'M')) if constants else None
    kF=data['candidates']['fixed_k']
    method_pairs=dict(F_max=[kF,kF] if kF else None,F_menu=best['pair'] if best else None,
                      N0=selected['N0'],Nplus_box=selected['Nplus_box'],M=selected['M'])
    methods={};executions={};prices={}
    lower=lower_for_account(data['fixed_class'])
    bestprice=best['prices']['M'] if best else None
    T=F(data['mission_s']);resource=data['resource_reused']
    for name,pair in method_pairs.items():
        if pair is None:
            methods[name]=dict(status='no_sufficient_menu_candidate',pair=None)
            continue
        row=lookup[tuple(pair)];constant=pair[0]==pair[1]
        label=name if name in ('N0','Nplus_box') else 'M'
        formula='F' if constant else ('N0_actual' if name=='N0' else ('Nplus_box' if name=='Nplus_box' else 'M'))
        risk=row['risks'][formula]
        qlo=brackets[tuple(pair)]['Q_lower']; qhi=risk['upper']
        status='certified' if qhi<=F(cell['epsilon']) else ('violates' if qlo>F(cell['epsilon']) else 'unresolved')
        price=row['prices'][label]
        guarded=not constant and name!='N0'
        eid=('fixed-'+str(pair[0])) if constant else ('window-'+str(pair[0])+'-'+str(pair[1])+('-H' if guarded else '-0'))
        boundid=eid+'-'+str(qhi)
        if eid not in executions:
            h=price['hold']
            executions[eid]=dict(pair=pair,constant=constant,guarded=guarded,hold=h,
                H_lower_margin_s=(h['lower_s']-row['period_high_s']['upper']-data['dE_s']) if guarded else None,
                hold_quantum_count=h['ticks']//20,
                hold_count_fits_prior_34_bits=h['ticks']//20<2**34,
                phase_counter_bits_required=(int(T/resource['calendar']['cycle_lower_ns']*10**9)+1).bit_length(),
                period_high_s=row['period_high_s'],period_low_s=row['period_low_s'],
                price_padding_s=price['C_s'],reads_lower=price['reads_lower'],reads_upper=price['reads_upper'],
                read_terms_upper=price['read_terms_upper'],fast_time_expected_upper_s=price['fast_time_expected_upper_s'],
                operations_performed_after_memory_failure=True,
                channel_disabled=constant,unknown_hardware_control=True)
        if boundid not in prices:
            prices[boundid]=dict(price=price,comparisons=comparisons(price,lower,bestprice,T),management=management[(tuple(pair),label)])
        methods[name]=dict(pair=pair,execution=eid,price=boundid,Q_lower=qlo,Q_upper=qhi,Q_status=status,
            Q_terms=risk['terms'],Q_basis=formula,
            V0=row['risks']['N0_design']['upper'] if name=='N0' else None)
    methods['Nplus_refined']=dict(alias='M',reason='identical actions, certificate and price')
    compact=[]
    for r in rows:
        compact.append(dict(pair=r['pair'],eligible=r['eligible'],
            risks={k:v for k,v in r['risks'].items()},
            known_price_upper={k:{x:v['coordinates'][x]['protection_upper_s'] for x in ('bus','serial')} for k,v in r['prices'].items()}))
    return dict(cell=cell,provenance=source,mission_s=T,environment=data['environment'],
        fixed_class=data['fixed_class'],fixed_class_lower_for_price=lower,
        fixed_largest_k=kF,methods=methods,executions=executions,price_bounds=prices,
        menu_generation=data['candidates']['generation'],candidate_summary=compact,
        registered_lower_witnesses={str(pair):b for pair,b in brackets.items()},
        resource=resource,comparison_scope='conditional known coordinates + unknown control; not global optima',
        common_app_init_separate=True,physical_Q=None,remaining_proof='no new theorem; retain certificate gaps and physical/implementation conditions')


def new_cell(cell):
    p=GridPoint(cell)
    # Sufficient feasibility first, including epsilon=1e-4, before lower searches.
    c=p.candidates()
    fixed=p.fixed_threshold()
    if fixed['excluded_from'] is None:
        fixed['registered_witness_limit_at_P_infinity']=[p.witness_bound(w,F(2)) for w in p.witnesses()]
        fixed['interpretation']='positive necessary price not established by registered bounds; OFF admissibility not established'
    else:
        fixed['positive_necessary_price_established']=True
    const=[r for r in c['rows'] if r['pair'][0]==r['pair'][1] and r['risks']['F']['upper']<=p.eps]
    best=min(const,key=lambda r:price_key(r,'M')) if const else None
    selected={tuple(x) for x in c['selected'].values() if x}
    if c['fixed_k']:
        selected.add((c['fixed_k'],c['fixed_k']))
    if best:
        selected.add(tuple(best['pair']))
    brackets={pair:p.n0_lower(*pair) for pair in selected}
    rowmap={tuple(x['pair']):x for x in c['rows']}
    lower=lower_for_account(fixed)
    mg={}
    for pair in selected:
        row=rowmap[pair]
        for label,price in row['prices'].items():
            mg[(pair,label)]=p.management(price,lower,best['prices']['M'] if best else price)
    data=dict(candidates=c,fixed_class=fixed,mission_s=p.T,dE_s=p.dE,
        environment=dict(b=p.b,B=p.B,a=p.a,R=p.R,Fr=p.Fr,g=p.g,Ip=p.Ip,IH=p.IH,IL=p.IL,box=p.box,K=p.K,XE=p.XE),
        resource_reused=p.resource)
    return pack(cell,data,brackets,mg,dict(kind='new_cell',model='accepted PR294 formulas and PR296 functions, parameters from map inputs'))


def reuse_accepted(cell):
    assert cell['stage']=='accepted_reuse'
    raw=accepted.numeric(json.loads((BASE/'first-point-result.json').read_text('utf-8')))
    # Do not construct a Point or invoke its Q/price/resource functions for c00.
    assert (cell['words'],F(cell['alpha']),F(cell['epsilon']))==(raw['words'],raw['alpha'],raw['epsilon'])
    raw=deepcopy(raw)
    raw['dE_s']=124*F('1.00001')/10**9+3*F('0.5')/10**9
    pairs={tuple(v) for v in raw['candidates']['selected'].values() if v}
    assert pairs=={(3,3)} and raw['candidates']['fixed_k']==3
    brackets={tuple(x['pair']):x for x in raw['N0_Q_brackets'] if tuple(x['pair']) in pairs}
    mg={(pair,label):raw['management'][label] for pair in pairs for label in ('N0','Nplus_box','M')}
    return pack(cell,raw,brackets,mg,dict(kind='accepted_reuse_no_rerun',PR=296,
        sha256=digest(BASE/'first-point-result.json'),path='../first-point-result.json'))


def result_header(c):
    return dict(status='CONDITIONAL_MAP_NOT_SELF_ACCEPTED',base_main=c['base_main'],
        input_sha256=digest(HERE/'inputs.json'),implementation_sha256=digest(Path(__file__)),
        accepted_library_sha256=digest(BASE/'first_point.py'),sources=c['source_sha256_LF'],
        accepted_cell_recomputed=False,new_guard_campaign=False,mission_s=315576000,
        new_theory=False,profile_changed=False)


def run(stage,write):
    c=load();header=result_header(c);dest=HERE/'result.json'
    if stage=='remaining':
        previous=accepted.numeric(json.loads(dest.read_text('utf-8')))
        for k,v in header.items():
            assert previous[k]==v,('resume input/code mismatch',k)
        records=previous['cells']
        assert set(records)=={'c00','c01','c02','c03','c04'}
        times=json.loads((HERE/'timing.json').read_text('utf-8'))
    else:
        records={};times=dict(python=sys.version.split()[0],host='local Windows; one process',cells_s={},scope='wall time only, not WCET or uncertainty')
    total_start=time.perf_counter()
    for cell in c['cells']:
        if cell['id'] in records:
            continue
        if stage=='first' and cell['stage'] not in ('accepted_reuse','first'):
            continue
        start=time.perf_counter()
        record=reuse_accepted(cell) if cell['stage']=='accepted_reuse' else new_cell(cell)
        dt=time.perf_counter()-start
        records[cell['id']]=record
        times['cells_s'][cell['id']]=dt
        if write:
            methods=record['methods'];m=methods['M']
            price=record['price_bounds'][m['price']]['price'] if m.get('pair') else None
            print(json.dumps(dict(cell=cell['id'],alpha=cell['alpha'],epsilon=cell['epsilon'],
                Fmax=record['fixed_largest_k'],M=m.get('pair'),N0=methods['N0'].get('Q_status'),
                serial_upper=float(price['coordinates']['serial']['protection_upper_fraction']) if price else None,
                elapsed_s=dt,accepted_reuse=cell['stage']=='accepted_reuse')),flush=True)
    out=dict(header,cells=records,complete=len(records)==14,total_cells=len(records))
    raw=encoded(out)
    if write:
        dest.write_bytes(raw)
        times['stage_'+stage+'_s']=time.perf_counter()-total_start
        times['input_sha256']=header['input_sha256'];times['implementation_sha256']=header['implementation_sha256']
        times['result_sha256']=hashlib.sha256(raw).hexdigest()
        (HERE/'timing.json').write_bytes(encoded(times))
    else:
        assert dest.read_bytes().replace(b'\r\n',b'\n')==raw,'Map result differs'
        print(json.dumps(dict(replay_cells=13,accepted_reused=1,total_cells=len(records),elapsed_s=time.perf_counter()-total_start,result_sha256=hashlib.sha256(raw).hexdigest())))
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('first','remaining','all'),default='all')
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    if not args.write and args.stage!='all':
        parser.error('Default replay is the whole new map; accepted cell is loaded only')
    run(args.stage,args.write)
