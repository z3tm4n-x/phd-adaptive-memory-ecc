"""Apply the accepted native ledger and parent normalization to the author example."""
from fractions import Fraction as F
from math import ceil
from pathlib import Path
from runpy import run_path

EXP = Path(__file__).resolve().parents[1]
ledger = run_path(str(EXP / "t196-archive-same-map-20261110/calculate.py"))
read = ledger["read_json"]
ost = read(EXP / "t186-ost-geo-3g/result.json")
source = read(EXP / "c1-geo-fixed-20261109/sepem.json")["maxima"]["S2"]
assert source["start_utc"] == "1996-12-16T07:20:00Z"
k = ost["archive"]["excess_multiplier"]
intercept = ost["ost_tabulated"]["b"]-k*ost["archive"]["old_limits"]["b"]
decade_cap = ceil(k*source["S1"]+intercept*ledger["T"])
assert decade_cap == 164215
price = ledger["comparison"](decade_cap,F("0.000762790"))["endpoints"]
assert [row["ladder_bus_s_upper_at_I0"] for row in price] == ["843839.613","1018620.684"]
for row in price:
    w=row["words"]
    parents = F(w*187464,2*524288)
    allowed_fraction = F(1,10000)/parents
    print(w, "E[parents] <=", float(parents), "illustrative direct fraction <=",float(allowed_fraction),
          "decade bus upper (s)", row["ladder_bus_s_upper_at_I0"])
broad = read(EXP / "t196-native-err-20261110/result.json")["131072"]["quarter_eligible"]
assert broad["fixed"]["necessary_bus_s_if_nonempty"] == "7825256.934"
assert broad["staircase"]["price"]["bus_read_repair_s_at_I0"] == "1061779.678"
assert F(44529,524288)*F("0.9814")*F("0.022938") < F("0.002")
assert F("1.90e-14")*ledger["T"] <= ledger["DELTA"]
print("Controller limit (1/h):", float(ledger["DELTA"]*3600/ledger["T"]))
