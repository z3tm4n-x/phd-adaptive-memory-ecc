#!/usr/bin/env python3
from pathlib import Path
import base64,hashlib
root=Path(__file__).resolve().parent
parts=sorted(root.glob("level1_map.csv.gz.b64.part*"))
data=base64.b64decode("".join(p.read_text().strip() for p in parts))
sha=hashlib.sha256(data).hexdigest()
expected="ef5cf8e65c41e0aac5c1b3bcbf0eef5aa7951ee609f3092794175ab60910bd80"
assert sha==expected,(sha,expected)
out=root/"level1_map.csv.gz"
out.write_bytes(data)
print(out, len(data), sha)
