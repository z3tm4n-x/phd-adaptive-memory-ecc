"""Freeze selected NOAA 5-minute SGPS filenames, including GOES-17 and dated holes."""
from concurrent.futures import ThreadPoolExecutor
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen
from urllib.parse import urljoin
import sys
import argparse

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'t67-goes-growth'))
from archive import ROOT,SPECIAL,Links
DAY=re.compile(r'^(dn|sci)_sgps-l2-avg5m_g(16|17|18|19)_d(\d{8})_v(\d+-\d+-\d+)\.nc$')
CUTOFF='20261109'


def get(url):
    error=None
    for attempt in range(3):
        try:
            request=Request(url,headers={'User-Agent':'C1 research archive inventory (SGPS)'})
            with urlopen(request,timeout=35) as response: return response.read()
        except OSError as e:
            error=e
            if attempt<2: time.sleep(attempt+1)
    raise OSError(f'{url}: {error}')


def inventory(cache):
    source_indexes={}
    unavailable={}
    cache.mkdir(parents=True,exist_ok=True)
    def listing(url):
        path=cache/(hashlib.sha256(url.encode()).hexdigest()+'.html')
        try:
            if path.exists(): data=path.read_bytes()
            else:
                data=get(url); path.write_bytes(data)
        except OSError as e:
            unavailable[url]=str(e);return []
        links=Links(); links.feed(data.decode())
        source_indexes[url]=hashlib.sha256(data).hexdigest()
        return links.links
    def children(url,pattern,low,high):
        return sorted({url+x for x in listing(url) if re.fullmatch(pattern,x) and low<=x<high})
    # The original dated T67 selection already covers G16/18/19 before Oct 2026.
    with gzip.open(HERE.parent/'t67-goes-growth/outputs/archive_files.csv.gz','rt',newline='') as stream:
        saved=[r for r in csv.DictReader(stream) if int(r['cadence_s'])==300 and r['date']<'20261001']
    frozen=[(int(r['satellite']),r['date'],tuple(map(int,r['version'].split('-'))),r['product_prefix']=='sci',r['url']) for r in saved]
    roots=[ROOT+'goes17/l2/data/sgps-l2-avg5m/']
    with ThreadPoolExecutor(max_workers=8) as pool:
        years=sum(pool.map(lambda u:children(u,r'20\d\d/','2017/','2027/'),roots),[])
        months=sum(pool.map(lambda u:children(u,r'\d\d/','01/','13/'),years),[])
        months=[u for u in months if ''.join(u.strip('/').split('/')[-2:])<=CUTOFF[:6]]
        months.extend(ROOT+f'goes{s}/l2/data/sgps-l2-avg5m/2026/{m:02}/' for s in (18,19) for m in (10,11))
        def entries(u):
            files=[]
            for f in listing(u):
                m=DAY.fullmatch(f)
                if m and '20170101'<=m[3]<CUTOFF:
                    files.append((int(m[2]),m[3],tuple(map(int,m[4].split('-'))),m[1]=='sci',urljoin(u,f)))
            return files
        members=frozen+sum(pool.map(entries,months),[])
    daily={}
    for s,day,v,science,url in sorted(members): daily[s,day]=url
    return {'cutoff_exclusive':'2026-11-09T00:00:00Z','source':'NCEI SGPS L2 avg5m',
            'selection':'largest numeric version, then sci; per satellite and UTC day',
            'index_hashes':dict(sorted(source_indexes.items())), 'unverified_indexes':dict(sorted(unavailable.items())), 'special':SPECIAL,
            'selected_daily':sorted(daily.values()), 'all_versions':len(members)}


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--out',required=True,type=Path); args=p.parse_args()
    out=inventory(args.out.parent/'indexes');args.out.parent.mkdir(exist_ok=True,parents=True)
    args.out.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print('selected daily files',len(out['selected_daily']),flush=True)


if __name__=='__main__':main()
