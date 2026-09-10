#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib
P=Path(__file__).resolve().with_name("numerical_repair_core.py.gz.b64")
SRC=gzip.decompress(base64.b64decode(P.read_bytes()))
WANT="1f433025a4b58151ef68d3e24dbaaf77dd46169c83c29565fe227cf6e08b0e23"
GOT=hashlib.sha256(SRC).hexdigest()
if GOT!=WANT: raise SystemExit(f"integrity failure {GOT} != {WANT}")
exec(compile(SRC,str(P)+"::<decoded>","exec"),globals(),globals())
