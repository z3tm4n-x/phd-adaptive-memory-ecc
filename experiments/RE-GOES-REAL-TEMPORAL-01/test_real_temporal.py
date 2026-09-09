#!/usr/bin/env python3
"""Integrity-checking loader for compressed focused-test source."""
from pathlib import Path
import base64, gzip, hashlib
CORE_SHA256 = "af9580c5f81be153f547b4891af59fb46745398c8301c507e9a26b7303357a9a"
_core = Path(__file__).with_name("test_real_temporal_core.py.gz.b64")
_src = gzip.decompress(base64.b64decode(_core.read_bytes()))
_got = hashlib.sha256(_src).hexdigest()
if _got != CORE_SHA256:
    raise RuntimeError(f"test core SHA-256 mismatch: {_got} != {CORE_SHA256}")
exec(compile(_src, str(Path(__file__).with_name("test_real_temporal_core.py")), "exec"), globals(), globals())
