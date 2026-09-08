#!/usr/bin/env python3
import importlib.util,json
from fractions import Fraction as R
from pathlib import Path
D=Path(__file__).parent; sp=importlib.util.spec_from_file_location('sa',D/'stage_a.py'); s=importlib.util.module_from_spec(sp); sp.loader.exec_module(s); c=json.loads((D/'config.json').read_text()); m=s.load(c)
def test_config_architecture():
 assert m['N']==m['nw']*m['n']==2**24 and m['P']==R(18874368,10**8); assert all(t>=m['P'] and m['B']/t==int(m['B']/t) for t in m['U'])
def test_conservation():
 for d in m['rate']:
  for b in m['rate'][d].values():
   for r in m['R']: assert (1-r)*b+2*(r*b/2)==b
def test_phase_sum():
 for nw in (3,5,8):
  P=R(7,50); B=R(6); t1=R(1,2); t2=R(1); r1=R(11,997); r2=R(13,991); z=R(0)
  for w in range(nw):
   a=P-P*R(w+1,nw); xs=[r1*(t1-a)]+[r1*t1]*(int(B/t1)-1)+[r1*a+r2*(t2-a)]+[r2*t2]*(int(B/t2)-1)+[r2*a]; z+=sum(x*x for x in xs)
  A1=P*R(nw-1,2); A2=P*P*R((nw-1)*(2*nw-1),6*nw); q1=int(B/t1);q2=int(B/t2); q=r1*r1*(nw*t1*t1-2*t1*A1+A2)+(q1-1)*nw*(r1*t1)**2+nw*(r2*t2)**2+2*r2*t2*(r1-r2)*A1+(r1-r2)**2*A2+(q2-1)*nw*(r2*t2)**2+r2*r2*A2; assert z==q
def test_stationary_reduction():
 beta=R(31,2*2**24)
 for b in (R(1,7),R(31,10)):
  for r in m['R']:
   nu=(1-r)*b
   for t in m['U'][:5]: assert m['n']*(m['n']-1)//2*m['nw']*int(m['T']/t)*(nu/m['N']*t)**2==beta*t*m['T']*nu*nu
def test_limits():
 for d in m['rate']:
  for p in s.PTH:
   b1,b2=s.rates(m,d,p); assert s.ld(m,b1,b2,R(0))==0; assert s.pair(m,b1,b2,R(1),m['U'][0],m['U'][0])==0
def test_resources():
 for a in m['U']:
  for b in m['U']:
   p,rd,wr,o,f=s.res(m,a,b); assert p==int(300/a)+int(300/b) and rd==wr==p*2**21 and o==p*m['P']
def test_causal_prefixes():
 rr=list(s.roots(m,'d5',R(0),R(1,100))); assert rr
 for aL,aH,A in rr[:20]:
  for p in s.PTH:
   a=aL if p[0]=='L' else aH; assert all(s.ok(m,'d5',R(0),R(1,100),p,a,b) for b in A[p])
def test_class_inclusion():
 d='d5';r=R(0);e=R(1,100); fx=list(s.fixed(m,d,r,e));pr=list(s.pre(m,d,r,e));rr={(a,b):A for a,b,A in s.roots(m,d,r,e)}; pp={(x['LL'][0],x['LL'][1]) for x in pr}; assert all((x['LL'][0],x['LL'][0]) in pp for x in fx); assert all(x['LL'][1] in rr[(x['LL'][0],x['LL'][0])][p] for x in pr for p in s.PTH)
def test_tie_rule():
 A={p:(R(30),R(30)) for p in s.PTH};B={p:(R(20),R(60)) for p in s.PTH}; assert s.pc(m,*A['LL'])==s.pc(m,*B['LL'])==20 and s.key(m,A)<s.key(m,B)
if __name__=='__main__':
 T=[v for k,v in sorted(globals().items()) if k.startswith('test_')]
 for t in T:t();print('PASS',t.__name__)
 print(len(T),'tests passed')
