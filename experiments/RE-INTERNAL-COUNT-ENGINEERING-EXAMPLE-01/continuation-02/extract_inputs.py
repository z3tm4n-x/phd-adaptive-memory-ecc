"""Read-only reconstruction of the supplied 60-test neutron archive."""
from pathlib import Path
import argparse, collections, hashlib, io, json, re, zipfile
import numpy as np
import openpyxl

ROOT = Path(__file__).resolve().parent
PREFIX = 'OpenData/2025-02-14MeV-NEUTRONS/'
RAW = PREFIX + '01-Original_DATA/01-STATIC-3.3V/'
TREATED = PREFIX + '02-TREATED_DATA/01-STATIC-3.3V/'
EXPECTED = {1:35651,2:7195,3:1089,4:288,5:74,6:34,7:7,8:12,9:4,10:1,11:1,12:3,14:3,16:1,23:1}

def components(points, anomalies, join_native=False):
    parent = {p:p for p in points}
    def root(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]; p = parent[p]
        return p
    for p in points:
        neighbours = [p ^ a for a in anomalies]
        if join_native:
            neighbours += [(p//16)*16+b for b in range(16)]
        for q in neighbours:
            if q in parent:
                parent[root(q)] = root(p)
    groups = collections.defaultdict(list)
    for p in points: groups[root(p)].append(p)
    return sorted(tuple(sorted(g)) for g in groups.values())

def main(archive):
    data = Path(archive).read_bytes()
    assert hashlib.sha256(data).hexdigest() == '7c4e05968a8e0adc9733a3ba706a8ed2f751e53162b80b9746c1b8c4ccdb2e88'
    z = zipfile.ZipFile(io.BytesIO(data)); names=z.namelist()
    script = z.read(TREATED+'Global_Analysis.jl').decode('utf-8-sig')
    # Read the explicit source list, not a hand-copied replacement.
    match = re.search(r'Anomalies\s*=\s*\[([^\]]+)\]',script,re.S)
    anomalies = sorted(set(int(s,16) for s in re.findall(r'0x[0-9a-fA-F]+',match[1])))
    assert len(anomalies)==35 and all(a%16==0 for a in anomalies)
    workbook_name=RAW+'Study_3V3_0x5555.xlsx'
    wb=openpyxl.load_workbook(io.BytesIO(z.read(workbook_name)),data_only=True,read_only=True)
    metadata={}
    for row in wb['events'].iter_rows(values_only=True):
        if isinstance(row[0],str) and row[0].startswith('out__'):
            metadata[re.search(r'out__\d+',row[0])[0]] = dict(duration_s=float(row[3]),neutrons=float(row[4]),factor=float(row[5]),fluence_cm2=float(row[6]),voltage_mV=float(row[7]))
    templates=[]; merged=[]; tests=[]; members={}; hist=collections.Counter()
    for name in sorted(n for n in names if n.startswith(RAW) and n.endswith('.dat')):
        text=z.read(name).decode('utf-8-sig'); points=[]; rows=double=0
        for line in text.splitlines():
            if not line.startswith('0x'): continue
            address,read,expected=[int(v,16) for v in line.split(',')[:3]]
            mask=read^expected
            assert address < 2**21 and mask and mask < 2**16
            assert address!=0, 'artifact rule needs explicit disposition'
            bits=[b for b in range(16) if mask>>b&1]
            double += len(bits)==2; rows+=1
            points.extend(16*address+b for b in bits)
        assert len(points)==len(set(points))
        groups=components(points,anomalies)
        alternate=components(points,anomalies,True)
        stem=Path(name).stem
        logname=next(n for n in names if n.startswith(TREATED) and n.endswith(stem+'_global.log'))
        log=z.read(logname).decode('utf-8-sig')
        # Independent supplied output: all lines starting with hexadecimal addresses.
        loggroups=sorted(tuple(sorted(int(v,16) for v in re.findall(r'0x[0-9a-fA-F]+',line))) for line in log.splitlines() if line.lstrip().startswith('0x'))
        assert groups==loggroups, (stem,len(groups),len(loggroups))
        meta=metadata[stem]
        assert abs(meta['neutrons']/meta['factor']/meta['fluence_cm2']-1)<1e-12
        tests.append(dict(id=stem,**meta,raw_words=rows,bits=len(points),groups=len(groups),double_words=double,merged_groups=len(alternate),template_start=len(templates),template_end=len(templates)+len(groups)))
        templates.extend(groups); merged.extend(alternate); hist.update(map(len,groups))
        for member in (name,logname): members[member]=hashlib.sha256(z.read(member)).hexdigest()
    assert len(tests)==60 and dict(hist)==EXPECTED
    assert sum(t['bits'] for t in tests)==55353
    assert sum(t['raw_words'] for t in tests)==55344
    assert sum(t['double_words'] for t in tests)==9
    def flatten(groups):
        return np.array([p for g in groups for p in g],np.int32),np.r_[0,np.cumsum([len(g) for g in groups])].astype(np.int32)
    points,offsets=flatten(templates); mp,mo=flatten(merged)
    (ROOT/'inputs').mkdir(exist_ok=True)
    np.savez_compressed(ROOT/'inputs/templates.npz',points=points,offsets=offsets,merged_points=mp,merged_offsets=mo)
    for member in (workbook_name,TREATED+'Global_Analysis.jl'):
        members[member]=hashlib.sha256(z.read(member)).hexdigest()
    result=dict(archive_sha256=hashlib.sha256(data).hexdigest(),archive_md5=hashlib.md5(data).hexdigest(),archive_bytes=len(data),source='https://doi.org/10.5281/zenodo.17500462',anomalies=anomalies,tests=tests,histogram=dict(sorted(hist.items())),total_duration_s=sum(t['duration_s'] for t in tests),total_fluence_cm2=sum(t['fluence_cm2'] for t in tests),raw_bits=sum(t['bits'] for t in tests),groups=len(templates),merged_groups=len(merged),all_60_supplied_group_logs_equal=True,member_sha256=members)
    (ROOT/'inputs/manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('tests','member_sha256','anomalies')},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');main(p.parse_args().archive)
