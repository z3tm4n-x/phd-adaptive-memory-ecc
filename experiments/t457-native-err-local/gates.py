"""Predeclared gate cases, physical vs channel exceptions and actual RTL mutants."""
from pathlib import Path
import shutil
import subprocess
from build_model import HERE, run
from oracle import audit, REQ, L

def witness(rows,name,r):
    return next(x for x in rows[name]["witness"] if x["round"]==r)

def verify(rows):
    for name,total,rep in (("clean",800,0),("last_check_bit",900,1),("two_parent_burst",1200,4),
                           ("one_birth_two_alias_ERR",1000,2),("outside_partner",900,1)):
        m=rows[name]
        assert m["protected_port_ns"]==total and m["corrections_released"]==rep
        assert m["counts_at_valid_cuts"]=={str(rep):1} and m["seals"]==1
    m=rows["one_birth_two_alias_ERR"]
    assert m["injections"]==1 and m["terminal_remaining_positions"]==0
    assert rows["two_parent_burst"]["injections"]==4
    assert rows["post_sample_residual"]["counts_at_valid_cuts"]=={"0":1,"1":1}
    assert rows["all_38_positions"]["counts_at_valid_cuts"]=={"1":38}
    assert rows["all_38_positions"]["terminal_remaining_positions"]==0
    for n in ("lost_last_completion","repeated_physical_address","duplicate_release","missing_mandatory_write"):
        assert not rows[n]["counts_at_valid_cuts"] and rows[n]["seals"]==0
    assert rows["lost_last_completion"]["committed_writes"]==1 and not rows["lost_last_completion"]["exceptions"]
    assert rows["repeated_physical_address"]["exceptions"]==["substituted_mandatory_address"]
    assert rows["missing_mandatory_write"]["exceptions"]==["missing_mandatory_write"]
    missing=witness(rows,"lost_report_after_write",0)
    assert missing["full"] and missing["local_count"]==1 and missing["count"] is None
    assert rows["lost_report_after_write"]["committed_writes"]==1
    assert witness(rows,"lost_report_after_write",1)["count"]==0
    for n in ("exact_cut","before_cut"):
        w=witness(rows,n,1280)
        assert w["step"]==2 and w["next_actual_start_ns"]==1282*L*10
    a,b=rows["exact_cut"],rows["exact_cut_literal"]
    assert a["folded_idle_ns"]>0 and not b["folded_idle_ns"]
    assert {k:v for k,v in a.items() if k!="folded_idle_ns"}=={k:v for k,v in b.items() if k!="folded_idle_ns"}
    assert rows["duplicate_at_threshold"]["identical_packet_duplicates"]==2
    assert witness(rows,"duplicate_at_threshold",1024)["closed_clean_cells"]==4
    assert witness(rows,"duplicate_at_threshold",1024)["step"]==1
    assert rows["loss_and_requalification"]["additional_cells_before_stop_not_already_true"]==[6]
    for n in ("loss_and_requalification","one_tick_late_and_stale"):
        prior=witness(rows,n,1280); bad=witness(rows,n,1282)
        assert prior["next_actual_start_ns"]==1282*L*10
        assert not bad["valid"] and bad["step"]==1 and bad["next_actual_start_ns"]==1283*L*10
    assert rows["one_tick_late_and_stale"]["late"]==rows["one_tick_late_and_stale"]["stale"]==1
    assert [x[:3] for x in rows["loss_and_requalification"]["transitions"]]==[
        [1280,1,2],[1282,2,1],[2816,1,2]]
    assert witness(rows,"loss_and_requalification",2816)["closed_clean_cells"]==5
    for n in ("missed_install","last_ERR_at_promotion","conflicting_report","late_at_threshold"):
        w=witness(rows,n,1280)
        assert w["step"]==1 and w["next_actual_start_ns"]==1281*L*10
    assert witness(rows,"last_ERR_at_promotion",1280)["count"]==1
    assert witness(rows,"missed_install",1280)["proposed"]==2
    m=rows["all_rungs_long_pause"]
    assert [t[0] for t in m["transitions"][:-1]]==[256*n for n in REQ]
    assert [t[2] for t in m["transitions"]]==[2,4,8,16,32,64,128,256,1]
    assert witness(rows,"all_rungs_long_pause",152832)["next_actual_start_ns"]==152833*L*10
    assert m["maximum_completed_between_scan_pause_ns"]==255*L*10
    assert m["max_last_release_to_next_start_ns"]==255*L*10+540 and m["application_ns"]==200
    t=rows["terminal_inside_write"]
    assert t["terminal_locked"] and t["seals"]==0 and t["protected_port_ns"]==870
    t=rows["post_stop_accounting"]
    assert t["diagnostic_first_proof_stop_ns"]==120 and t["first_physical_exceedance_ns"] is None
    assert t["invalid_common_cells"] and not t["additional_cells_before_stop_not_already_true"]
    assert (t["passes"],t["protected_port_ns"])==(3,2500)
    assert all(m["extra_port_ns"]==m["between_scans_protected_ns"]==0 for m in rows.values())

def sentinels(work):
    src=(HERE/"native.sv").read_text()
    # Alter the actual test DUT, not the expected results. Compilation errors
    # and unexpected failures do not count as a successful negative control.
    mutations=[
        ("early_zero","seen==A-1","seen==A-2",0,L,"F 202 0 7 0"),
        ("lost_final_ERR","count<=count+hit","count<=count+(addr==A-1?0:hit)",1,L,"F 236 0 8 0"),
        ("stale_actual_start","next_round<=round_no+chosen","next_round<=round_no+(cut_bad?step:chosen)",
         11,1285*L,"installation"),
        ("idle_poll","!launch && (!locked || release_event)",
         "!launch && (!locked || release_event) && !(!active && phase>=126 && phase<130)",
         12,1283*L,"port exclusion ledger")]
    out={}
    for name,old,new,case,end,marker in mutations:
        assert src.count(old)==1
        d=work/("mutation-"+name);d.mkdir()
        path=d/"native.sv";path.write_text(src.replace(old,new))
        shutil.copyfile(work/"policy_vpi.vpi",d/"policy_vpi.vpi")
        subprocess.run(["iverilog","-g2012","-s","tb","-o",str(d/"sim"),str(path),str(HERE/"tb.sv")],check=True)
        trace=run(d,case,end,False,True)
        try:
            with trace.open() as h: audit(h,case,end)
        except AssertionError as e:
            assert marker in str(e),("unexpected sentinel failure",name,str(e))
            out[name]=str(e)
        else: raise AssertionError(("undetected RTL mutation",name))
    return out
