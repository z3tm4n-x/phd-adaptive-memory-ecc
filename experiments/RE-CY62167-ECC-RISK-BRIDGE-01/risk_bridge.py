# Auto-loader for exact source payload; see risk_bridge.py.zlib.b85.
from __future__ import annotations
import base64,zlib
from pathlib import Path
_payload=Path(__file__).with_name("risk_bridge.py.zlib.b85")
_code=zlib.decompress(base64.b85decode(_payload.read_bytes()))
exec(compile(_code,str(Path(__file__).with_name("risk_bridge.py.decoded")),"exec"),globals(),globals())
