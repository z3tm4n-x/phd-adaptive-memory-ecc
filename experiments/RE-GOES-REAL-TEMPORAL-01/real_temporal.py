#!/usr/bin/env python3
"""Integrity-checking loader for the deterministic compressed core source."""
from pathlib import Path
import base64, gzip, hashlib
CORE_SHA256 = "6ffb2bbedd971b01201109aab94c3616a7ec6b39e3bc8549864d42716fcb2d79"
_core = Path(__file__).with_name("real_temporal_core.py.gz.b64")
_src = gzip.decompress(base64.b64decode(_core.read_bytes()))
_got = hashlib.sha256(_src).hexdigest()
if _got != CORE_SHA256:
    raise RuntimeError(f"core source SHA-256 mismatch: {_got} != {CORE_SHA256}")
exec(compile(_src, str(Path(__file__).with_name("real_temporal_core.py")), "exec"), globals(), globals())
