"""Inputs from the frozen C1 archive and common-class packages."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
COMMON_PIN='c0176b4837b5310378fb4218f2d549aeb4c991e9'
COMMON_SUB='experiments/c1-common-geo-20261109'
DT=300
T=315576000
WIDTH=T//DT


def setup(common,previous):
    root=Path(common).resolve()
    files=('prior.py','coverage.py','cadence.py','minute_sources.py','growth_check.py',
           'coverage.json','cadence.json','growth.json','six.json','fixed_six.py','verify.py')
    for name in files:
        rel=COMMON_SUB+'/'+name
        expected=subprocess.check_output(['git','-C',str(root),'rev-parse',COMMON_PIN+':'+rel],text=True).strip()
        data=(root/rel).read_bytes().replace(b'\r\n',b'\n')
        actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual!=expected:raise ValueError('Different PR423 input '+rel)
    sys.path.insert(0,str(root/COMMON_SUB))
    import prior
    return root/COMMON_SUB,prior.activate(previous)


def save(name,value,check):
    path=HERE/name
    text=json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    if check:
        if path.read_text(encoding='utf-8')!=text:raise SystemExit('Mismatch: '+name)
    else:path.write_text(text,encoding='utf-8',newline='\n')
