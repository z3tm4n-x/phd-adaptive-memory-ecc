"""Replay the accepted pin traces, all route reports and exact essential masks."""
import argparse
from collections import Counter
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import re
import tempfile
import zipfile

from check_route import check, require

HERE = Path(__file__).resolve().parent
MODES = ("F0", "F1", "A0", "A1")


def mask(path):
    digest = hashlib.sha256()
    ones = words = 0
    with path.open("rb") as source:
        for header in range(8):
            line = source.readline()
            if header == 7:
                declared = int(re.fullmatch(rb"Bits:\s*(\d+)\s*", line)[1])
        for line in source:
            word = line.strip()
            require(len(word) == 32 and not word.strip(b"01"), "invalid EBD word")
            digest.update(word)
            ones += word.count(b"1")
            words += 1
    require(32 * words == declared and 0 < ones < declared, "mask length or population")
    return {"payload_bits": declared, "marked_bits": ones, "words32": words,
            "ascii_payload_sha256": digest.hexdigest()}


def physical_inventory(path, protected):
    entries = [line.split("\t") for line in path.read_text().splitlines()[1:]]
    types = Counter(e[1] for e in entries)
    copies = 3 if protected else 1
    captures = [e for e in entries if re.fullmatch(r"core/lane\[\d+\]\.u/(sampled_err_reg|repair_image_reg\[\d+\])", e[0])]
    require(len(captures) == 17 * copies and len({(e[2], e[3]) for e in captures}) == len(captures),
            "merged or missing capture")
    if protected:
        require(types["ICAPE2"] == types["FRAME_ECCE2"] == 1 and types["RAMB18E1"] == 3, "SEM placement")
    else:
        require(types["ICAPE2"] == types["FRAME_ECCE2"] == 0, "unexpected SEM")
    return {"capture_sites_and_bels": captures, "primitives_in_inventory": dict(sorted(types.items())),
            "placed_FF": sum(v for k, v in types.items() if k.startswith("FD"))}


def observations(path, mode):
    rows = []
    for line in path.read_text().splitlines():
        words = line.split()
        require(words and words[0] in ("FULL", "BOUNDARY", "RECOVERY"), "unknown observation")
        pairs = dict(w.split("=", 1) for w in words[1:])
        rows.append({"test": words[0], **{k: int(v) if re.fullmatch(r"-?\d+", v) else v for k, v in pairs.items()}})
    a, p = mode.startswith("A"), int(mode[-1])
    full = {r["case"]: r for r in rows if r["test"] == "FULL"}
    require(set(full) == {"clean", "last", "edges", "all", "one_err", "one_data", "common_err"}, "missing pin sentinel")
    for key, row in full.items():
        require(row["mode"] == int(a) and row["protected"] == p and row["reads"] == 131072,
                "incorrect configuration/size")
        writes = {"clean": 0, "last": 1, "edges": 6, "all": 131072, "one_err": p,
                  "one_data": 1, "common_err": 0}[key]
        require(row["writes"] == writes and row["owner_ns"] == (row["reads"]+writes)*100,
                "port or write accounting")
        require(row["wrong_write"] == (key == "one_data" and not p), "write-data coverage")
        require(row["next_ns"] == (86429000 if not a else
                91750400 if key == "common_err" or key == "one_err" and not p else 45875200),
                "next start on pins")
    require(full["last"]["partial_ns"] == 13107230 and full["last"]["sample_last_ns"] == 45874620
            and full["last"]["we_last_ns"] == 45874720 and full["last"]["publication_ns"] == 45874760,
            "last-word transaction and horizon")
    require(full["all"]["peak_1ms_ns"] == 571560, "1 ms saturated peak")
    if a:
        cuts = {(r["level"], r["defect"]): r for r in rows if r["test"] == "BOUNDARY"}
        require(len(cuts) == 12 and len(rows) == 22, "boundary coverage")
        for level in range(1,8):
            require(cuts[level,0]["actual_round"] == 2**level, "promotion")
        require([cuts[1,i]["actual_round"] for i in range(1,6)] == [2,1,1,2 if p else 8,2], "deadline/command sentinel")
        recovery = [r for r in rows if r["test"] == "RECOVERY"]
        require([r["first_2L_epoch"] for r in recovery] == [2560,2688,-1], "SEM history recovery")
    else:
        require(len(rows) == 7 and all(r["install_tick"] == -1 for r in rows), "fixed decision logic")
    return rows


def summarize(source):
    result = {}
    for mode in MODES:
        location = source/mode
        protected = mode.endswith("1")
        sta = check(location)
        require(sta["pass"] and not check(location, D(100))["pass"], "STA or access-time sentinel")
        inv = physical_inventory(location/"cells.tsv", protected)
        usage = sta["resources"]
        # A port FF packed in the I/O block is still susceptible to a state upset.
        require(inv["placed_FF"] >= usage["Slice Registers"], "FF inventory omits fabric FFs")
        pwr = (location/"power.rpt").read_text(encoding="utf-8")
        def field(label):
            return re.search(r"(?m)^\| "+re.escape(label)+r"\s*\|\s*([^|]+)\|", pwr)[1].strip()
        power = {name: field(name) for name in ("Total On-Chip Power (W)", "Dynamic (W)", "Device Static (W)", "Confidence Level")}
        ebd = mask(location/"bank.ebd")
        result[mode] = {"route": sta, "placement": inv, "essential_mask": ebd, "vectorless_power": power,
                        "pin_observations": observations(location/"observations.txt", mode)}
    rule = (source/"rule.txt").read_text().strip()
    require(rule == "POLICY levels_mask=255 saturation=596 samples=47474 report_cases=15 post_install_loss=1", "threshold/history scoreboard")
    links = (source/"sem_links.txt").read_text().splitlines()
    for mode in (0,1):
        require(links[mode] == f"SEM_LINK adaptive={mode} commissioning_wait=1 correction_spans_write=1 captured=1 committed=1 first_next_address=1 fail_status=1 runtime_cold=0", "SEM board connection")
    require(len(links)==2, "unexpected SEM test set")
    return {"builds": result, "rule": rule, "sem_board_status_tests": links}


def pack(routes, simulations, output):
    # Raw text reports and actual masks are compressible. Do not ship vendor IP, checkpoints or bitstreams.
    members = {}
    reports = ["timing.rpt","route.rpt","check.rpt","drc.rpt","utilization.rpt","hierarchy.rpt","power.rpt",
               "pins.rpt","effective.xdc","cells.tsv","worst_setup.rpt","worst_hold.rpt","bank.ebd"]
    for mode in MODES:
        root = routes/mode
        for path in [root/n for n in reports]+sorted(root.glob("clocked_*.rpt")):
            members[mode+"/"+path.name] = path.read_bytes()
        if mode.endswith("1"):
            members[mode+"/sem_properties.rpt"] = (root/"sem_properties.rpt").read_bytes()
        members[mode+"/observations.txt"] = (simulations/mode/"observations.txt").read_bytes()
    members["rule.txt"] = ((simulations/"rule.txt").read_text(encoding="utf-8").splitlines()[0]+"\n").encode()
    members["sem_links.txt"] = "".join((simulations/f"sem{k}.txt").read_text(encoding="utf-8").splitlines()[0]+"\n" for k in (0,1)).encode()
    members["SHA256SUMS"] = "".join(hashlib.sha256(data).hexdigest()+"  "+name+"\n"
                                     for name,data in sorted(members.items())).encode()
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for n,data in sorted(members.items()):
            info=zipfile.ZipInfo(n)
            archive.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)


def replay(bundle):
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(bundle) as data:
        base=Path(tmp)
        names=data.namelist()
        require(len(names)==len(set(names)), "duplicate archive paths")
        for name in names:
            require(re.fullmatch(r"(?:[AF][01]/[a-zA-Z0-9_.]+|rule\.txt|sem_links\.txt|SHA256SUMS)",name), "unexpected member")
        data.extractall(base)
        declared={name:sha for sha,name in (x.split("  ",1) for x in (base/"SHA256SUMS").read_text().splitlines())}
        require(set(declared)==set(names)-{"SHA256SUMS"}, "missing file hash")
        for name,sha in declared.items():
            require(hashlib.sha256((base/name).read_bytes()).hexdigest()==sha, "hash mismatch "+name)
        return summarize(base)


if __name__ == "__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--pack",nargs=2,type=Path,metavar=("ROUTES","SIMULATIONS"))
    cli.add_argument("--bundle",type=Path,default=HERE/"results/evidence.zip")
    cli.add_argument("--results",type=Path,default=HERE/"results/digital.json")
    cli.add_argument("--write",action="store_true")
    args=cli.parse_args()
    if args.pack:
        args.bundle.parent.mkdir(parents=True,exist_ok=True)
        pack(*args.pack,args.bundle)
    result=replay(args.bundle)
    if args.write:
        args.results.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    else:
        require(result==json.loads(args.results.read_text(encoding="utf-8")), "published result differs")
    for mode,case in result["builds"].items():
        s=case["route"]
        print(mode,s["resources"],s["wns_ns"],s["whs_ns"],min(map(D,s["external_margin_ns"].values())),
              case["placement"]["placed_FF"],case["essential_mask"]["marked_bits"],case["vectorless_power"])
    print("PASS 4 implementations, 58 pin trials, 47474 policy updates and four access-time sentinels.")
