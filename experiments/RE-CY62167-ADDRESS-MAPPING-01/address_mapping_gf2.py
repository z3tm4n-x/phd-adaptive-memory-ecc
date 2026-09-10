from __future__ import annotations
from collections import defaultdict
from typing import Iterable,Sequence
from address_mapping_data import *

def feature_mask(x:int,y:int)->int:
    if not(0<=x<=MAX_COORDINATE and 0<=y<=MAX_COORDINATE):raise ValueError('x/y outside 12-bit coordinate grid')
    v=1
    for i in range(COORD_BITS):
        if x>>i&1:v|=1<<(1+i)
        if y>>i&1:v|=1<<(1+COORD_BITS+i)
    return v

def gf2_rank(rows:Iterable[int],ncols:int)->int:
    basis=[0]*ncols;rank=0
    for v in map(int,rows):
        while v:
            p=v.bit_length()-1
            if p>=ncols:raise ValueError('row contains bit outside ncols')
            if basis[p]:v^=basis[p]
            else:basis[p]=v;rank+=1;break
    return rank

def gf2_rref(rows,ncols):
    work=sorted(set(int(v) for v in rows if v));r=0;piv=[]
    for col in range(ncols):
        q=next((k for k in range(r,len(work)) if work[k]>>col&1),None)
        if q is None:continue
        work[r],work[q]=work[q],work[r];p=work[r]
        for k in range(len(work)):
            if k!=r and work[k]>>col&1:work[k]^=p
        piv.append(col);r+=1
        if r==len(work):break
    return work[:r],piv

def solve_gf2_unique(rows:Sequence[int],rhs:Sequence[int],ncols:int)->int:
    if len(rows)!=len(rhs):raise ValueError('matrix/rhs length mismatch')
    basis=[None]*ncols
    for v,b in sorted((int(v),int(b)&1) for v,b in zip(rows,rhs)):
        while v:
            p=v.bit_length()-1
            if basis[p] is None:basis[p]=(v,b);break
            v^=basis[p][0];b^=basis[p][1]
        else:
            if b:raise ValueError('inconsistent GF(2) system')
    rank=sum(x is not None for x in basis)
    if rank!=ncols:raise ValueError(f'rank deficient: rank={rank}, ncols={ncols}')
    sol=0
    for p in range(ncols):
        row,b=basis[p];val=b^(((row&((1<<p)-1))&sol).bit_count()&1)
        if val:sol|=1<<p
    return sol

def fit_affine_mapping(records:Sequence[CellRecord]):
    ordered=sorted(records,key=lambda r:(r.x,r.y,r.field0_raw,r.source_file,r.segment_id,r.cluster_id,r.line_start,r.cell_index));rows=[feature_mask(r.x,r.y) for r in ordered];rank=gf2_rank(rows,FEATURE_COUNT)
    if rank<FEATURE_COUNT:return [],rank
    return [solve_gf2_unique(rows,[(int(r.field0_raw)>>j)&1 for r in ordered],FEATURE_COUNT) for j in range(ADDRESS_BITS)],rank

def predict_address(x,y,coeff):
    v=feature_mask(x,y);return sum((((v&int(c)).bit_count()&1)<<j) for j,c in enumerate(coeff))

def feature_names():return ['1']+[f'x{i}' for i in range(12)]+[f'y{i}' for i in range(12)]
def equation_string(j,c):
    t=[n for i,n in enumerate(feature_names()) if c>>i&1];return f'A{j} = '+(' xor '.join(t) if t else '0')

def deduplicate_event_local(records):
    g=defaultdict(list)
    for r in records:g[r.dedup_key].append(r)
    out=[];conf=[];removed=0
    for k in sorted(g):
        rs=sorted(g[k],key=lambda r:(r.field0_raw,r.line_start,r.cell_index,r.raw_fields));a=sorted({r.field0_raw for r in rs})
        if len(a)>1:conf.append({'dedup_key':list(k),'candidate_addresses':a,'raw_records':[list(r.raw_fields) for r in rs]})
        out.append(rs[0]);removed+=len(rs)-1
    return out,conf,removed

def nullspace_basis(rows,ncols):
    rr,piv=gf2_rref(rows,ncols);free=[i for i in range(ncols) if i not in piv];basis=[]
    for f in free:
        v=1<<f
        for row,p in zip(rr,piv):
            if row>>f&1:v|=1<<p
        basis.append(v)
    if any(any((row&v).bit_count()&1 for row in rows) for v in basis):raise AssertionError('invalid nullspace basis')
    return basis

def coord_vector_to_json(v):
    x=v&4095;y=(v>>12)&4095;bits=[f'x{i}' for i in range(12) if x>>i&1]+[f'y{i}' for i in range(12) if y>>i&1]
    return {'coordinate_bit_terms':bits,'xor_delta_x':x,'xor_delta_y':y,'bit_vector_24_lsb_order':[(v>>i)&1 for i in range(24)]}
