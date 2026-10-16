"""Large generic column blocks. No calendar, memory or E-model regeneration."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import struct
from trace_codec import lines as old_lines,encode_column,decode_column

MAGIC=b'T106CT3\n'
BLOCK=131072


def lines(path):
    path=Path(path)
    if path.suffix!='.ct3':
        yield from old_lines(path);return
    with path.open('rb') as f:
        if f.read(8)!=MAGIC:raise ValueError('CT3 signature')
        while size:=f.read(4):
            if len(size)!=4:raise ValueError('short CT3 size')
            n=struct.unpack('<I',size)[0]
            if not 0<n<=64*1024*1024:raise ValueError('CT3 size limit')
            data=f.read(n)
            if len(data)!=n:raise ValueError('short CT3 block')
            order,kinds,columns=json.loads(lzma.decompress(data))
            columns=[[decode_column(c) for c in cols] for cols in columns]
            if len(order)>BLOCK:raise ValueError('CT3 row limit')
            cursors=[0]*len(kinds)
            for k in order:
                i=cursors[k];cursors[k]+=1
                yield ' '.join([kinds[k]]+[col[i] for col in columns[k]])+'\n'
            if any(any(len(col)!=cursors[k] for col in cols) for k,cols in enumerate(columns)):
                raise ValueError('unused CT3 columns')


def rows(path):
    for i,line in enumerate(lines(path),1):
        if f:=line.split():yield i,f


def digest(path):
    h=hashlib.sha256()
    for line in lines(path):h.update(line.encode('ascii'))
    return h.hexdigest()


def pack(source,dest):
    h=hashlib.sha256();count=0;order=[];kinds=[];columns=[];index={}
    def flush(out):
        if not order:return
        encoded=[[encode_column(col) for col in cols] for cols in columns]
        data=lzma.compress(json.dumps([order,kinds,encoded],separators=(',',':')).encode('ascii'),preset=3)
        out.write(struct.pack('<I',len(data)));out.write(data)
        order.clear();kinds.clear();columns.clear();index.clear()
    with Path(dest).open('wb') as out:
        out.write(MAGIC)
        for line in lines(source):
            fields=line.split()
            if not fields or line!=' '.join(fields)+'\n':raise ValueError('noncanonical trace')
            h.update(line.encode('ascii'));count+=1;kind=fields[0]
            if kind not in index:
                index[kind]=len(kinds);kinds.append(kind);columns.append([[] for _ in fields[1:]])
            k=index[kind];order.append(k)
            if len(columns[k])!=len(fields)-1:raise ValueError('record width')
            for col,v in zip(columns[k],fields[1:]):col.append(v)
            if len(order)==BLOCK:flush(out)
        flush(out)
    if digest(dest)!=h.hexdigest():raise AssertionError('CT3 roundtrip')
    return dict(records=count,raw_sha256=h.hexdigest(),bytes=Path(dest).stat().st_size)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('dest');a=p.parse_args()
    print(json.dumps(pack(a.source,a.dest)),flush=True)
