"""Independent acceptance checks. No imports from author numeric solvers."""
from fractions import Fraction as F
from pathlib import Path
import hashlib, json, importlib.util, sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[3]
def read(path):
    return json.loads((ROOT/path).read_text())
manifest=[
  {
    "path": "experiments/t186-method-comparison/code-strength/common-input.json",
    "sha": "31fe2d05282a283f2fa8da67147a8ad1baac1276"
  },
  {
    "path": "experiments/t186-method-comparison/ev30-service/service-input.json",
    "sha": "d82bd52716f91ed1b0fd429d56e819373bf61010"
  },
  {
    "path": "experiments/t186-method-comparison/ev30-service/outputs/result.json",
    "sha": "1b3ce3b147b10b312f358d36961f5f83bc190f99"
  },
  {
    "path": "experiments/t186-method-comparison/app-only/outputs/result.json",
    "sha": "0ea731ec1b64c43bf363c3f1c242ca81595cdfd5"
  },
  {
    "path": "experiments/regime-map-methodology-20261019/revision-evidence-20261022/thresholds.json",
    "sha": "29e77fef9b7a9564bd362b0c8c279d66733e2959"
  },
  {
    "path": "experiments/t186-method-comparison/stage2/policies.py",
    "sha": "2f0f94c39c9200337c267085b6262493e62ae800"
  }
]
for item in manifest:
    data=(ROOT/item["path"]).read_bytes()
    actual=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    assert actual==item["sha"], (item["path"], actual)

e="experiments/t186-method-comparison/"
s=read(e+"ev30-service/outputs/result.json")
cfg=read(e+"code-strength/common-input.json")
T=315576000
W=131072
period=1000020
counts={k:((T*10**9-1-a)//period+1) for k,a in [("read",100000),("write",600000)]}
assert counts==s["workload"]["counts"]
up=F(100001,100000);lo=F(99999,100000);J=F(1,2)
rd=F(3*64+32+32+64)*up+J
wr=F(3*64+32+32+32+3*64+32+64)*up+J
assert rd==F(s["transactions"]["full_upper_ns"]["read"])
assert wr==F(s["transactions"]["full_upper_ns"]["write"])
response=400+wr+420
release=400+wr
assert response==F(s["service"]["max_response_upper_ns"])==F("1396.50576")
assert release==F(s["service"]["arrival_to_release_upper_ns"])==F("976.50576")
assert response<2400<3000<500000
mean=(counts["read"]*rd+counts["write"]*wr+W*rd)/(T*10**9)
assert mean==F(s["price"]["mean_bus_fraction_upper_at_controller_budget"])
peak=(rd+2*wr)/10**6
assert peak==F(s["peak"]["fraction_upper"])
assert (10**6+3000)//500000+1==3
assert (10**6+3000)//period+1==2
init=W*rd
assert init==F(s["initialization"]["active_bus_prefix_upper_ns"])
joint=(F(4,5)*(768*lo-J)-J)/up-(6*64+32+32)
assert joint==F(s["transactions"]["joint_decode_encode_controller_limit_ns"])
assert joint-64==F(s["transactions"]["total_controller_limit_at_fixed_codec_ns"])
pulse=40*lo-J-35
capture=56*lo-J-45
assert pulse==F(s["AC"]["maximum_admissible_ns"]["WE_pulse_shrink_ns"])
assert capture==F(s["AC"]["maximum_admissible_ns"]["read_address_CE_BE_board_capture_ns"])

m="experiments/regime-map-methodology-20261019/revision-evidence-20261022/"
thresholds=read(m+"thresholds.json")
old=read(e+"app-only/outputs/result.json")
delta=F(old["risk"]["terms"]["lifetime_exceptions"])
component=F(old["Q_upper"])-delta
eps=F(1,1000)
for row in thresholds["thresholds"]:
    target=F(row["target_over_epsilon"])*eps
    beta=F(row["extra_beta"])
    lower=F(row["c_limit_lower"]);upper=F(row["c_limit_upper"])
    assert upper-lower==F(1,10**9)
    assert delta+beta+component*lower**3<=target<delta+beta+component*upper**3
assert delta+F(1,10000)+component*4**3<eps
assert delta+F(1,10000)+component*4**3>eps/2

# Verify the author's preparation against the pinned policy, not its simulator.
spec=importlib.util.spec_from_file_location("policies", ROOT/e/"stage2/policies.py")
policies=importlib.util.module_from_spec(spec);spec.loader.exec_module(policies)
p=policies.Patent(window_s=60)
assert p.mode(0)==1 and p.timer==60*10**9
assert p.mode(60*10**9-1)==1
p.wake(60*10**9)
assert p.mode(60*10**9)==27 and p.timer is None
assert p.mode(120*10**9)==27
print(json.dumps({
 "verified_git_blobs":len(manifest),
 "response_ns":str(response),"arrival_to_release_ns":str(release),
 "mean_percent":float(100*mean),"peak_percent":float(100*peak),
 "active_prefix_ms":float(init/10**6),"joint_codec_controller_ns":str(joint),
 "six_thresholds_bracketed":True,
 "patent_empty_history":"FAST before w; LOW at w and thereafter while no observations",
 "scope":"independent arithmetic plus pinned policy semantics; no physical Q or hardware validation"
},ensure_ascii=False,indent=2))
