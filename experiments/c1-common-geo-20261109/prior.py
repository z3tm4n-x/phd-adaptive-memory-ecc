"""Use only the published PR419 readers and numerical inputs, from a named checkout."""
import hashlib
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
PIN = 'c944c91a2c20a207516824333e02711aaf34898f'
SUBDIR = 'experiments/c1-geo-fixed-20261109'
FILES = ('fixed.py','goes_profile.py','goes_inventory.py','sepem.py',
         'sepem.json','goes.json','goes-sources.json.gz','goes-events.json.gz','fixed.json')


def activate(checkout):
    root = Path(checkout).resolve()
    for name in FILES:
        rel = SUBDIR+'/'+name
        data = (root/rel).read_bytes()
        if not name.endswith('.gz'):
            data = data.replace(b'\r\n',b'\n')
        digest = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        expected = subprocess.check_output(['git','-C',str(root),'rev-parse',PIN+':'+rel],text=True).strip()
        if digest != expected:
            raise ValueError(f'PR419 input differs from {PIN}: {name}')
    sys.path.insert(0,str(root/SUBDIR))
    return root/SUBDIR
