"""Read-only loading of the accepted RES-003 implementation, with blob checks."""
from pathlib import Path
import hashlib
import sys

UPSTREAM=Path(__file__).resolve().parent.parent/'RE-INTERNAL-COUNT-CONTROL-01'
EXPECTED={'core.py':'7873e28e126ea02e03fc6c429ac0b4275e243cfb',
          'simulate.py':'ee55c6bf57b034b0efc0b41936a549d6a14b53dd',
          'config.json':'5ca1b8cda0a19315684c34423cadafa2cf544e6e'}

def verify():
    result={}
    for name,expected in EXPECTED.items():
        data=(UPSTREAM/name).read_bytes()
        actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual!=expected: raise RuntimeError(f'Upstream {name} does not match the accepted base')
        result[name]=actual
    return result

verify()
sys.path.insert(0,str(UPSTREAM))
import core as known_core
import simulate as known_sim
