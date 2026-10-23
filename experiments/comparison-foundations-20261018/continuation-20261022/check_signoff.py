"""Only the changed timing composition and Patent empty-history semantics."""
from fractions import Fraction as F
from hashlib import sha1
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
def pin(path, expected):
    raw = (ROOT / path).read_bytes()
    assert sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == expected
    return raw

data = json.loads(pin("experiments/t186-method-comparison/ev30-service/service-input.json",
                      "d82bd52716f91ed1b0fd429d56e819373bf61010"))
path = "experiments/t186-method-comparison/stage2/policies.py"
pin(path, "2f0f94c39c9200337c267085b6262493e62ae800")
spec = importlib.util.spec_from_file_location("frozen_policies", ROOT / path)
policies = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policies)
for w in (30, 60, 120):
    p = policies.Patent(window_s=w)
    assert p.timer == w * policies.NS
    assert p.mode(w * policies.NS - 1) == 1
    p.wake(w * policies.NS)
    assert p.k == 27 and p.timer is None
    assert p.mode(2 * w * policies.NS) == 27

c = data["controller_budget_ns"]
read = 3*data["cycle_ns"] + data["read_release_ns"] + data["decode_ns"] + c
write = read + data["encode_ns"] + 3*data["cycle_ns"] + data["write_release_ns"]
upper = lambda x: x*F(data["clock_upper"])+F(data["endpoint_span_ns"])
wr, rd = upper(write), upper(read)
local = F(4, 5)*(data["transaction_aperture_ns"]*F(data["clock_lower"])-F(data["endpoint_span_ns"]))
assert wr == F("576.50576") and rd == F("320.5032")
assert 400 + wr == F("976.50576")
assert 400 + wr + 420 == F("1396.50576") < 2400 < 3000 < 500000
assert 400 + rd + 420 == F("1140.5032")
assert wr < local and local-wr == F("37.488096")
print(json.dumps({"timing_composition": "PASS", "patent_empty_history_30_60_120s": "PASS",
                  "new_Q_or_hardware_measurement": False}))
