"""Cyclic-sequential and synchronous scrub survival engine."""
from __future__ import annotations
import math
import numpy as np
from ecc_word_model import log_clean_survival
BIN_S=300.0

def _H_eval(rate, seconds):
    """Piecewise-constant cumulative exposure from trace origin at arbitrary seconds."""
    r=np.asarray(rate,float); x=np.asarray(seconds,float); n=len(r); total=n*BIN_S
    if np.any(x< -1e-9): raise ValueError('time before rate trace')
    orig=x.copy(); xc=np.clip(x,0,total); idx=np.minimum((xc//BIN_S).astype(int),n-1); frac=xc-idx*BIN_S
    cs=np.r_[0.,np.cumsum(np.where(np.isfinite(r),r,0.)*BIN_S)]
    val=cs[idx]+np.where(frac==0,0.0,np.where(np.isfinite(r[idx]),r[idx]*frac,np.nan))
    val=np.where(xc==total,cs[-1],val)
    if np.any(orig>total): val=np.where(orig>total,cs[-1]+r[-1]*(orig-total),val)
    return val

def _valid_window_mask(rate,B):
    ok=np.isfinite(rate).astype(int); c=np.r_[0,np.cumsum(ok)]; return (c[B:]-c[:-B])==B

def _roll_sum(x,B):
    c=np.r_[0.,np.cumsum(np.asarray(x,float))];return c[B:]-c[:-B]

def _pattern_for_small_tau(tau,phi):
    """Return pattern classes of full scrub intervals starting inside each 300-s bin."""
    ti=int(round(tau)); g=math.gcd(300,ti); L=ti//g
    # schedule over one L-bin superperiod, starts at phi+k*tau
    out=[[] for _ in range(L)]
    end=L*BIN_S
    k=0
    while True:
        a=phi+k*tau
        if a>=end-1e-12: break
        q=int(a//BIN_S); u=a-q*BIN_S
        if q<L: out[q].append(u)
        k+=1
    return out

def _small_tau_all_starts(rate,B,tau,phases):
    r=np.asarray(rate,float);N=len(r);M=N-B+1; starts=np.arange(M)
    valid=_valid_window_mask(r,B)
    sum_log=np.zeros(M);sum_F=np.zeros(M);max_F=np.zeros(M)
    t0=starts*BIN_S; T=B*BIN_S
    for phi in phases:
        pattern=_pattern_for_small_tau(tau,phi);L=len(pattern)
        rs=np.nan_to_num(r,nan=0.0)
        # contribution from the infinite full-interval schedule, grouped by start bin.
        C=[]
        rn=np.r_[rs,rs[-1]]
        for qmod,offsets in enumerate(pattern):
            arr=np.zeros(N)
            for u in offsets:
                if u+tau <= BIN_S+1e-10:
                    arr += log_clean_survival(rs*tau)
                else:
                    mu=rs*(BIN_S-u)+rn[1:]*(u+tau-BIN_S)
                    arr += log_clean_survival(mu)
            C.append(arr)
        # choose pattern relative to each sliding-window start and rolling-sum it.
        full=np.zeros(M)
        for sres in range(L):
            vals=np.empty(N)
            for imod in range(L):
                idx=np.arange(imod,N,L);qmod=(imod-sres)%L;vals[idx]=C[qmod][idx]
            rr=_roll_sum(vals,B);sel=(starts%L)==sres;full[sel]=rr[sel]
        nfull=int(math.floor((T-phi+1e-12)/tau))
        last_start=phi+nfull*tau
        rem=T-last_start
        # infinite schedule includes the final partial's would-be full interval iff rem>0; subtract it.
        if rem>1e-10:
            a=t0+last_start; mu_full=_H_eval(r,a+tau)-_H_eval(r,a)
            full -= log_clean_survival(mu_full)
        mu0=_H_eval(r,t0+phi)-_H_eval(r,t0) if phi>0 else np.zeros(M)
        muf=_H_eval(r,t0+T)-_H_eval(r,t0+last_start) if rem>1e-10 else np.zeros(M)
        logsw=log_clean_survival(mu0)+full+log_clean_survival(muf)
        logsw=np.where(valid,logsw,np.nan);Fw=-np.expm1(logsw)
        sum_log += np.nan_to_num(logsw);sum_F += np.nan_to_num(Fw);max_F=np.maximum(max_F,np.nan_to_num(Fw))
    P=len(phases);mean_log=sum_log/P;meanF=sum_F/P;mean_log[~valid]=np.nan;meanF[~valid]=np.nan;max_F[~valid]=np.nan
    return mean_log,meanF,max_F,valid

def _large_tau_all_starts(rate,B,tau,phases):
    r=np.asarray(rate,float);N=len(r);M=N-B+1;starts=np.arange(M);valid=_valid_window_mask(r,B);T=B*BIN_S;m=int(round(tau/BIN_S))
    sum_log=np.zeros(M);sum_F=np.zeros(M);max_F=np.zeros(M); base=np.arange(N)*BIN_S
    for phi in phases:
        if phi >= T-1e-12:
            t0=starts*BIN_S; mu=_H_eval(r,t0+T)-_H_eval(r,t0); logsw=log_clean_survival(mu); logsw=np.where(valid,logsw,np.nan); Fw=-np.expm1(logsw); sum_log+=np.nan_to_num(logsw); sum_F+=np.nan_to_num(Fw); max_F=np.maximum(max_F,np.nan_to_num(Fw)); continue
        # G_i: log survival for one full tau interval starting at bin i + phi.
        max_i=N-m-1 if phi>1e-12 else N-m
        G=np.zeros(N)
        inds=np.arange(max(0,max_i+1)); a=inds*BIN_S+phi;mu=_H_eval(r,a+tau)-_H_eval(r,a);G[inds]=log_clean_survival(mu)
        nfull=int(math.floor((T-phi+1e-12)/tau)); last=phi+nfull*tau;rem=T-last
        full=np.zeros(M)
        if nfull:
            # sum G[s+k*m], k=0..nfull-1 using residue prefixes
            for res in range(m):
                ix=np.arange(res,N,m); pref=np.r_[0.,np.cumsum(G[ix])]; pos={int(v):j for j,v in enumerate(ix)}
                ss=starts[starts%m==res]
                if len(ss):
                    j=np.array([pos[int(v)] for v in ss]); full[ss]=pref[j+nfull]-pref[j]
        t0=starts*BIN_S
        mu0=_H_eval(r,t0+phi)-_H_eval(r,t0) if phi>0 else np.zeros(M)
        muf=_H_eval(r,t0+T)-_H_eval(r,t0+last) if rem>1e-10 else np.zeros(M)
        logsw=log_clean_survival(mu0)+full+log_clean_survival(muf);logsw=np.where(valid,logsw,np.nan);Fw=-np.expm1(logsw)
        sum_log+=np.nan_to_num(logsw);sum_F+=np.nan_to_num(Fw);max_F=np.maximum(max_F,np.nan_to_num(Fw))
    P=len(phases);ml=sum_log/P;mf=sum_F/P;ml[~valid]=np.nan;mf[~valid]=np.nan;max_F[~valid]=np.nan
    return ml,mf,max_F,valid

def cyclic_phase_aggregate(rate,window_bins,tau_s,phase_count=32):
    tau=float(tau_s); phases=(np.arange(phase_count)+.5)*tau/phase_count
    if tau<=BIN_S: return _small_tau_all_starts(rate,window_bins,tau,phases)
    if abs(tau/BIN_S-round(tau/BIN_S))>1e-12: raise ValueError('production tau>300 must be multiple of 300 s')
    return _large_tau_all_starts(rate,window_bins,tau,phases)

def synchronous_all_starts(rate,window_bins,tau_s):
    """Global reset at t0+tau,t0+2tau...; one phase phi=tau equivalent."""
    # use phase very near tau; cleaner direct generic calculation over each window is fine for QA only
    r=np.asarray(rate,float);N=len(r);B=window_bins;M=N-B+1;valid=_valid_window_mask(r,B);T=B*BIN_S;starts=np.arange(M);t0=starts*BIN_S
    tau=float(tau_s);n=int(T//tau);logsw=np.zeros(M)
    for k in range(n):
        a=t0+k*tau;b=np.minimum(t0+(k+1)*tau,t0+T);mu=_H_eval(r,b)-_H_eval(r,a);logsw+=log_clean_survival(mu)
    rem=T-n*tau
    if rem>1e-12:
        mu=_H_eval(r,t0+T)-_H_eval(r,t0+n*tau);logsw+=log_clean_survival(mu)
    logsw[~valid]=np.nan;return logsw

def aggregate_domain(mean_log_word,mean_F_word,max_F_word,N_words=524288):
    logS=N_words*mean_log_word; Fprod=-np.expm1(logS); upper=np.minimum(1.0,N_words*mean_F_word);lower=max_F_word
    return logS,Fprod,upper,lower

def cyclic_phase_aggregate_multi(rate, window_bins_list, tau_s, phase_count=16):
    """Exact phase quadrature for several reporting windows, reusing phase/tau preprocessing."""
    r=np.asarray(rate,float);N=len(r);tau=float(tau_s);Bs=tuple(int(b) for b in window_bins_list);phases=(np.arange(phase_count)+.5)*tau/phase_count
    acc={B:[np.zeros(N-B+1),np.zeros(N-B+1),np.zeros(N-B+1),_valid_window_mask(r,B)] for B in Bs}
    if tau<=BIN_S:
        # Each phase builds C arrays once; B-specific rolling queries are cheap.
        for phi in phases:
            pattern=_pattern_for_small_tau(tau,phi);L=len(pattern);rs=np.nan_to_num(r,nan=0.0);rn=np.r_[rs,rs[-1]];C=[]
            for offsets in pattern:
                arr=np.zeros(N)
                for u in offsets:
                    if u+tau<=BIN_S+1e-10: arr+=log_clean_survival(rs*tau)
                    else: arr+=log_clean_survival(rs*(BIN_S-u)+rn[1:]*(u+tau-BIN_S))
                C.append(arr)
            # Precompute rolling source arrays by start residue, one per B below.
            vals_by_sres=[]
            for sres in range(L):
                vals=np.empty(N)
                for imod in range(L):
                    ix=np.arange(imod,N,L);vals[ix]=C[(imod-sres)%L][ix]
                vals_by_sres.append(vals)
            for B in Bs:
                M=N-B+1;starts=np.arange(M);valid=acc[B][3];T=B*BIN_S;full=np.zeros(M)
                for sres,vals in enumerate(vals_by_sres):
                    rr=_roll_sum(vals,B);sel=starts%L==sres;full[sel]=rr[sel]
                nfull=int(math.floor((T-phi+1e-12)/tau));last=phi+nfull*tau;rem=T-last;t0=starts*BIN_S
                if rem>1e-10:
                    a=t0+last;full-=log_clean_survival(_H_eval(r,a+tau)-_H_eval(r,a))
                mu0=_H_eval(r,t0+phi)-_H_eval(r,t0)
                muf=_H_eval(r,t0+T)-_H_eval(r,t0+last) if rem>1e-10 else np.zeros(M)
                ls=log_clean_survival(mu0)+full+log_clean_survival(muf);ls=np.where(valid,ls,np.nan);fw=-np.expm1(ls)
                acc[B][0]+=np.nan_to_num(ls);acc[B][1]+=np.nan_to_num(fw);acc[B][2]=np.maximum(acc[B][2],np.nan_to_num(fw))
    else:
        if abs(tau/BIN_S-round(tau/BIN_S))>1e-12: raise ValueError('production tau>300 must be multiple of 300 s')
        m=int(round(tau/BIN_S)); allstarts={B:np.arange(N-B+1) for B in Bs}
        for phi in phases:
            max_i=N-m-1 if phi>1e-12 else N-m;G=np.zeros(N);inds=np.arange(max(0,max_i+1));a=inds*BIN_S+phi;G[inds]=log_clean_survival(_H_eval(r,a+tau)-_H_eval(r,a))
            # Intervals crossing missing GOES bins are irrelevant to any valid reporting
            # window, but NaNs must not poison residue-prefix sums for later valid starts.
            G=np.nan_to_num(G,nan=0.0)
            # prefix for each residue once
            pref_by_res={};ix_by_res={};pos_by_res={}
            for res in range(m):
                ix=np.arange(res,N,m);ix_by_res[res]=ix;pref_by_res[res]=np.r_[0.,np.cumsum(G[ix])]
            for B in Bs:
                starts=allstarts[B];M=len(starts);valid=acc[B][3];T=B*BIN_S;t0=starts*BIN_S
                if phi>=T-1e-12:
                    ls=log_clean_survival(_H_eval(r,t0+T)-_H_eval(r,t0))
                else:
                    nfull=int(math.floor((T-phi+1e-12)/tau));last=phi+nfull*tau;rem=T-last;full=np.zeros(M)
                    if nfull:
                        for res in range(m):
                            ss=starts[starts%m==res]
                            if not len(ss):continue
                            j=((ss-res)//m).astype(int);pref=pref_by_res[res];full[ss]=pref[j+nfull]-pref[j]
                    mu0=_H_eval(r,t0+phi)-_H_eval(r,t0);muf=_H_eval(r,t0+T)-_H_eval(r,t0+last) if rem>1e-10 else np.zeros(M)
                    ls=log_clean_survival(mu0)+full+log_clean_survival(muf)
                ls=np.where(valid,ls,np.nan);fw=-np.expm1(ls);acc[B][0]+=np.nan_to_num(ls);acc[B][1]+=np.nan_to_num(fw);acc[B][2]=np.maximum(acc[B][2],np.nan_to_num(fw))
    out={}
    for B,(sl,sf,mx,v) in acc.items():
        ml=sl/phase_count;mf=sf/phase_count;ml[~v]=np.nan;mf[~v]=np.nan;mx[~v]=np.nan;out[B]=(ml,mf,mx,v)
    return out
