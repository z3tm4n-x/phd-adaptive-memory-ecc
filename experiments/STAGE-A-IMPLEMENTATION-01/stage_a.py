#!/usr/bin/env python3
"""Bounded Stage-A certificate/policy computation (exact rational decisions)."""
import argparse,base64,csv,gzip,hashlib,json,math
from fractions import Fraction as R
from pathlib import Path
PTH=('LL','LH','HL','HH'); LV={'LL':('L','L'),'LH':('L','H'),'HL':('H','L'),'HH':('H','H')}; CMP=('Fixed','Precomputed','Causal')
def F(x): return x if isinstance(x,R) else R(str(x))
def fs(x): return f'{float(x):.15g}'
def sc(x): return f'{float(x):.12e}'
def load(c):
 m={'N':int(c['memory']['N_bits']),'nw':int(c['memory']['N_words']),'n':int(c['memory']['data_bits_per_word']),'P':F(c['restoration']['full_pass_duration_s']),'B':F(c['scenario']['block_duration_s']),'T':F(c['scenario']['horizon_s']),'U':tuple(map(F,c['restoration']['U_s'])),'E':tuple(map(F,c['certificate']['epsilon_grid'])),'R':tuple(map(F,c['model']['rho_grid'])),'rate':{d:{'L':F(v['L_s-1']),'H':F(v['H_s-1'])} for d,v in c['frozen_levels'].items()}}
 assert m['N']==m['nw']*m['n']==2**24 and all(t>=m['P'] and m['B']/t==int(m['B']/t) for t in m['U']); return m
def rates(m,d,p): a,b=LV[p]; return m['rate'][d][a],m['rate'][d][b]
def ld(m,b1,b2,r): return r*m['B']*(b1+b2)/2
def pair(m,b1,b2,r,t1,t2):
 r1=(1-r)*b1/m['N']; r2=(1-r)*b2/m['N']; nw=m['nw']; P=m['P']; A1=P*R(nw-1,2); A2=P*P*R((nw-1)*(2*nw-1),6*nw); q1=int(m['B']/t1); q2=int(m['B']/t2)
 S=r1*r1*(nw*t1*t1-2*t1*A1+A2)+(q1-1)*nw*(r1*t1)**2+nw*(r2*t2)**2+2*r2*t2*(r1-r2)*A1+(r1-r2)**2*A2+(q2-1)*nw*(r2*t2)**2+r2*r2*A2
 return m['n']*(m['n']-1)//2*S
def cert(m,b1,b2,r,t1,t2):
 D=ld(m,b1,b2,r); A=pair(m,b1,b2,r,t1,t2); raw=D+A; return min(R(1),raw),raw,D,A
def pc(m,a,b): return int(m['B']/a)+int(m['B']/b)
def res(m,a,b):
 p=pc(m,a,b); o=m['P']*p; return p,p*2**21,p*2**21,o,o/m['T']
def ok(m,d,r,e,p,a,b): return cert(m,*rates(m,d,p),r,a,b)[0]<=e
def key(m,pol):
 pv=tuple(pc(m,*pol[p]) for p in PTH); rr=tuple(x for p in PTH for x in pol[p]); return max(pv),pv,tuple(-x for x in rr)
def best(m,its):
 z=list(its); return min(z,key=lambda x:key(m,x)) if z else None
def fixed(m,d,r,e):
 for t in m['U']:
  if all(ok(m,d,r,e,p,t,t) for p in PTH): yield {p:(t,t) for p in PTH}
def pre(m,d,r,e):
 for a in m['U']:
  for b in m['U']:
   if all(ok(m,d,r,e,p,a,b) for p in PTH): yield {p:(a,b) for p in PTH}
def roots(m,d,r,e):
 for aL in m['U']:
  for aH in m['U']:
   A={}
   for p in PTH:
    a=aL if p[0]=='L' else aH; q=[b for b in m['U'] if ok(m,d,r,e,p,a,b)]
    if not q: break
    A[p]=q
   if len(A)==4: yield aL,aH,A
def causal(m,rr):
 for aL,aH,A in rr: yield {p:((aL if p[0]=='L' else aH),max(A[p])) for p in PTH}
def dst(m,d,r,e):
 v=[ld(m,*rates(m,d,p),r) for p in PTH]
 return 'DIRECT-CERTIFICATE-BUDGET-EXHAUSTED' if any(x>e for x in v) else ('DIRECT-EQUALITY-PRESENT' if any(x==e for x in v) else 'DIRECT-BUDGET-REMAINS')
def wcsv(p,f,rows):
 with p.open('w',newline='',encoding='utf-8') as h:
  w=csv.DictWriter(h,fieldnames=f,extrasaction='ignore',lineterminator='\n'); w.writeheader(); w.writerows(rows)
def frozen(path,c):
 h=hashlib.sha256(path.read_bytes()).hexdigest(); exp=c['upstream']['proton_rate_5min_sha256']
 if h!=exp: raise RuntimeError(f'frozen CSV SHA-256 mismatch: {h} != {exp}')
 cols=c['upstream']['columns']; v={d:[] for d in cols}
 with path.open(newline='',encoding='utf-8') as fh:
  for row in csv.DictReader(fh):
   if row['east_valid']!='1' or row['west_valid']!='1': continue
   try: xs={d:F(row[col]) for d,col in cols.items()}
   except: continue
   if any(x<0 for x in xs.values()): continue
   for d,x in xs.items(): v[d].append((x,row['timestamp_utc']))
 if len(next(iter(v.values())))!=int(c['upstream']['paired_valid_intervals']): raise RuntimeError('paired-valid row count mismatch')
 for d,a in v.items():
  s=sorted(a); n=len(s); med=s[n//2][0] if n%2 else (s[n//2-1][0]+s[n//2][0])/2; mx=max(a)[0]
  if med!=F(c['frozen_levels'][d]['L_s-1']) or mx!=F(c['frozen_levels'][d]['H_s-1']): raise RuntimeError(f'L/H mismatch {d}')
def audit(m):
 out=[]
 for d in sorted(m['rate'],key=lambda x:int(x[1:])):
  for r in m['R']:
   for p in PTH:
    b1,b2=rates(m,d,p); D=ld(m,b1,b2,r); z={'shield_mm':d[1:],'rho':fs(r),'path':p,'b1_s-1':fs(b1),'b2_s-1':fs(b2),'Lambda_D':sc(D)}
    for e in m['E']: z['eps_'+fs(e)]='DIRECT-CERTIFICATE-BUDGET-EXHAUSTED' if D>e else ('DIRECT-EQUALS-EPS-ZERO-RESIDUAL-BUDGET' if D==e else 'DIRECT-BUDGET-REMAINS')
    out.append(z)
 return out
def mask(m,a):
 s=set(a); return f"0x{sum(1<<i for i,t in enumerate(m['U']) if t in s):03x}"
def search(m):
 sel=[]; pas=[]; det={'U_s':[fs(t) for t in m['U']],'cases':{}}; trees={}
 for d in sorted(m['rate'],key=lambda x:int(x[1:])):
  for r in m['R']:
   for e in m['E']:
    cid=f'{d}_rho={fs(r)}_eps={fs(e)}'; s=dst(m,d,r,e)
    if s.startswith('DIRECT-CERTIFICATE'):
     pas.append({'shield_mm':d[1:],'rho_case':fs(r),'epsilon':fs(e),'status':s,'fixed_count':0,'precomputed_count':0,'causal_root_count':0,'causal_tree_count':0}); det['cases'][cid]={'status':s}; continue
    fx=list(fixed(m,d,r,e)); pr=list(pre(m,d,r,e)); rr=list(roots(m,d,r,e)); cb=list(causal(m,rr)); tc=sum(math.prod(len(A[p]) for p in PTH) for _,_,A in rr)
    pas.append({'shield_mm':d[1:],'rho_case':fs(r),'epsilon':fs(e),'status':'SEARCHED','fixed_count':len(fx),'precomputed_count':len(pr),'causal_root_count':len(rr),'causal_tree_count':tc})
    det['cases'][cid]={'status':'SEARCHED','fixed_tau_s':[fs(x['LL'][0]) for x in fx],'precomputed_pairs_s':[[fs(x['LL'][0]),fs(x['LL'][1])] for x in pr],'causal_roots':[[fs(a),fs(b),mask(m,A['LL']),mask(m,A['LH']),mask(m,A['HL']),mask(m,A['HH']),math.prod(len(A[p]) for p in PTH)] for a,b,A in rr]}
    for nm,bp in [('Fixed',best(m,fx)),('Precomputed',best(m,pr)),('Causal',best(m,cb))]:
     if bp is None: continue
     trees.setdefault(cid,{})[nm]={}
     for p in PTH:
      a,b=bp[p]; q,raw,D,A=cert(m,*rates(m,d,p),r,a,b); ps,rd,wr,oc,of=res(m,a,b); trees[cid][nm][p]={'tau1_s':fs(a),'tau2_s':fs(b),'passes':ps}
      sel.append({'shield_mm':d[1:],'rho_case':fs(r),'epsilon':fs(e),'comparator':nm,'path':p,'status':'CERTIFIED','tau1_s':fs(a),'tau2_s':fs(b),'Q':sc(q),'Q_raw':sc(raw),'Lambda_D':sc(D),'pair_bound':sc(A),'certificate_margin':sc(e-q),'numerical_status':'RESOLVED-EXACT-RATIONAL','passes':ps,'reads':rd,'writes':wr,'occupied_s':fs(oc),'occupied_fraction':sc(of)})
 for d in sorted(m['rate'],key=lambda x:int(x[1:])):
  for e in m['E']:
   cid=f'{d}_rho=M_rho_eps={fs(e)}'; ex=any(dst(m,d,r,e).startswith('DIRECT-CERTIFICATE') for r in m['R']); st='DIRECT-CERTIFICATE-BUDGET-EXHAUSTED' if ex else 'NOT-EXECUTED'; det['cases'][cid]={'status':st}; pas.append({'shield_mm':d[1:],'rho_case':'M_rho','epsilon':fs(e),'status':st,'fixed_count':0,'precomputed_count':0,'causal_root_count':0,'causal_tree_count':0})
 return sel,pas,det,trees
def gaps(m,s):
 L={(x['shield_mm'],x['rho_case'],x['epsilon'],x['comparator'],x['path']):x for x in s}; out=[]; cases=sorted({(x['shield_mm'],x['rho_case'],x['epsilon']) for x in s})
 for d,r,e in cases:
  for a,label in [('Fixed','fixed_to_causal'),('Precomputed','precomputed_to_causal')]:
   if not all((d,r,e,c,p) in L for c in (a,'Causal') for p in PTH): continue
   av=[int(L[d,r,e,a,p]['passes']) for p in PTH]; cv=[int(L[d,r,e,'Causal',p]['passes']) for p in PTH]
   for p,x,y in zip(PTH,av,cv):
    q=x-y; out.append({'shield_mm':d,'rho':r,'epsilon':e,'gap':label,'path':p,'baseline_passes':x,'causal_passes':y,'pass_saving':q,'read_saving':q*2**21,'write_saving':q*2**21,'occupied_s_saving':fs(m['P']*q)})
   q=max(av)-max(cv); out.append({'shield_mm':d,'rho':r,'epsilon':e,'gap':label,'path':'WORST_CASE','baseline_passes':max(av),'causal_passes':max(cv),'pass_saving':q,'read_saving':q*2**21,'write_saving':q*2**21,'occupied_s_saving':fs(m['P']*q)})
 return out
def boundary(m):
 out=[]
 for d in sorted(m['rate'],key=lambda x:int(x[1:])):
  for r in m['R']:
   for e in m['E']:
    ds=dst(m,d,r,e); cand=[]
    if ds.startswith('DIRECT-CERTIFICATE'):
     for p in PTH:
      v=ld(m,*rates(m,d,p),r); cand.append((abs(v-e),p,'direct','','',v,v-e,'FAIL' if v>e else ('EQUAL' if v==e else 'PASS')))
    else:
     for p in PTH:
      b1,b2=rates(m,d,p)
      for a in m['U']:
       for b in m['U']:
        v=cert(m,b1,b2,r,a,b)[0]; cand.append((abs(v-e),p,'certificate',fs(a),fs(b),v,v-e,'PASS' if v<=e else 'FAIL'))
    g,p,typ,a,b,v,sg,cl=min(cand,key=lambda x:(x[0],x[1],x[3],x[4])); out.append({'shield_mm':d[1:],'rho':fs(r),'epsilon':fs(e),'family_status':ds,'boundary_type':typ,'path':p,'tau1_s':a,'tau2_s':b,'value':sc(v),'signed_value_minus_epsilon':sc(sg),'absolute_gap':sc(g),'classification':cl,'numerical_status':'RESOLVED-EXACT-RATIONAL'})
 return out

def main():
 a=argparse.ArgumentParser(); a.add_argument('--config',required=True); a.add_argument('--output-dir',required=True); a.add_argument('--frozen-csv'); x=a.parse_args(); c=json.loads(Path(x.config).read_text()); m=load(c); o=Path(x.output_dir); o.mkdir(parents=True,exist_ok=True)
 if x.frozen_csv: frozen(Path(x.frozen_csv),c)
 da=audit(m); wcsv(o/'direct_budget_audit.csv',['shield_mm','rho','path','b1_s-1','b2_s-1','Lambda_D',*[f'eps_{fs(e)}' for e in m['E']]],da)
 rr=[]
 for t1 in m['U']:
  for t2 in m['U']:
   p,rd,wr,oc,of=res(m,t1,t2); rr.append({'tau1_s':fs(t1),'tau2_s':fs(t2),'passes':p,'reads':rd,'writes':wr,'occupied_s':fs(oc),'occupied_fraction':sc(of)})
 wcsv(o/'resource_table.csv',['tau1_s','tau2_s','passes','reads','writes','occupied_s','occupied_fraction'],rr)
 s,p,d,t=search(m); sp=o/'selected_policies.csv'; wcsv(sp,['shield_mm','rho_case','epsilon','comparator','path','status','tau1_s','tau2_s','Q','Q_raw','Lambda_D','pair_bound','certificate_margin','numerical_status','passes','reads','writes','occupied_s','occupied_fraction'],s); (o/'selected_policies.csv.gz.b64').write_text(base64.b64encode(gzip.compress(sp.read_bytes(),mtime=0)).decode()+'\n'); sp.unlink(); wcsv(o/'passing_sets.csv',['shield_mm','rho_case','epsilon','status','fixed_count','precomputed_count','causal_root_count','causal_tree_count'],p); C={}; empty=[]
 for k,v in d['cases'].items():
  if v.get('status')!='SEARCHED': continue
  if not(v['fixed_tau_s'] or v['precomputed_pairs_s'] or v['causal_roots']): empty.append(k); continue
  A=','.join(v['fixed_tau_s']); B='|'.join(','.join(x) for x in v['precomputed_pairs_s']); Q='|'.join(','.join(map(str,x)) for x in v['causal_roots']); C[k]=f'F={A};P={B};C={Q}'
 z={'U_s':d['U_s'],'encoding':'F=fixed taus; P=precomputed pairs separated by |; C=causal roots firstL,firstH,LLmask,LHmask,HLmask,HHmask,tree_count separated by |; masks index U_s','nonempty_searched_cases':C,'searched_no_policy_cases':empty,'direct_pruned':'see direct_budget_audit.csv'}; zb=(json.dumps(z,separators=(',',':'))+'\n').encode(); (o/'passing_sets.json.gz.b64').write_text(base64.b64encode(gzip.compress(zb,mtime=0)).decode()+'\n'); (o/'selected_policy_trees.json').write_text(json.dumps(t,indent=2,sort_keys=True)+'\n'); wcsv(o/'resource_gaps.csv',['shield_mm','rho','epsilon','gap','path','baseline_passes','causal_passes','pass_saving','read_saving','write_saving','occupied_s_saving'],gaps(m,s)); wcsv(o/'numerical_boundary_summary.csv',['shield_mm','rho','epsilon','family_status','boundary_type','path','tau1_s','tau2_s','value','signed_value_minus_epsilon','absolute_gap','classification','numerical_status'],boundary(m))
if __name__=='__main__': main()
