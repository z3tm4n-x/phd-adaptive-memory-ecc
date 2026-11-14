"""Independent recomputation from pin-level RTL observations, standard Python."""
import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
from pathlib import Path
import io
import json
import zipfile

HERE = Path(__file__).resolve().parent
MODES = ("F_board","A_board","F_core","A_core")
N = 131072
L = 4587520
FIXED = 8642900
PERIOD = 100100
FILES = ({f"{m}_{p}.csv" for m in MODES for p in (0,1)} |
         {"F_core_strict.txt","A_core_strict.txt","edges_0.txt","edges_1.txt"})
COLUMNS = "case adaptive plane context discipline phase_or_index source_edge arrival eligible grant valid request_address pad_address expected_data valid_data".split()


class CheckError(ValueError):
    pass


def check(condition, message):
    if not condition:
        raise CheckError(message)


def convert(fields):
    row = dict(zip(COLUMNS,fields,strict=True))
    return {k:(v if k in ("case","context","discipline") else int(v)) for k,v in row.items()}


def pin(address):
    # Swap two bits only when their values differ.
    toggle = ((address>>5) ^ (address>>16)) & 1
    return address ^ ((1<<5 | 1<<16) if toggle else 0)


def data(address,plane):
    if plane==0:
        return (0x5a37+173*(address&0xffff)) % 65536
    return (address&0xffff) ^ (0xc639 if address>=65536 else 0x39c6)


def check_results(raw):
    check(set(raw)==FILES,"Incomplete set of original logs")
    check(len({(data(i,0),data(i,1)) for i in range(N)})==N,"Aliasing two-plane oracle")
    same={}
    tests=Counter()
    summary={}
    for adaptive in (0,1):
        expected=[]
        for grant,pad,word in ((102,"00021","3c69"),(242,"10020","a55a"),
                               (522,"00021","3c69"),(662,"00021","3c69")):
            expected.extend([f"GRANT A={adaptive} tick={grant} request=10001 pad={pad}",
                             f"VALID A={adaptive} tick={grant+10} value={word}"])
        expected.append(f"PASS A={adaptive} grants=4 valid=4 wrong_when_late=1 deferred_correct=1")
        check(raw[f"edges_{adaptive}.txt"].decode().splitlines()==expected,"Independent boundary run")
    for m in MODES:
        mode=m[0]
        b=m.endswith("board")
        if not b:
            failure=raw[m+"_strict.txt"].decode().strip()
            check(failure=="strict ordinary request returned another address tick=532 phase=112","Missing falsifier")
        for p in (0,1):
            ranges=defaultdict(list); rows=[]; evidence=[]; signals=[]; ready=[]
            parse=csv.reader(io.StringIO(raw[f"{m}_{p}.csv"].decode("ascii")))
            controls=[]
            for vals in parse:
                if vals[0]=="CHECK":
                    controls.append(vals[1:]); continue
                if vals[0]=="SIGNAL":
                    signals.append(list(map(int,vals[1:])));continue
                if vals[0]=="READY":
                    ready.append(list(map(int,vals[1:])));continue
                x=convert(vals)
                check(x["plane"]==p and x["adaptive"]==int(mode=="A"),"Mode tag")
                kind=x["case"]; s=x["context"]; discipline=x["discipline"]; h=x["phase_or_index"]
                eligible=x["eligible"]; grant=x["grant"];valid=x["valid"];arrival=x["arrival"]
                want=x["request_address"];actual=x["pad_address"]
                check(valid-grant==10 and x["valid_data"]==data(actual,p) and x["expected_data"]==data(pin(want),p),"Response data or deadline")
                wrong=kind=="EXT" and discipline=="hold" and h==102
                check(actual==pin(0x10020 if wrong else want),"Incorrect physical address")
                check((x["expected_data"]!=x["valid_data"])==wrong,"Silent wrong payload")
                if kind=="EXT":
                    check(not b and arrival%140==h and eligible==arrival+(discipline=="gate" and h==102),"Request phase")
                    first=next(g for g in range(eligible,eligible+140) if g%140==102)
                    check(grant==first,"Calendar does not match")
                    ranges[s,discipline].append((h,grant-arrival,valid-arrival,wrong))
                    if wrong: evidence.append([s,arrival,grant,valid,want,actual,x["expected_data"],x["valid_data"]])
                elif kind=="BOARD":
                    check(b and h>=0 and s in ("cold_early","cold_late","cross"),"Unexpected board trace")
                    expected=102+h*PERIOD
                    check(grant==expected and want==h and actual==pin(h),"Built-in stream and order")
                    if h==0:
                        check((arrival,eligible,x["source_edge"])==(0,0,-1),"Cold request eligibility")
                    else:
                        previous=expected-PERIOD
                        check((x["source_edge"],arrival,eligible)==(previous+100004,previous+100004,previous+100005),"Request generation")
                    ranges[s,"board"].append((h,grant-eligible,valid-eligible,False))
                elif kind=="QUEUE":
                    check(not b,"Unexpected queue")
                    check(h==len(ranges[s,"queue"]) and grant%140==102,"Queued source")
                    ranges[s,"queue"].append((h,grant-arrival,valid-arrival,False))
                else:
                    raise CheckError("Unknown trace")
                if not s.startswith("level_"):
                    rows.append(tuple(v for k,v in x.items() if k!="adaptive"))
                tests[mode,p,kind]+=1
            if mode=="F":
                same[b,p]=rows
            else:
                check(same[b,p]==rows,"Unequal F/A stimulus, latency or data on common tests")
            if b:
                check(set(ranges)=={(k,"board") for k in ("cold_early","cold_late","cross")},"Startup coverage")
                check([len(ranges[k,"board"]) for k in ("cold_early","cold_late","cross")]==[3,3,94],"Missing board requests")
                check(len(ready)==3 and [k[0] for k in ready]==[2,37,157] and all(t+1==s for _,t,s in ready),"Missing readiness exits")
                check(len(controls)==3 and all(int(row[-1])>0 for row in controls) and int(controls[-1][-2])>0,"No repair or real pause")
                check([int(r[-3]) for r in controls]==[3,3,94],"Completed board stream")
                summary.setdefault(mode,{})["startup"] = ready
                summary[mode]["board_rows_per_data_function"]=len(rows)
                summary[mode]["read_requests_during_pause_in_long_run"]=int(controls[-1][-2])
            else:
                for ctx in ("active_clean","active_repair","pause"):
                    for discipline in ("early","hold","gate"):
                        coverage = ranges[ctx,discipline]
                        check([r[0] for r in coverage]==list(range(140)),"Missing request phase")
                        good=[r for r in coverage if not r[3]]
                        limits=(min(r[1] for r in good), max(r[1] for r in good),min(r[2] for r in good),max(r[2] for r in good))
                        check(limits=={"early":(0,139,10,149),"hold":(1,139,11,149),"gate":(1,140,11,150)}[discipline],"Wrong extremum")
                        check(sum(r[3] for r in coverage)==(discipline=="hold"),"Wrong error count")
                for label,edge in (("into_pause",L),("fixed_restart",FIXED),("adaptive_restart",2*L)):
                    check(ranges[label,"hold"]==[(139,103,113,False)],"Lost slot at scan boundary")
                    row=next(r for r in rows if r[2]==label)
                    check(row[6]==edge-1,"Wrong boundary witness")
                queue=ranges["four_pending","queue"]
                check(len(queue)==4 and [r[2]-queue[0][2] for r in queue]==[0,140,280,420],"FIFO spacing")
                check([r[2] for r in queue]==[111,251,391,531],"Boundary of the four-head stream")
                if mode=="A":
                    for level in range(2,8):check(ranges[f"level_{level}","early"]==[(139,103,113,False)],"Missing adaptive level")
                check(len(controls)==1 and int(controls[0][-1])>0,"No physical repairs")
                check(len(signals)==14,"Detailed boundary trace")
                fail=evidence[0]
                for sig in signals:
                    a,plane,t,h,req,src,candidate,g,v,pad,cs,oe,we,dq,sampled,value=sig
                    check(plane==p and a==int(mode=="A") and h==t%140,"Signal tag")
                    if h in (101,102):check(candidate==0x10020,"Precaptured address not observed")
                    if h==102:check(req and g and pad==pin(0x10020) and src==fail[4] and not cs and not oe and we,"Wrong-boundary witness")
                    if h==108:check(sampled==fail[-1],"Actual DQ capture")
                    if h==112:check(v and value==fail[-1] and cs and oe and we,"Bad response witness")
                summary[mode]["external_requests_per_data_function"]=sum(map(len,ranges.values()))
                summary[mode]["silent_wrong_address_traces_per_data_function"]=len(evidence)
                summary[mode]["mandatory_repairs_external_suite"]=int(controls[0][-1])
                summary[mode]["four_pending_arrival_to_valid_ticks"]=[r[2] for r in queue]
                summary[mode].setdefault("counterexample_active",{})[str(p)]=fail
    return {"built_in_and_core":summary,
        "clock_tick_ns":10,"grant_to_sample_data_register_valid_consumer_ticks":[6,7,10,11],
        "first_E0_to_grant_valid_ticks":[102,112],
        "from_cold_deassertion_to_grant_valid_ticks":[103,113],
        "recurring_from_req_publication_ticks":[96,106],"recurring_from_first_eligible_ticks":[95,105],
        "intergrant_ticks":PERIOD,
        "early_address_req_to_grant_ticks":[0,139],"early_address_req_to_valid_ticks":[10,149],
        "late_address_suppressed_req_to_grant_ticks":[1,140],"late_address_suppressed_req_to_valid_ticks":[11,150],
        "rows_checked":sum(tests.values()),"independent_icarus_reads":8,
        "paired_modes_identical_on_common_stimulus":True}


def load_zip(path):
    with zipfile.ZipFile(path) as archive:
        check(len(archive.namelist())==len(FILES) and set(archive.namelist())==FILES,"Unexpected archive members")
        return {f:archive.read(f) for f in sorted(FILES)}


def check_mutation(raw):
    # Replace the erroneously returned value by the newly requested value,
    # leaving the old physical address and other pad observations intact.
    key="F_core_0.csv"; lines=raw[key].decode().splitlines()
    for index,line in enumerate(lines):
        fields=line.split(",")
        if fields[:6]==["EXT","0","0","active_clean","hold","102"]:
            fields[-1]=fields[-2];lines[index]=",".join(fields);break
    else: raise CheckError("Missing mutation target")
    mutated=dict(raw);mutated[key]=("\n".join(lines)+"\n").encode()
    try:check_results(mutated)
    except CheckError as exc:
        check(str(exc)=="Response data or deadline","Unexpected sentinel failure")
    else:raise CheckError("False corrected payload accepted")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--record",type=Path,help="capture emitted raw simulator logs")
    parser.add_argument("--results",type=Path,default=HERE/"results")
    parser.add_argument("--reference",type=Path,help="compare all member bytes with a published ZIP")
    args=parser.parse_args()
    bundle=args.results/"pin-trials.zip"; result_path=args.results/"summary.json"
    if args.record:
        raw={f:(args.record/f).read_bytes() for f in sorted(FILES)}
    else:
        raw=load_zip(bundle)
    result=check_results(raw);check_mutation(raw)
    if args.reference:
        check(raw==load_zip(args.reference),"Raw bytes differ from the reference run")
    if args.record:
        args.results.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(bundle,"w") as archive:
            for name,content in sorted(raw.items()):
                entry=zipfile.ZipInfo(name)
                entry.create_system=3  # Identical metadata on Windows and Linux.
                entry.external_attr=0o600 << 16
                archive.writestr(entry,content,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
        result_path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
    else:
        check(result==json.loads(result_path.read_text(encoding="utf-8")),"Report differs from raw observations")
    print("PASS",result["rows_checked"],"request records; F/A paired, 140-phase coverage, negative sentinel; ZIP",sha256(bundle.read_bytes()).hexdigest())
