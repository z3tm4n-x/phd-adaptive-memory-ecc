#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib
P=Path(__file__).resolve().with_name("test_numerical_repair_core.py.gz.b64")
SRC=gzip.decompress(base64.b64decode(P.read_bytes()))
WANT="e3adc1d7fdb50996bff79907a93cd442f7d5723c2586d0397727067a46f58002"
GOT=hashlib.sha256(SRC).hexdigest()
if GOT!=WANT: raise SystemExit(f"integrity failure {GOT} != {WANT}")
exec(compile(SRC,str(P)+"::<decoded>","exec"),globals(),globals())
