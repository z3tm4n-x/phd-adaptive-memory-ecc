"""Check frozen inputs and identities, not a Q/cost calculation or a grid replay."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def run():
    raw = (HERE / "inputs.json").read_bytes()
    c = json.loads(raw)
    for path, digest in c["source_git_blobs"].items():
        assert git_blob((ROOT / path).read_bytes()) == digest, path

    e = c["environment"]
    b, B, Fs, rho, ell = (F(e[k]) for k in ("b", "B", "Fs", "rho", "ell"))
    t = e["template"]
    T, N, width, rise = c["bank"]["mission_s"], t["count"], t["width_s"], t["rise_s"]
    assert T == N*t["cycle_s"] and width == 2*rise
    assert t["left_s"] >= 0 and t["left_s"] + width <= t["cycle_s"]
    D = e["reference_words"] * e["reference_bits"]
    assert D == e["reference_positions"]
    a0 = 2*Fs/(N*width)
    assert b+a0 < B and a0/rise < rho*ell
    alphas = list(map(F, e["alpha_axis"]))
    for alpha in alphas:
        assert 0 <= alpha <= 1
        a = (1-alpha)*a0
        R, Fr, g = B-b-a, alpha*Fs, rho*ell-a/rise
        assert R > 0 and g > 0
        assert N*width*a/2 + Fr == Fs
        Ip = b*b*T+2*b*(1-alpha)*Fs+N*width*a*a/3
        IH = N*width*(b*b+b*a+a*a/3)
        IL = (T-N*width)*b*b
        assert IH+IL == Ip
        assert N*width*(b+a)**2-IH == N*width*(b*a+2*a*a/3) >= 0
    for x,y in zip(alphas, alphas[1:]):
        ax,ay=(1-x)*a0,(1-y)*a0
        assert (B-b-ay)-(B-b-ax) == (y-x)*a0
        assert (rho*ell-ay/rise)-(rho*ell-ax/rise) == (y-x)*a0/rise
        assert y*Fs-x*Fs == (y-x)*Fs

    old = json.loads((ROOT / "experiments/hybrid-p-r-20261026/inputs.json").read_text())
    oe = old["proposed_environment"]
    scale = F(39*old["fixed"]["words"], D)
    half = a0/2
    assert b*scale == F(oe["background"])
    assert B*scale == F(oe["total_peak"])
    assert Fs*scale == F(oe["total_solar_mass"])
    assert half*scale == F(oe["p"]["amplitude_above_background"])
    assert (B-b-half)*scale == F(oe["residual"]["cap_R"])
    assert Fs*scale/2 == F(oe["residual"]["mass_F_r"])
    assert (rho*ell-half/rise)*scale == F(oe["residual"]["growth_g"])

    probe = c["first_probe"]
    assert probe["words"]*4 == probe["useful_bytes"] == 4194304
    assert F(probe["alpha"]) == F(1,10) and F(probe["epsilon"]) == F(1,1000)
    resource = json.loads((HERE / c["service"]["resource_file"]).read_text())
    rraw = (HERE / c["service"]["resource_file"]).read_bytes().replace(b"\r\n",b"\n")
    assert hashlib.sha256(rraw).hexdigest() == c["service"]["resource_SHA256_LF"]
    assert any(row["words"] == probe["words"] for row in resource["rows"])
    assert all(w*4 == n for w,n in zip(c["bank"]["words_axis"], c["bank"]["useful_bytes_axis"]))

    # New hold rounding: the lower physical duration must cover the required bound.
    s = c["service"]; ns = F(1,10**9)
    xm,xp,J,q = F(s["xi_minus"]),F(s["xi_plus"]),F(s["J_ns"])*ns,s["timer_quantum_ticks"]
    dE = 124*xp*ns+3*J
    for W in c["bank"]["words_axis"]:
        PH = 196*W*xp*ns+J
        ticks = q*math.ceil((PH+dE+J)/(q*xm*ns))
        Hlo,Hhi = ticks*xm*ns-J,ticks*xp*ns+J
        assert Hlo >= PH+dE and Hhi >= Hlo
        assert (ticks-q)*xm*ns-J < PH+dE

    known0 = b*b*T+2*b*Fs+N*width*a0*a0/3
    old_upper = b*b*T+(B+b)*Fs
    assert known0 < old_upper
    print("Pinned sources:", len(c["source_git_blobs"]))
    print("Normalization, nesting identities, alpha=.5 equivalence and hold rounding: OK")
    print("First probe: W=1048576, alpha=1/10, epsilon=1/1000")
    print("Ip2(alpha=0), exact reference units:", known0)
    print("Old broad window upper, exact reference units:", old_upper)
    print("inputs SHA256:", hashlib.sha256(raw).hexdigest())
    print("No Q/cost cells, old proofs, simulations or resource replay executed.")

if __name__ == "__main__":
    run()
