"""Independent consumer: raw pin events, released-address sets, closed-cell history.
No VPI/RTL decoder or native cost calculator is imported here.
"""
from collections import Counter
import hashlib
import sys
from build_model import BANK
sys.path.insert(0,str(BANK.parent))
from memory_oracle import MemoryOracle

A, L, CUT, INSTALL = 8, 280, 250, 270  # time below in nominal 10ns ticks
REQ = (5,10,19,38,75,149,298,596)

def limits(z):
    return 1 << sum(z>=n for n in REQ)

def history(z,dirty,step,r,bad):
    # Count successive complete, wholly eligible COMMON cells, not packets.
    if r==0:
        return 0,False,1
    if bad:
        z,dirty,step=0,True,1
    if r%256==0:
        z=0 if dirty else min(z+1,REQ[-1])
        dirty,step=False,limits(z)
    return z,dirty,step

def prescribed(case,mixed):
    last=4 if mixed else 3
    if case in (1,5,6,8,16,18): return [(215,1,last,37)]
    if case==15: return [(1280*L+215,1,last,21)]
    if case==17: return [(r*L+215,r,last,r) for r in range(38)]
    if case==2: return [(22,1,1,0),(22,1,2,33),(185,2,2,21),(185,2,3,37)]
    if case==3: return [(2,1,0,35)]
    if case==4: return [(223,1,last,32)]
    if case==23: return [(2,1,0,12),(12,2,0,12)]
    return []

def audit(lines,case,end,mixed=0):
    mem=MemoryOracle(5)
    for w,v in enumerate(mem.words): v.data=0xa5bc3410+0x10001*w
    def word(a): return 4 if mixed and a==7 else a%4
    def dq(a): return (mem.words[word(a)].data >> (16*(a>=4 and not(mixed and a==7)))) & 65535
    r=-1; next_start=0; step=1; z=0; cell_dirty=False; last_bad=0
    op=None; inj=[]; starts=reads=writes=repairs=passes=active_ticks=0
    useful_ticks=0; switches=[]; changes=0; late=stale=dupes=0
    counts=Counter(); digest=hashlib.sha256(); last_t=-1; end_row=None
    invalid_cells=set(); true_cells=set(); pre_invalid=set(); pre_true=set()
    exception_kinds=set(); highlights=[]; tau=None
    cut=None; install_count=0; skipped=0; max_pause=0; install_work=0
    last_pass_start=None; last_release=None; release_gap=0; terminal_locked=False
    # Each tuple describes the actually observed wire interval; at T clip instead
    # of draining or charging a nonexistent release.
    needed_read=needed_write=0; physical_writes=0; seals=0
    for line_no,line in enumerate(lines,1):
        try:
            if not line.strip() or "$finish called" in line: continue
            fields=line.split(); k=fields[0]; v=list(map(int,fields[1:]))
            assert end_row is None, "records after END"
            t=v[0]
            assert last_t<=t<=end, ("time order",t,last_t)
            last_t=t
            if k not in ("Z","END"):
                digest.update((" ".join(fields)+"\n").encode("ascii"))
            if k=="B":
                _,nr=v
                assert t==nr*L and nr==next_start and op is None, ("actual grant epoch",nr,next_start)
                if r>=0: assert cut is not None and installed
                if last_pass_start is not None: max_pause=max(max_pause,t-last_pass_start-L)
                if last_release is not None: release_gap=max(release_gap,t-last_release)
                last_pass_start=t;passes+=1;active_ticks+=min(L,end-t)
                r=nr; started=[]; completions=[]; coverage=[]; deliveries=[]; poisoned=False
                seal=None;cut=None;installed=False;this_app=[];pass_repairs=0
            elif k=="J":
                _,parent,w,b=v;inj.append(tuple(v))
                # Test-only auxiliary stop, NEVER fed to the decision or port.
                pending=(op and word(op["a"])==w and op["sample"] and op["sample"][0])
                if tau is None and (mem.words[w].errors or pending): tau=t
                mem.words[w].toggle(b,t*10)
            elif k=="G":
                _,rr,req,a=v
                idx=len(started)
                assert rr==r and t==r*L+140*(idx//4)+(0,24,52,76)[idx%4] and req==idx
                assert a==(6 if case==6 and r==0 and idx==7 else idx)
                if a!=req:
                    exception_kinds.add("substituted_mandatory_address")
                    if tau is None: tau=t
                assert op is None and 0<=idx<A
                mem.begin(starts,word(a),10*t,"control");starts+=1;started.append(a)
                op=dict(start=t,a=a,sample=None,wrote=False)
                needed_read+=min(10,end-t)
            elif k=="S":
                _,a,err,data=v
                assert op and op["a"]==a and t==op["start"]+6 and op["sample"] is None
                _,expected=mem.observe(t*10)
                assert bool(err)==expected and data==dq(a), ("sample DQ/ERR",v,expected)
                op.update(sample=(err,data)); reads+=1
                if err: needed_write+=max(0,min(10,end-op["start"]-10))
            elif k=="W":
                _,a,data,ok=v
                assert op and op["a"]==a and op["sample"]==(1,data)
                assert t==op["start"]+16 and not op["wrote"]
                assert ok==int(not(case==8 and r==0 and a==7))
                writes+=1
                if ok:
                    w=mem.words[word(a)]
                    w.errors={b:birth for b,birth in w.errors.items() if birth>=10*op["start"]}
                    op["wrote"]=True;physical_writes+=1
                else:
                    exception_kinds.add("missing_mandatory_write")
                    if tau is None: tau=t
            elif k=="R":
                _,a,hit,we,drop=v
                assert op and op["a"]==a and op["sample"] is not None
                assert t==op["start"]+(20 if hit else 10) and hit==op["sample"][0]
                assert bool(we)==op["wrote"] and (not hit or we or case==8)
                assert drop==int(case==5 and r==0 and a==7)
                completions.append((a,hit,we,t))
                last_release=t
                if we:
                    repairs+=1;pass_repairs+=1
                    if tau is None: pre_true.add((r+255)//256)
                if not drop: coverage.append((a,hit,we))
                mem.lock=None;mem.trace.clear();mem.flags.clear();op=None
            elif k=="D":
                assert v[1]==completions[-1][0];poisoned=True
            elif k=="F":
                _,rr,seen,reported=v
                assert rr==r and seal is None and t==completions[-1][3]
                assert seen==A and not poisoned and [p[0] for p in coverage]==list(range(A))
                assert all(not h or w for _,h,w in coverage) and reported==sum(h for _,h,_ in coverage)
                assert op is None and t==(r*L+216+(20 if coverage[-1][1] else 10))
                seal=(t,reported);seals+=1
            elif k=="P":
                _,tag,cnt,complete=v
                assert seal and t>=seal[0] and complete
                if tag!=r: stale+=1
                elif t>r*L+CUT: late+=1
                else:
                    if deliveries and cnt==deliveries[0]:dupes+=1
                    deliveries.append(cnt)
            elif k=="A":
                assert op is None and t%140==102
                this_app.append(t); useful_ticks+=min(10,end-t)
            elif k=="C":
                _,rr,seen,local_count,sealed,bad,observed,choice=v
                assert rr==r and t==r*L+CUT and cut is None and op is None
                assert len(started)==len(completions)==A
                independently_full=(not poisoned and [x[0] for x in coverage]==list(range(A))
                                    and all(not h or w for _,h,w in coverage))
                assert bool(sealed)==independently_full==(seal is not None)
                if sealed: assert seen==A and local_count==sum(h for _,h,_ in coverage)
                valid=independently_full and bool(deliveries) and len(set(deliveries))==1
                assert bool(bad)==(not valid)
                assert observed==(seal[1] if valid else 0), ("cut count",v)
                ref=history(z,cell_dirty,step,r,bad or observed!=0)
                assert ref[2]==choice, ("step at cut",r,ref[2],choice)
                cut=dict(round=r,cut_ns=10*t,full=bool(sealed),count=observed if valid else None,
                         local_count=seal[1] if sealed else None,valid=bool(valid),
                         last_release_ns=10*completions[-1][3],proposed=choice)
                if valid: counts[str(observed)]+=1
                if not valid and tau is None: pre_invalid.add((r+255)//256)
            elif k=="K":
                _,rr,actual,anchor,nxt,lost,cost,appcost=v
                assert rr==r and t==r*L+INSTALL and cut and not installed
                assert lost==int(case==13 and r==1280)
                bad=not cut["valid"] or lost or bool(cut["count"])
                old=step
                z,cell_dirty,step=history(z,cell_dirty,step,r,bad)
                common=(r+255)//256
                if bad and r: last_bad=common
                assert (actual,anchor,nxt)==(step,last_bad,r+step), ("installation",v,step,last_bad)
                assert cost==0 and appcost==sum(max(0,min(t,a+10)-max(r*L+CUT,a)) for a in this_app)
                install_work+=cost
                if pass_repairs: true_cells.add(common)
                if not cut["valid"] or lost: invalid_cells.add(common)
                if lost and tau is None: pre_invalid.add(common)
                next_start=nxt;installed=True;install_count+=1
                if step!=old: changes+=1;switches.append([r,old,step,10*t,cost*10])
                if r in (0,1,1280,1282,1283,1284,1536,2560,2816,152576,152832,152833) or (case==17 and r==37):
                    highlights.append(dict(**cut,pass_port_ns=100*len(started)+100*sum(h for _,h,_,_ in completions),
                       installed_ns=10*t,step=step,next_round=nxt,cut_install_port_ns=cost*10,
                       cut_install_application_ns=appcost*10,closed_clean_cells=z))
            elif k=="Z":
                _,b=v
                assert installed and op is None and r*L+L<=t<b<=min(end,next_start*L)
                assert not (case==14 and t>=(152577*L)), "designated long gap must be literal"
                skipped+=b-t
            elif k=="END":
                assert t==end;end_row=v
                _,rticks,wticks,held,ap,iticks,iheld,mheld,nb,ns,jump,locked,sealed=v
                assert (rticks,wticks,held)==(needed_read,needed_write,needed_read+needed_write), "port exclusion ledger"
                assert (ap,iticks,iheld,mheld,nb,ns,jump)==(useful_ticks,end-active_ticks,0,0,passes,changes,skipped)
                assert bool(locked)==(op is not None) and bool(sealed)==(seal is not None)
                if r>=0 and not installed: assert end<=r*L+INSTALL
                assert next_start*L>=end or not installed, "missing scheduled next pass"
                terminal_locked=bool(locked)
            else: raise ValueError(("unknown record",k))
        except (ValueError,TypeError,IndexError,AssertionError) as e:
            raise AssertionError(f"case={case}, line={line_no}: {line.strip()} ; {e}") from e
    assert end_row is not None and inj==prescribed(case,mixed), ("stimulus mismatch",inj)
    _,rd,wr,held,ap,iticks,iheld,mheld,nb,ns,jump,_,_=end_row
    return dict(ticks_ns=10,horizon_ns=10*end,passes=passes,seals=seals,
                starts=starts,completed_samples=reads,write_edges=writes,committed_writes=physical_writes,
                corrections_released=repairs,injections=len(inj),counts_at_valid_cuts=dict(sorted(counts.items())),
                invalid_common_cells=sorted(invalid_cells),true_repair_cells=sorted(true_cells),
                additional_cells_before_stop_not_already_true=sorted(pre_invalid-pre_true),
                diagnostic_first_proof_stop_ns=None if tau is None else 10*tau,
                exceptions=sorted(exception_kinds),late=late,stale=stale,identical_packet_duplicates=dupes,
                terminal_locked=terminal_locked,terminal_remaining_positions=sum(len(w.errors) for w in mem.words),
                first_physical_exceedance_ns=min((w.first_exceedance for w in mem.words if w.first_exceedance is not None),default=None),
                read_ns=10*rd,repair_add_ns=10*wr,protected_port_ns=10*held,extra_port_ns=10*(held-rd-wr),
                application_ns=10*ap,between_scans_ns=10*iticks,between_scans_protected_ns=10*iheld,
                management_strip_protected_ns=10*mheld,cut_install_windows=install_count,
                cut_install_protected_ns=10*install_work,maximum_completed_between_scan_pause_ns=10*max_pause,
                max_last_release_to_next_start_ns=10*release_gap,
                folded_idle_ns=10*jump,transitions=switches,witness=highlights,
                event_sha256=digest.hexdigest())
