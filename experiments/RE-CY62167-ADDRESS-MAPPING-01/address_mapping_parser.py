from __future__ import annotations
import re
from collections import Counter
from typing import Optional,Sequence
from address_mapping_data import *
HEADER_RE=re.compile(r'^cluster\s+(\d+)\s+with xmin\s+(-?\d+)\s+xmax\s+(-?\d+)\s+ymin\s+(-?\d+)\s+ymax\s+(-?\d+)\s*$')
XADD_RE=re.compile(r'^xadd\s+(-?\d+)\s+yadd\s+(-?\d+)(?:\s+(\d+):(\d+):(\d+))?\s*$')
COUNT_RE=re.compile(r'^NUMBER OF EVENTS\s*=\s*(\d+)\s*$')

def normalize_timestamp(h:Optional[str],m:Optional[str],s:Optional[str]):
    if h is None:return None
    a,b,c=map(int,(h,m,s))
    if not(0<=a<=23 and 0<=b<=59 and 0<=c<=59):raise ValueError('invalid timestamp')
    return f'{a:02d}:{b:02d}:{c:02d}'

def _zero_geometry(xmin,xmax,ymin,ymax,xadd,yadd,cells:Sequence[tuple[int,...]]):
    return (xmin,xmax,ymin,ymax,xadd,yadd)==(0,0,0,0,0,0) and len(cells)==1 and ((len(cells[0])==2 and cells[0]==(0,0)) or (len(cells[0])==3 and cells[0][1:]==(0,0)))

def classify_cell(*,cluster_id,timestamp_raw,xmin,xmax,ymin,ymax,xadd,yadd,cells,cell):
    zero=_zero_geometry(xmin,xmax,ymin,ymax,xadd,yadd,cells)
    if len(cell)==3:
        a,x,y=cell
        if timestamp_raw=='03:03:03' and zero and a>MAX_EXTERNAL_ADDRESS:return 'STRICT_SERVICE','03:03:03 all-zero singleton with leading integer outside external 21-bit address range'
        if timestamp_raw=='03:03:03' and zero and 0<=a<=MAX_EXTERNAL_ADDRESS:return 'AMBIGUOUS','03:03:03 all-zero singleton is service-like but leading integer lies inside external address range'
        if not 0<=a<=MAX_EXTERNAL_ADDRESS:return 'AMBIGUOUS','three-field record has leading integer outside external 21-bit range without strict service signature'
        if not(0<=x<=MAX_COORDINATE and 0<=y<=MAX_COORDINATE):return 'AMBIGUOUS','coordinate outside declared 12-bit supplied grid'
        return 'PHYSICAL_ELIGIBLE','ordinary three-field record in declared address/coordinate ranges'
    if len(cell)==2:
        x,y=cell
        if timestamp_raw is None and cluster_id==0 and zero and x==0 and y==0:return 'AMBIGUOUS','non-timestamped cluster-0 all-zero singleton lacks evidence to distinguish physical cell from service record'
        if not(0<=x<=MAX_COORDINATE and 0<=y<=MAX_COORDINATE):return 'AMBIGUOUS','coordinate outside declared 12-bit supplied grid'
        return 'PHYSICAL_NO_ADDRESS','ordinary two-field record has XY but no candidate address field'
    raise ValueError('unsupported cell arity')

def parse_cluster_text(source_file:str,text:str):
    lines=text.splitlines();i=0;seg=1;prev=None;records=[];clusters=0;bounds_bad=0
    while i<len(lines):
        if not lines[i].strip():i+=1;continue
        start=i+1; h=HEADER_RE.match(lines[i].strip())
        if not h:raise ValueError(f'{source_file}:{i+1}: unexpected line')
        cid,xmin,xmax,ymin,ymax=map(int,h.groups())
        if prev is not None and cid<=prev:seg+=1
        prev=cid;i+=1
        if i>=len(lines):raise ValueError('missing xadd line')
        m=XADD_RE.match(lines[i].strip())
        if not m:raise ValueError('invalid xadd line')
        xadd,yadd=map(int,m.groups()[:2]);ts=normalize_timestamp(*m.groups()[2:]);i+=1;cells=[]
        while i<len(lines) and not COUNT_RE.match(lines[i].strip()):
            raw=lines[i].strip()
            if raw:
                parts=tuple(map(int,raw.split()))
                if len(parts) not in(2,3):raise ValueError('unsupported cell row')
                cells.append(parts)
            i+=1
        if i>=len(lines):raise ValueError('missing NUMBER OF EVENTS')
        declared=int(COUNT_RE.match(lines[i].strip()).group(1));i+=1
        if declared!=len(cells):raise ValueError(f'{source_file}:{start}: NUMBER OF EVENTS={declared}, parsed={len(cells)}')
        if cells:
            xs=[c[-2] for c in cells];ys=[c[-1] for c in cells]
            bounds_bad+=((min(xs),max(xs),min(ys),max(ys))!=(xmin,xmax,ymin,ymax))
        for n,c in enumerate(cells):
            a,x,y=(c if len(c)==3 else (None,*c));cl,reason=classify_cell(cluster_id=cid,timestamp_raw=ts,xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax,xadd=xadd,yadd=yadd,cells=cells,cell=c)
            records.append(CellRecord(source_file,seg,cid,start,n,ts,xmin,xmax,ymin,ymax,xadd,yadd,declared,len(c),a,x,y,c,cl,reason))
        clusters+=1
    cc=Counter(r.classification for r in records)
    bad=sum(not(0<=r.x<=MAX_COORDINATE and 0<=r.y<=MAX_COORDINATE) for r in records)
    return records,ParseStats(source_file,clusters,len(records),sum(r.field_arity==2 for r in records),sum(r.field_arity==3 for r in records),cc['STRICT_SERVICE'],cc['AMBIGUOUS'],cc['PHYSICAL_ELIGIBLE'],cc['PHYSICAL_NO_ADDRESS'],bounds_bad,bad)
