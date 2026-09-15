"""Identity/time utilities only; no rate or risk calculator."""
import csv, hashlib, io, json, subprocess, zipfile
from datetime import datetime, timedelta
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE='64a7a1f436b2abd6997d37d14e6ce571e3a480c8'
START=datetime.fromisoformat('2026-01-19T04:00:00+00:00')
TIMES=[START+timedelta(seconds=300*i) for i in range(288)]
GOES_SHA='7b5e2f62e8a3b235ae1956505742253bb7d7633dfaa4be6e0350e37e5d8ab581'
REF_SHA='9f8a43a00780a0853db6e4a03263eb87672065be5a93edfcc79f544c78f7593d'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def git_blob(repo,path):return subprocess.check_output(['git','-C',str(repo),'show',BASE+':'+path])

def sources():
    entries=json.loads((HERE/'recovery/source_manifest.json').read_text())
    for e in entries:
        if sha(HERE/e['package_path'])!=e['sha256']:raise ValueError('source changed: '+e['package_path'])

def archive_extract(archive,repo,dest):
    if sha(archive)!=GOES_SHA:raise ValueError('GOES archive SHA')
    manifest=json.loads(git_blob(repo,'experiments/RE-GOES19-PROTON-RATE-01/input_manifest.json'))
    wanted={r['name']:r['sha256'] for r in manifest['goes_archive']['files']}
    found={}
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if not name.endswith('.nc'):continue
            base=Path(name).name;raw=z.read(name)
            if base in found or hashlib.sha256(raw).hexdigest()!=wanted.get(base):raise ValueError('GOES member identity')
            found[base]=wanted[base];(Path(dest)/base).write_bytes(raw)
    if set(found)!=set(wanted):raise ValueError('incomplete GOES members')
    return found

def reference(repo):
    raw=git_blob(repo,'experiments/RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv')
    if hashlib.sha256(raw).hexdigest()!=REF_SHA:raise ValueError('upstream reference SHA')
    rows=[r for r in csv.DictReader(io.StringIO(raw.decode())) if TIMES[0]<=datetime.fromisoformat(r['timestamp_utc'])<START+timedelta(days=1)]
    if [datetime.fromisoformat(r['timestamp_utc']) for r in rows]!=TIMES:raise ValueError('upstream reference time coverage')
    if any(r['east_valid']!='1' or r['west_valid']!='1' for r in rows):raise ValueError('incomplete upstream reference')
    return rows

def transport():
    d=HERE/'recovery/outputs';q=json.loads((d/'transport_qualification.json').read_text())
    if not q['structural_numerical_gate_pass'] or sha(d/'radar_transport.npz')!=q['hashes']['radar_transport.npz']:raise ValueError('unqualified transport')
    return d/'radar_transport.npz'
