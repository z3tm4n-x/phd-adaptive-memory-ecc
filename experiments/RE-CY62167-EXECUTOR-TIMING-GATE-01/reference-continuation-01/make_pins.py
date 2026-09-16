"""Rebuild source-to-pin table from the hashed primary PDF and package ZIP."""
import hashlib, json, re, zipfile
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).resolve().parent
DOCS = ROOT.parents[3] / "tmp/pdfs/cy62167-reference"
def build():
    manifest = json.loads((ROOT/"source_manifest.json").read_text())
    for item in manifest["primary_documents"]:
        assert hashlib.sha256((DOCS/item["name"]).read_bytes()).hexdigest() == item["sha256"]
    archive = (DOCS/"a7all.zip").read_bytes()
    assert hashlib.sha256(archive).hexdigest() == "576e04c5eea02d4d139a475338cfa4be600e7c4e5a983ba792d799849880d53b"
    with zipfile.ZipFile(DOCS/"a7all.zip") as z:
        raw = z.read("a7all/xc7a200tfbg676pkg.txt")
    package = {}
    for line in raw.decode().splitlines():
        v=line.split()
        if len(v)==8 and v[6]=="HR":
            package[v[0]]={"function":v[1], "bank":int(v[3]), "io_type":v[6]}
    nets={}
    with pdfplumber.open(DOCS/"ug952.pdf") as doc:
        for page in range(58,62):
            for pin,net,ball in re.findall(r"([A-Z][0-9]+) (FMC1_HPC_[A-Z0-9_]+) LVCMOS25 ([A-Z]+[0-9]+)",doc.pages[page].extract_text()):
                nets[net]={"j30":pin,"ball":ball,"ug952_page":page+1,**package[ball]}
    rows=[]
    io_pins=[29,31,33,35,38,40,42,44,30,32,34,36,39,41,43,45]
    addr_pins=[25,24,23,22,21,20,19,18,8,7,6,5,4,3,2,1,48,17,16]
    def add(port,short,targets):
        name="FMC1_HPC_"+short
        rows.append({"port":port,"net":name,**nets[name],"sram_pins":targets,"rail":"VCCO_VADJ 2.375..2.625 V","standard":"LVCMOS25"})
    for i in range(48):
        pair=i//2
        suffix="_CC" if pair in (0,1,17,18) else ""
        add(f"dq[{i}]",f"LA{pair:02}{suffix}_{'PN'[i%2]}",[f"M{i//16}.{io_pins[i%16]}"])
    for i in range(19):
        add(f"addr[{i}]",f"LA{24+i//2:02}_{'PN'[i%2]}",[f"M{m}.{addr_pins[i]}" for m in range(3)])
    for port,net,pin in [("ce_n","LA33_N",26),("oe_n","HA00_CC_P",28),("we_n","HA00_CC_N",11)]:
        add(port,net,[f"M{m}.{pin}" for m in range(3)])
    for i,net in enumerate(["HA01_CC_P","HA01_CC_N","HA02_P"]):
        add(f"err[{i}]",net,[f"M{i}.13"])
    assert len(rows)==73
    for key in ("port","net","ball","j30"):
        assert len({r[key] for r in rows})==73
    assert {r["bank"] for r in rows}=={12,15,16}
    assert all(r["io_type"]=="HR" for r in rows)
    table={"package_member_sha256":hashlib.sha256(raw).hexdigest(),"signals":rows,
      "straps_each_sram":{"A19_pin9":"GND","BYTE_pin47":"VADJ","CE2_pin12":"VADJ","BHE_pin14":"GND","BLE_pin15":"GND","VCC_pin37":"VADJ","VSS_pins27_46":"GND","NC_pin10":"unconnected"},
      "readiness":{"PG_M2C":"J30.F1 / FPGA.N17","PRSNT_M2C_B":"J30.H2 / FPGA.N16","CTRL2_PWRGOOD":"J30.D1 / FPGA.P15","note":"board sequencer plus separately qualified voltage/clock; not equivalent to ready"},
      "clock":{"source":"UG952 p26 U51","positive":"R3","negative":"P3","bank":34,"note":"dedicated differential board clock; wrapper and clock-input constraints remain integration obligations"}}
    (ROOT/"pinmap.json").write_text(json.dumps(table,indent=2)+"\n",encoding="utf-8",newline="\n")
    lines=["# Generated physical SRAM ports only; NOT a complete board bitstream constraint set.",
      "# Apply to a wrapper exposing dq/addr/ce_n/oe_n/we_n/err. Witness control ports are internal.",
      "# No false paths or unproved multicycle exceptions. Complete clock, min/max I/O and hold STA required."]
    for r in rows:
        lines += [f"set_property PACKAGE_PIN {r['ball']} [get_ports {{{r['port']}}}]",
                  f"set_property IOSTANDARD LVCMOS25 [get_ports {{{r['port']}}}]",
                  f"set_property PULLTYPE {{}} [get_ports {{{r['port']}}}]"]
    lines+=["# Drive/slew/loading must be selected and validated against TIMING.md; intentionally not invented."]
    (ROOT/"reference_pins.xdc").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
    print("73 unique signal nets; all mapped to VADJ HR banks 12/15/16.")
if __name__=="__main__": build()
