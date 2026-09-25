from __future__ import annotations
import math, re, hashlib
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
import numpy as np, h5py

N_BITS=16_777_216
FOUR_PI=4*math.pi
SHIELDS=(0.,1.,2.,3.,5.,7.,10.)
OLD_LO=np.array([1.02,1.90,2.31,3.40,5.84,11.64]); OLD_HI=np.array([1.86,2.30,3.34,6.48,11.00,23.27])
CORR_LO=np.array([0.92,1.80,2.20,3.30,6.30,12.4]); CORR_HI=np.array([1.80,2.20,3.20,6.20,11.7,23.3]); CORR=np.array([.656,.688,.708,.625,.618,.753])
EPOCH=datetime(2000,1,1,12,tzinfo=timezone.utc)
SIG_E=np.array([.9,1.,1.1,1.5,2.5,3.,4.,5.,40.,80.,124.,164.,184.,186.])
SIG_S=np.array([9.41e-10,1.27e-9,4.02e-10,5.58e-11,1.61e-12,6.13e-13,1.49e-13,6.82e-14,1e-13,9e-14,8e-14,7.8e-14,7.73e-14,8.2e-14])
PUB_E=np.array([0.804918275,0.901437971,0.974395614,1.0988785,1.5050335,2.0088794,2.49665934,2.99006635,4.00393596,4.97881106,39.8676386,79.6744857,185.048672])
PUB_S=np.array([7.378374012e-10,1.264976068e-9,1.143508257e-9,7.289529628e-10,2.824585756e-11,1.965619489e-12,4.094295288e-13,1.329744164e-13,1.695785056e-14,5.452245901e-15,1.000301271e-13,9.115809830e-14,6.467389864e-14])

def sha256(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def _fill(ds):
 a=np.asarray(ds[...],float); fill=float(np.asarray(ds.attrs.get('_FillValue',[-1e31])).ravel()[0]); a[(~np.isfinite(a))|(a<=fill/2)|(a<0)]=np.nan; return a
@dataclass
class Goes:
 times:list; flux:np.ndarray; p11:np.ndarray; valid:np.ndarray; eff:np.ndarray; lo:np.ndarray; hi:np.ndarray; files:list

def load_goes(root):
 paths=sorted(Path(root).rglob('*.nc'))
 if len(paths)!=59: raise ValueError(len(paths))
 ts=[]; fs=[]; ps=[]; vs=[]; ref=None; metas=[]
 for p in paths:
  with h5py.File(p,'r') as f:
   t=[EPOCH+timedelta(seconds=float(x)) for x in f['time'][...]]; yaw=np.asarray(f['yaw_flip_flag'][...],np.uint8)
   raw=_fill(f['AvgDiffProtonFlux'])*1000; p11=_fill(f['AvgIntProtonFlux'])
   lo=np.asarray(f['DiffProtonLowerEnergy'][...],float)/1000; hi=np.asarray(f['DiffProtonUpperEnergy'][...],float)/1000; eff=np.asarray(f['DiffProtonEffectiveEnergy'][...],float)/1000
   old=np.allclose(lo[:,:6],OLD_LO[None,:],rtol=0,atol=.011) and np.allclose(hi[:,:6],OLD_HI[None,:],rtol=0,atol=.011)
   corr=np.allclose(lo[:,:6],CORR_LO[None,:],rtol=0,atol=.011) and np.allclose(hi[:,:6],CORR_HI[None,:],rtol=0,atol=.011)
   if old:
    raw[:,:,:6]*=CORR[None,None,:];lo[:,:6]=CORR_LO;hi[:,:6]=CORR_HI;eff[:,:6]=np.sqrt(CORR_LO*CORR_HI)
   elif not corr: raise ValueError('bounds')
   if ref is None: ref=(lo.copy(),hi.copy(),eff.copy())
   else:
    for a,b in zip(ref,(lo,hi,eff)):
     if not np.array_equal(a,b): raise ValueError('energy metadata changed')
   out=np.full_like(raw,np.nan); outp=np.full_like(p11,np.nan); valid=np.zeros(raw.shape[:2],bool)
   for i,y in enumerate(yaw):
    if y==0: out[i,0]=raw[i,1];out[i,1]=raw[i,0];outp[i,0]=p11[i,1];outp[i,1]=p11[i,0]
    elif y==2: out[i,0]=raw[i,0];out[i,1]=raw[i,1];outp[i,0]=p11[i,0];outp[i,1]=p11[i,1]
    else: continue
    valid[i]=np.all(np.isfinite(out[i]),axis=1)
   ts.extend(t);fs.append(out);ps.append(outp);vs.append(valid);metas.append((p.name,sha256(p)))
 sec=np.array([x.timestamp() for x in ts]);
 if len(ts)!=16992 or not np.all(np.diff(sec)==300):raise ValueError('cadence')
 lo0,hi0,ef0=ref; lower=np.stack([lo0[1],lo0[0]]);upper=np.stack([hi0[1],hi0[0]]);effective=np.stack([ef0[1],ef0[0]])
 return Goes(ts,np.concatenate(fs),np.concatenate(ps),np.concatenate(vs),effective,lower,upper,metas)

def reconstruct_on_grid(eff,flux,lo,hi,grid):
 grid=np.asarray(grid,float); out=np.full(grid.shape,np.nan); m=(grid>=lo)&(grid<=hi)
 if not np.any(m): return out
 x=grid[m]; le=np.log(np.asarray(eff,float)); lx=np.log(x)
 # np.interp supplies endpoint holds, exactly the required support-edge constant extension
 out[m]=np.interp(lx,le,np.asarray(flux,float))
 return out

def reconstruct(goes,grid):
 T=len(goes.times); J=np.full((T,2,len(grid)),np.nan)
 for d in range(2):
  for t in np.flatnonzero(goes.valid[:,d]):
   z=reconstruct_on_grid(goes.eff[d],goes.flux[t,d],float(goes.lo[d,0]),float(goes.hi[d,-1]),grid)
   J[t,d]=np.where(np.isfinite(z),z,0)
 return J

def sigma_main(E):
 E=np.asarray(E,float); y=np.empty_like(E); inside=(E>=SIG_E[0])&(E<=SIG_E[-1]); y[inside]=np.exp(np.interp(np.log(E[inside]),np.log(SIG_E),np.log(SIG_S)))
 slope=(SIG_S[1]-SIG_S[0])/(SIG_E[1]-SIG_E[0]); low=E<SIG_E[0];y[low]=np.maximum(0,SIG_S[0]+slope*(E[low]-SIG_E[0]));y[E>SIG_E[-1]]=SIG_S[-1];return y

def zero_cross():
 slope=(SIG_S[1]-SIG_S[0])/(SIG_E[1]-SIG_E[0]);return SIG_E[0]-SIG_S[0]/slope

def sigma_model(E,name):
 E=np.asarray(E,float); y=sigma_main(E)
 if name=='main_loglog':return y
 if name!='published_rpp_fluka_digitized':raise ValueError(name)
 m=(E>=PUB_E[0])&(E<=PUB_E[-1]);y[m]=np.exp(np.interp(np.log(E[m]),np.log(PUB_E),np.log(PUB_S)));y[E>PUB_E[-1]]=PUB_S[-1];return y

def trap_weights(x):
 x=np.asarray(x,float);w=np.zeros_like(x);w[0]=(x[1]-x[0])/2;w[-1]=(x[-1]-x[-2])/2;w[1:-1]=(x[2:]-x[:-2])/2;return w

def low_ext(goes,grid,gamma=2):
 out=np.zeros((len(goes.times),2,len(grid)))
 ez=zero_cross()
 for d in range(2):
  lo=float(goes.lo[d,0]);mask=(grid>=ez)&(grid<lo);shape=(grid[mask]/lo)**(-gamma)
  v=goes.valid[:,d]&np.isfinite(goes.flux[:,d,0]);out[np.ix_(v,[d],mask)]=goes.flux[v,d,0][:,None,None]*shape[None,None,:]
 return out

def solve_gamma(j390,p11):
 if not(np.isfinite(j390) and np.isfinite(p11) and j390>0 and p11>0):return None
 ratio=p11/(j390*500);lo=1+1e-8;hi=100
 def f(g):return (390/500)**g/(g-1)-ratio
 while f(hi)>0 and hi<1e6:hi*=2
 for _ in range(80):
  mid=(lo+hi)/2
  if f(mid)>0:lo=mid
  else:hi=mid
 return (lo+hi)/2

def gap_integrals(goes):
 T=len(goes.times);g=np.full((T,2),np.nan);med=np.zeros(2)
 for d in range(2):
  vals=[]
  for t in range(T):
   if goes.valid[t,d]:
    q=solve_gamma(float(goes.flux[t,d,-1]),float(goes.p11[t,d]));
    if q is not None:g[t,d]=q;vals.append(q)
  med[d]=np.median(vals) if vals else 1.2
  g[goes.valid[:,d]&~np.isfinite(g[:,d]),d]=med[d]
 integ=np.full((T,2),np.nan)
 for d in range(2):
  for t in np.flatnonzero(goes.valid[:,d]):
   q=g[t,d];j=float(goes.flux[t,d,-1]);p=float(goes.p11[t,d])
   if j>0 and solve_gamma(j,p) is not None:
    a=500/390;integ[t,d]=j*390*((a**(1-q)-1)/(1-q))
   else: integ[t,d]=max(0,p)*((500/390)**(q-1)-1)
 return integ

def calculate_energy_contributions(goes,transport_path,sigma_names=('main_loglog','published_rpp_fluka_digitized')):
 z=np.load(transport_path);E=np.asarray(z['energy_mev'],float);sh=np.asarray(z['shield_mm'],float);P=np.asarray(z['primary'],float);S=np.asarray(z['secondary'],float)
 if tuple(sh.tolist())!=SHIELDS:raise ValueError('shields')
 J=reconstruct(goes,E)*FOUR_PI;L=low_ext(goes,E)*FOUR_PI;inp=J+L;gap=gap_integrals(goes);tw=trap_weights(E)
 result={}
 for sm in sigma_names:
  sig=sigma_model(E,sm); high=float(sigma_model(np.array([600.]),sm)[0]);
  # grid contribution excludes P11/gap; high bucket separately
  for di,mm in enumerate(sh):
   dens=np.full((len(goes.times),2,len(E)),np.nan);highbit=np.full((len(goes.times),2),np.nan)
   for d in range(2):
    v=goes.valid[:,d]
    out=inp[v,d]@P[di].T+inp[v,d]@S[di].T
    dens[v,d]=N_BITS*out*sig[None,:]*tw[None,:]
    highbit[v,d]=N_BITS*FOUR_PI*high*(gap[v,d]+goes.p11[v,d])
   total=np.nansum(dens,axis=2)+highbit
   total[~goes.valid]=np.nan
   result[sm,float(mm)]={'density':dens,'highbit':highbit,'total':total}
 return E,result
MULT_POINTS=[
(.9,7455,7507,7403),(1.,4690,4710,4670),(1.1,14012,14090,13934),(1.5,3214,3224,3204),(2.5,28782,29008,28564),(3.,24703,25040,24383),(4.,4336,4406,4269),(5.,1994,2053,1936),(29.,1165,1183,1147),(40.,12442,16402,9972),(80.,10890,15325,8489),(124.,9404,13632,7177),(164.,8668,13358,6446),(186.,8356,12972,6150)]
def multiplicity_grid(E,low='low_energy_conservative'):
 xp=np.array([x[0] for x in MULT_POINTS]); pp=np.array([(ne-n1)/ne for _,ne,nb,n1 in MULT_POINTS]); kk=np.array([nb/ne for _,ne,nb,n1 in MULT_POINTS]);E=np.asarray(E,float)
 p=np.full_like(E,pp[-1]);k=np.full_like(E,kk[-1]);m=(E>=xp[0])&(E<=xp[-1]);p[m]=np.interp(np.log(E[m]),np.log(xp),pp);k[m]=np.interp(np.log(E[m]),np.log(xp),kk)
 lowm=E<xp[0]
 pl=max(pp[(xp>=.9)&(xp<=3)])
 if low=='K1_only':p[lowm]=0;k[lowm]=1
 elif low=='low_energy_conservative':p[lowm]=pl;k[lowm]=1+pl
 else:raise ValueError(low)
 return p,k

def dcluster_rates(E,contrib,low):
 p,k=multiplicity_grid(E,low); out={}
 for key,r in contrib.items():
  dens=r['density'];hb=r['highbit']; ev=np.nansum(dens/k[None,None,:],axis=2)+hb/k[-1]; dr=np.nansum(dens*(p/k)[None,None,:],axis=2)+hb*p[-1]/k[-1]
  ev[~np.isfinite(r['total'])]=np.nan;dr[~np.isfinite(r['total'])]=np.nan;out[key]=(ev,dr)
 return out
def partition_dcluster(E,r,low):
 p,k=multiplicity_grid(E,low);dens=r['density'];hb=r['highbit'];direct=np.nansum(dens*(p/k)[None,None,:],axis=2)+hb*p[-1]/k[-1];acc=np.nansum(dens*((1-p)/k)[None,None,:],axis=2)+hb*(1-p[-1])/k[-1];direct[~np.isfinite(r['total'])]=np.nan;acc[~np.isfinite(r['total'])]=np.nan;return direct,acc

def select_direction(a,name):
 if name=='East':return a[:,0]
 if name=='West':return a[:,1]
 if name=='central_mean':return np.where(np.all(np.isfinite(a),axis=1),np.mean(a,axis=1),np.nan)
 raise ValueError(name)
