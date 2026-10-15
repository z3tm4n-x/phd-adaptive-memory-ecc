"""Lossless column-block storage for long text traces; no model functions.

All tokens, record order, spelling and timestamps are retained. Compression
does not regenerate PIN fields from an E model or discard clean operations.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import zlib

MAGIC=b'T106CT2\n'
BLOCK=16384


def encode_column(values):
    """Integer differences, not model differences; retain exact spelling."""
    width=len(values[0]) if all(len(v)==len(values[0]) for v in values) else 0
    for base in (10,16):
        try:numbers=[int(v,base) for v in values]
        except ValueError:continue
        render=lambda v:(str(v) if base==10 else format(v,'x')).zfill(width)
        if any(render(n)!=v for n,v in zip(numbers,values)):continue
        return ['n',base,width,[numbers[0]]+[b-a for a,b in zip(numbers,numbers[1:])]]
    return ['t',values]


def decode_column(encoded):
    if encoded[0]=='t':return encoded[1]
    _,base,width,deltas=encoded
    value=0;out=[]
    for delta in deltas:
        value+=delta
        out.append((str(value) if base==10 else format(value,'x')).zfill(width))
    return out


def lines(path):
    path=Path(path)
    if path.suffix!='.ctz':
        opener=gzip.open if path.suffix=='.gz' else open
        with opener(path,'rt') as f:yield from f
        return
    with path.open('rb') as f:
        version=f.read(len(MAGIC))
        if version not in (b'T106CT1\n',MAGIC):raise ValueError('trace codec signature')
        while size:=f.read(4):
            if len(size)!=4:raise ValueError('short block size')
            n=struct.unpack('<I',size)[0]
            if not 0<n<64*1024*1024:raise ValueError('block size limit')
            data=f.read(n)
            if len(data)!=n:raise ValueError('short trace block')
            order,kinds,columns=json.loads(zlib.decompress(data))
            if version==MAGIC:columns=[[decode_column(col) for col in cols] for cols in columns]
            cursors=[0]*len(kinds)
            if len(order)>BLOCK:raise ValueError('record count limit')
            for k in order:
                i=cursors[k];cursors[k]+=1
                yield ' '.join([kinds[k]]+[col[i] for col in columns[k]])+'\n'
            if any(any(len(col)!=cursors[k] for col in cols) for k,cols in enumerate(columns)):
                raise ValueError('unused columns')


def rows(path):
    for i,line in enumerate(lines(path),1):
        f=line.split()
        if f:yield i,f


def digest(path):
    h=hashlib.sha256()
    for line in lines(path):h.update(line.encode('ascii'))
    return h.hexdigest()


def pack(source,dest):
    h=hashlib.sha256();count=0;order=[];kinds=[];columns=[];index={}
    def flush(out):
        if not order:return
        encoded=[[encode_column(col) for col in cols] for cols in columns]
        data=zlib.compress(json.dumps([order,kinds,encoded],separators=(',',':')).encode('ascii'),9)
        out.write(struct.pack('<I',len(data)));out.write(data)
        order.clear();kinds.clear();columns.clear();index.clear()
    with Path(dest).open('wb') as out:
        out.write(MAGIC)
        for line in lines(source):
            fields=line.split()
            if not fields or line!=' '.join(fields)+'\n':raise ValueError('noncanonical trace text')
            h.update(line.encode('ascii'));count+=1
            kind=fields[0]
            if kind not in index:
                index[kind]=len(kinds);kinds.append(kind);columns.append([[] for _ in fields[1:]])
            k=index[kind];order.append(k)
            if len(columns[k])!=len(fields)-1:raise ValueError('inconsistent record width')
            for col,value in zip(columns[k],fields[1:]):col.append(value)
            if len(order)==BLOCK:flush(out)
        flush(out)
    if digest(dest)!=h.hexdigest():raise AssertionError('lossless roundtrip failed')
    return dict(records=count,raw_sha256=h.hexdigest(),bytes=Path(dest).stat().st_size)


def compare(a,b):
    # Exact original rows outside jumps, including memory/app/permission rows.
    ar=[f for _,f in rows(a) if f[0]!='END'];br=[f for _,f in rows(b) if f[0]!='END']
    jumps=[f for f in br if f[0]=='JUMP'];assert jumps
    intervals=[(int(f[1]),int(f[1])+int(f[2])*1000) for f in jumps]
    for f in ar:
        if f[0]=='JUMP':assert f in br,'baseline jump changed'
    expected=[f for f in ar if f[0]!='JUMP' and not any(x<=int(f[1])<y for x,y in intervals)]
    actual=[f for f in br if f[0]!='JUMP']
    assert len(expected)==len(actual),('tail length',len(expected),len(actual))
    for i,(x,y) in enumerate(zip(expected,actual)):
        assert x==y,('first tail difference',i,x,y)
    return dict(compared_rows=len(expected),represented_intervals=len(jumps))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('dest');a=p.parse_args()
    print(json.dumps(pack(a.source,a.dest)))
