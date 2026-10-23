"""Bounded source-access snapshot; no event selection or slope estimation.

Raw snapshots are outside Git. Re-running records a new retrieval time and may
find changed remote data; it is not a byte-identical scientific replay.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE='https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/'
URLS={
    'legacy_products':'https://www.ncei.noaa.gov/products/goes-1-15/space-weather-instruments',
    'legacy_full':'https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/full/',
    'legacy_avg':'https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/avg/',
    'legacy_fits_readme':'https://archive.data.noaa.gov/satellite-spaceweather/GOES1-15/docs/goes_operational_data/SMS-1_GOES-7_Full_Resolution_Data_Readme.txt',
    'legacy_avg_readme':'https://archive.data.noaa.gov/satellite-spaceweather/GOES1-15/docs/goes_operational_data/SMS-1_GOES_12_Averaged_Data_Readme.txt',
    'seiss_products':'https://www.ncei.noaa.gov/products/goes-r-space-environment-in-situ',
    'g19_readme':BASE+'goes19/l1b/docs/GOES-19_SEISS_SGPS_L1b_Provisional_Maturity_ReadMe.pdf',
    **{f'g{sat}_l1b':BASE+f'goes{sat}/l1b/seis-l1b-sgps/' for sat in [16,17,18,19]},
    **{f'g{sat}_1m':BASE+f'goes{sat}/l2/data/sgps-l2-avg1m/' for sat in [16,17,18,19]},
    'g19_1m_2026':BASE+'goes19/l2/data/sgps-l2-avg1m/2026/',
    'g19_1m_202610':BASE+'goes19/l2/data/sgps-l2-avg1m/2026/10/',
    'g19_l1b_202610':BASE+'goes19/l1b/seis-l1b-sgps/2026/10/',
}


class Links(HTMLParser):
    def __init__(self):super().__init__();self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.hrefs.extend(v for k,v in attrs if k=='href')


def fetch(item,cache):
    name,url=item;when=datetime.now(timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(url,timeout=25) as response:
            data=response.read(8*1024*1024+1)
            if len(data)>8*1024*1024:raise ValueError('metadata snapshot exceeds 8 MiB cap')
            info=dict(id=name,url=url,retrieved_utc=when,status=response.status,
                final_url=response.url,content_type=response.headers.get('Content-Type'),
                last_modified=response.headers.get('Last-Modified'),bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest())
        suffix='.pdf' if url.endswith('.pdf') else '.txt' if url.endswith('.txt') else '.html'
        (cache/(name+suffix)).write_bytes(data)
        if suffix=='.html':
            parser=Links();parser.feed(data.decode('utf-8','replace'))
            entries=sorted(set(x for x in parser.hrefs if re.fullmatch(r'\d{2,4}/',x) or x.endswith(('.nc','.FIT','.fit'))))
            info.update(entries=entries,scope='directory entries only; not valid time coverage')
        return info
    except Exception as exc:
        return dict(id=name,url=url,retrieved_utc=when,status='UNAVAILABLE',error=str(exc),valid_coverage=None)


def local_sepem(path):
    records=[]
    expected={'SEPEM_H_reference.txt':'012b8a375ded951fef9bd9268e20a97556a8a7ebc171dd8b7d0763141a41fa50',
        'SEPEM_He_reference.txt':'232d068905d6fcc3dd79bd9b0ad69181f1d49496a523c6042a5455599d4a0f22',
        'data_readme_ftp.txt':'9c8a8b606b69228dad6a80acbd3adfb3a64e0d9be7f5ef930c3a9a67ab0e3e7b'}
    for p in sorted(path.glob('*')):
        if not p.is_file():continue
        rec=dict(name=p.name,bytes=p.stat().st_size,exists=True)
        if p.name in expected:
            digest=hashlib.sha256()
            with p.open('rb') as f:
                for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
            rec.update(sha256=digest.hexdigest(),matches_accepted_passport=digest.hexdigest()==expected[p.name])
            if not rec['matches_accepted_passport']:raise ValueError('SEPEM pinned source mismatch: '+p.name)
        if p.name.startswith('SEPEM_'):
            with p.open('rb') as f:
                header=f.readline().decode('ascii','replace').strip()
                first=f.readline().decode('ascii','replace').strip()
                f.seek(max(0,p.stat().st_size-4096));tail=f.read().decode('ascii','replace').splitlines()
            rec.update(header=header,first_timestamp=first.split(',')[0],last_timestamp=tail[-1].split(',')[0])
        records.append(rec)
    return dict(files=records,raw_location_parameter='--sepem',downloaded_now=False,
                observed_gap_mask=None,scope='local presence, file edges and accepted reference hashes; no new event calculation')


def accepted_windows():
    path=ROOT/'experiments/t67-goes-growth/outputs/source_manifest.json'
    m=json.loads(path.read_text('utf-8'));groups={}
    for f in m['files']:
        key=f"g{f['satellite']}_{f['cadence_s']}s"
        groups.setdefault(key,[]).append(f)
    return dict(manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        event_windows=len(m['events']),files=len(m['files']),
        groups={k:dict(files=len(fs),first_date=min(f['date'] for f in fs),
                      last_date=max(f['date'] for f in fs)) for k,fs in sorted(groups.items())},
        scope='accepted selected-window ledger, not newly fetched full archive; local raw availability not inferred')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--sepem',type=Path,required=True)
    args=parser.parse_args()
    if args.cache.resolve().is_relative_to(ROOT.resolve()):raise ValueError('raw cache must be outside repository')
    args.cache.mkdir(parents=True,exist_ok=True)
    start=datetime.now(timezone.utc).isoformat()
    with ThreadPoolExecutor(max_workers=4) as pool:
        remote=list(pool.map(lambda x:fetch(x,args.cache),URLS.items()))
    result=dict(snapshot_started_utc=start,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote=remote,sepem=local_sepem(args.sepem),t113_selected_windows=accepted_windows(),
        continuous_homogeneous_1974_to_snapshot=False,mission_quantile_estimated=False)
    (HERE/'outputs').mkdir(exist_ok=True)
    (HERE/'outputs/access-snapshot.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(remote_ok=sum(r['status']==200 for r in remote),remote_total=len(remote),
                         snapshot_started_utc=start,local_files=len(result['sepem']['files'])),indent=2))
    for r in remote:
        print(r['id'],r['status'],len(r.get('entries',[])),r.get('entries',[])[-2:])


if __name__=='__main__':main()
