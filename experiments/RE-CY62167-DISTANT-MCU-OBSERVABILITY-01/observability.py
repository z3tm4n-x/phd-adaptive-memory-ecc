#!/usr/bin/env python3
"""Bounded observability audit for CY62167 proton MCU cluster data.

This module deliberately separates registered clusters from parent-particle truth.
It never interprets field0_raw, never treats x/y axis names as row/column names,
and evaluates W16 only as a declared regular-interleaving comparator.
"""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, itertools, json, math, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

TASK_ID='RE-CY62167-DISTANT-MCU-OBSERVABILITY-01'
START='672a9daf2d799ed72491a8d701395cdb458bee21'
BRANCH='research/cy62167-distant-mcu-observability-01'
N_BITS=16_777_216
NX=NY=4096
ENERGY_FILES=[
 (0.9,'clust_p0.9MeV.txt','10ab9973e182b8aa2d6647d3fb2d451a'),
 (1.0,'clust_p1MeV.txt','a0dfb8e032b4102bd00815d800b9a770'),
 (1.1,'clust_p1.1MeV.txt','68b78596d0903c014747c62c606eb851'),
 (1.5,'clust_p1.5MeV.txt','fa049e8ef13a9c5e1e5d2c41353a6e4f'),
 (2.5,'clust_p2.5MeV.txt','7cee7f8bc1497e3c79d11b2f304d2540'),
 (3.0,'clust_p3MeV.txt','88f4ce176d5a6826f71f37ff32641c0e'),
 (4.0,'clust_p4MeV.txt','713f0f33a961e143598021c88c5f2de0'),
 (5.0,'clust_p5MeV.txt','2bcef85b1a963b2c4da61bf5c5544cce'),
 (29.0,'clust_p29MeV.txt','be0a36e3ef587b3fa9fdcf0663aa404e'),
 (40.0,'clust_p40MeV.txt','ff7fe1c5365f6ade8c81680423d68aa3'),
 (80.0,'clust_p80MeV.txt','0ce14a24799e0523b8242d0d66d04c96'),
 (124.0,'clust_p124MeV.txt','dbf5911333c50a5b6eb366c026208e7c'),
 (164.0,'clust_p164MeV.txt','ec1a27f27a6b904557125d3219116a13'),
 (186.0,'clust_p186MeV.txt','28614930fc22db2365e07b6a55850a17')]
TIMESTAMP_ENERGIES={0.9,1.0,1.1,1.5,2.5,3.0,4.0,5.0,186.0}

def md5(path):
 h=hashlib.md5()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def load_task1_parser(repo_root:Path):
 p=repo_root/'experiments/RE-CY62167-PROTON-01/parse_zenodo_protons.py'
 spec=importlib.util.spec_from_file_location('task1_parser',p); mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod

def pairs(cells):
 for a,b in itertools.combinations(cells,2): yield abs(a.x-b.x),abs(a.y-b.y)
def square3_connected(cells):
 n=len(cells)
 if n<=1:return True
 seen={0}; stack=[0]
 while stack:
  i=stack.pop();a=cells[i]
  for j,b in enumerate(cells):
   if j not in seen and max(abs(a.x-b.x),abs(a.y-b.y))<=3: seen.add(j);stack.append(j)
 return len(seen)==n
def exact16(dx,dy): return (dx==0 and dy==16) or (dy==0 and dx==16)
def multiple16(dx,dy): return (dx==0 and dy>=16 and dy%16==0) or (dy==0 and dx>=16 and dx%16==0)

def analyze_clusters(raw_dir:Path, repo_root:Path):
 parser=load_task1_parser(repo_root); rows=[]; records_by_e={}; all_stats={}
 for e,name,expected in ENERGY_FILES:
  p=raw_dir/name
  if md5(p)!=expected: raise ValueError(f'MD5 mismatch {name}')
  recs=list(parser.physical_records(parser.parse_cluster_file(p)));records_by_e[e]=recs
  pairctr=Counter(); k2bad=0; n_ge3=0; n_ge3_span4=0; n_ge3_span16=0; n_exact16=0;n_mult16=0;n_bridge_exact=0
  anythr={4:0,8:0,16:0,32:0};same_x_pairs=same_y_pairs=0; total_pairs=0
  spansx=[];spansy=[];maxinf=[];maxman=[]; anchors_match=0; bounds_match=0
  cminx=10**9;cmaxx=-1;cminy=10**9;cmaxy=-1
  for r in recs:
   cs=r.cells; xs=[c.x for c in cs];ys=[c.y for c in cs]
   cminx=min(cminx,*xs);cmaxx=max(cmaxx,*xs);cminy=min(cminy,*ys);cmaxy=max(cmaxy,*ys)
   dxspan=max(xs)-min(xs);dyspan=max(ys)-min(ys);spansx.append(dxspan);spansy.append(dyspan)
   anchors_match += int(r.xadd==r.xmin and r.yadd==r.ymin)
   bounds_match += int((r.xmin,r.xmax,r.ymin,r.ymax)==(min(xs),max(xs),min(ys),max(ys)))
   ps=list(pairs(cs)); total_pairs += len(ps)
   for dx,dy in ps:
    pairctr[(dx,dy)]+=1;same_x_pairs+=int(dx==0 and dy>0);same_y_pairs+=int(dy==0 and dx>0)
   mi=max([max(a) for a in ps],default=0); mm=max([sum(a) for a in ps],default=0);maxinf.append(mi);maxman.append(mm)
   for t in anythr: anythr[t]+=int(any(max(dx,dy)>=t for dx,dy in ps))
   if r.k==2 and mi>3:k2bad+=1
   if r.k>=3:
    n_ge3+=1;n_ge3_span4+=int(mi>=4);n_ge3_span16+=int(mi>=16)
   ex=any(exact16(dx,dy) for dx,dy in ps); mu=any(multiple16(dx,dy) for dx,dy in ps)
   n_exact16+=int(ex);n_mult16+=int(mu)
   if ex and r.k>=3 and square3_connected(cs):n_bridge_exact+=1
  top=[{'abs_dx':a,'abs_dy':b,'count':c} for (a,b),c in pairctr.most_common(40)]
  row={'energy_mev':e,'source_file':name,'registered_clusters':len(recs),'timestamp_available':e in TIMESTAMP_ENERGIES,
   'K2_clusters':sum(r.k==2 for r in recs),'Kge3_clusters':n_ge3,'K2_dinf_gt3':k2bad,
   'x_span_mean':float(np.mean(spansx)),'y_span_mean':float(np.mean(spansy)),'x_span_max':max(spansx),'y_span_max':max(spansy),
   'max_pair_dinf_mean':float(np.mean(maxinf)),'max_pair_dinf_max':max(maxinf),'max_pair_dman_max':max(maxman),
   'events_pair_dinf_ge4_fraction':anythr[4]/len(recs),'events_pair_dinf_ge8_fraction':anythr[8]/len(recs),'events_pair_dinf_ge16_fraction':anythr[16]/len(recs),'events_pair_dinf_ge32_fraction':anythr[32]/len(recs),
   'Kge3_span_dinf_ge4_fraction':n_ge3_span4/max(n_ge3,1),'Kge3_span_dinf_ge16_fraction':n_ge3_span16/max(n_ge3,1),
   'same_axis_x_pair_count':same_x_pairs,'same_axis_y_pair_count':same_y_pairs,'all_within_cluster_pair_count':total_pairs,
   'w16_exact_candidate_event_count':n_exact16,'w16_exact_candidate_event_fraction':n_exact16/len(recs),
   'w16_multiple_candidate_event_count':n_mult16,'w16_multiple_candidate_event_fraction':n_mult16/len(recs),
   'w16_exact_candidate_bridge_event_count':n_bridge_exact,
   'pair_offset_counts_json':json.dumps({f'{a},{b}':c for (a,b),c in sorted(pairctr.items())},separators=(',',':')),
   'top_pair_offsets_json':json.dumps(top,separators=(',',':')),
   'xadd_yadd_equal_xmin_ymin_fraction':anchors_match/len(recs),'header_bounds_equal_cell_bounds_fraction':bounds_match/len(recs),
   'coordinate_x_min':cminx,'coordinate_x_max':cmaxx,'coordinate_y_min':cminy,'coordinate_y_max':cmaxy}
  rows.append(row);all_stats[e]=row
 return rows,records_by_e,all_stats

def relation_probability_exact16(nx=NX,ny=NY):
 total=N_BITS*(N_BITS-1)/2; favorable=ny*(nx-16)+nx*(ny-16); return favorable/total
def relation_probability_multiple16(nx=NX,ny=NY):
 total=N_BITS*(N_BITS-1)/2
 sx=sum(nx-16*m for m in range(1,(nx-1)//16+1)); sy=sum(ny-16*m for m in range(1,(ny-1)//16+1))
 return (ny*sx+nx*sy)/total

def cross_cluster(records_by_e):
 out=[]; pex=relation_probability_exact16();pmu=relation_probability_multiple16()
 for e,name,_ in ENERGY_FILES:
  recs=records_by_e[e]
  if not any(r.timestamp_sod is not None for r in recs):
   out.append({'energy_mev':e,'source_file':name,'dt_class':'NA','registered_cluster_pairs_examined':0,'cell_pair_opportunities':0,'observed_w16_exact_cell_pairs':0,'expected_independent_w16_exact_cell_pairs':0,'observed_w16_multiple_cell_pairs':0,'expected_independent_w16_multiple_cell_pairs':0,'exact16_obs_over_expected':'','multiple16_obs_over_expected':'','diagnostic_status':'NO_TIMESTAMP_DIAGNOSTIC'});continue
  byseg=defaultdict(lambda:defaultdict(list))
  for r in recs:
   if r.timestamp_sod is not None:byseg[r.segment_id][r.timestamp_sod].append(r)
  for dtclass in ('same_bin','adjacent_bin'):
   ncp=opp=obsx=obsm=0
   for bins in byseg.values():
    if dtclass=='same_bin': jobs=((v[i],v[j]) for v in bins.values() for i in range(len(v)) for j in range(i+1,len(v)))
    else: jobs=((a,b) for t,v in bins.items() for a in v for b in bins.get(t+1,[]))
    for a,b in jobs:
     ncp+=1;opp+=a.k*b.k
     for ca in a.cells:
      for cb in b.cells:
       dx,dy=abs(ca.x-cb.x),abs(ca.y-cb.y);obsx+=int(exact16(dx,dy));obsm+=int(multiple16(dx,dy))
   ex=opp*pex;mu=opp*pmu
   out.append({'energy_mev':e,'source_file':name,'dt_class':dtclass,'registered_cluster_pairs_examined':ncp,'cell_pair_opportunities':opp,'observed_w16_exact_cell_pairs':obsx,'expected_independent_w16_exact_cell_pairs':ex,'observed_w16_multiple_cell_pairs':obsm,'expected_independent_w16_multiple_cell_pairs':mu,'exact16_obs_over_expected':obsx/ex if ex>0 else '', 'multiple16_obs_over_expected':obsm/mu if mu>0 else '','diagnostic_status':'DIAGNOSTIC_ONLY_TIMESTAMP_IS_DETECTION_READOUT_SCALE_NOT_PARENT_TIME'})
 return out

def write_csv(path,rows):
 with Path(path).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def mapping_rows(stats):
 ex=sum(v['w16_exact_candidate_event_count'] for v in stats.values());k2bad=sum(v['K2_dinf_gt3'] for v in stats.values())
 return [
 {'scenario':'W0','declared_mapping':'ID=1 / no effective spatial protection comparator','coordinate_requirement':'registered transformed XY geometry only','within_cluster_observable':'YES','distant_split_component_observable':'NO','key_censoring':'registered cluster is a post-processed object, not independently observed parent event','identified_set':'local registered K>=2 component observable; same-parent probability not point-identified','disposition':'C','can_compute_p_D_next':'AS_IDENTIFIED_SET'},
 {'scenario':'W16-reg','declared_mapping':'regular ID=16 comparator; same-axis exact-16 relation is primary diagnostic','coordinate_requirement':'assume transformed XY axes support regular-grid relative offsets; axis row/column identity not asserted','within_cluster_observable':'PARTIAL','distant_split_component_observable':'NO','key_censoring':f'K2 dInf>3 count={k2bad}; isolated ID16 pair cannot enter one K2 cluster under observed square-3 support; bridge K>=3 and cross-cluster populations are censored/ambiguous','identified_set':f'observed within-cluster exact16 candidates={ex}; conservative parent-level set remains broad because split clusters cannot be linked to one particle','disposition':'C','can_compute_p_D_next':'AS_IDENTIFIED_SET'},
 {'scenario':'W-unknown','declared_mapping':'all manufacturer-compatible proprietary mappings not otherwise identified','coordinate_requirement':'exact data/parity-cell to ECC-word transformation','within_cluster_observable':'NO_FOR_WORD_COLLISION','distant_split_component_observable':'NO','key_censoring':'exact W absent; pre-clustering observations and parent-event timestamps absent; parity locations absent','identified_set':'no nontrivial device-specific p_D identified','disposition':'D','can_compute_p_D_next':'NO'}]

def observation_json(stats):
 allrows=list(stats.values())
 return {'task_id':TASK_ID,'raw_file_record_contract':{'record':'already-formed cluster block: cluster id + bounding-box header + xadd/yadd + optional HH:MM:SS + K cell rows + declared count','cell_row':'(x,y) or (field0_raw,x,y)','field0_raw':'UNDOCUMENTED; preserved only; no new semantics assigned'},'cluster_semantics':{'status':'POST_PROCESSED_CLUSTER_NOT_PARENT_GROUND_TRUTH','source_chain':'Zenodo states MCU were determined using Tsiligiannis-2014/Bosser-2015 procedure','spatial_rule_evidence':'historical method: detection window extends 3 bit cells in every direction; recursive expansion; later merge passes','raw_reproduction':{'all_K2_dinf_le3':all(r['K2_dinf_gt3']==0 for r in allrows),'K2_literal_Manhattan_not_required':'Task-1/raw geometry has dM>3 cases while square-3 invariant holds','Kge3_recursive_span_exists':any(r['Kge3_span_dinf_ge4_fraction']>0 for r in allrows)},'temporal_rule_evidence':'Bosser historical method also required detections within 2 seconds; additional merge passes existed. Exact implementation producing Zenodo files is not published.','cluster_id':'post-processing sequence label; resets can mark parser segments, not proven parent-particle ids.'},'timestamp':{'availability':'present only in 0.9-5 and 186 MeV proton files','confirmed_semantics':'second-resolution value attached to already-formed registered cluster','not_established':'incident-particle arrival time; unique parent-event time; complete raw readout chronology','cross_cluster_use':'diagnostic only; same/adjacent timestamp does not imply common parent'},'unavailable_observations':['pre-clustering bitflip log for all proton runs','per-bit detection/readout timestamp before grouping','exact multi-pass cluster-merge provenance','manufacturer proprietary physical/logical/interleaving transformation','parent-particle event labels']}

def coordinate_json(stats):
 allrows=list(stats.values())
 return {'task_id':TASK_ID,'classification':'TRANSFORMED_PHYSICAL_MAP_COORDINATE_REPRESENTATION','axis_labels':['axis_x','axis_y'],'physical_row_column_names':'NOT ESTABLISHED','evidence':['Bosser 2015 distinguishes logical addresses from physical addresses and states that manufacturer-provided scrambling/interleaving knowledge is required to create physical bitmaps.','LELAPE 2024 states that the relevant Infineon SRAM campaigns used proprietary unscrambling/interleaving information to map logical addresses to physical bitcell locations in the XY plane and then applied MD-based clustering.','Zenodo states its MCU data were determined using the cited clustering procedure.'],'proprietary_transform_publicly_available':False,'xadd_yadd_semantics':'UNDOCUMENTED_ANCHOR_FIELDS; empirical equality to xmin/ymin is reported but no stronger label is assigned','empirical_checks':{'all_header_bounds_match_cells':all(abs(r['header_bounds_equal_cell_bounds_fraction']-1)<1e-15 for r in allrows),'all_xadd_yadd_equal_xmin_ymin':all(abs(r['xadd_yadd_equal_xmin_ymin_fraction']-1)<1e-15 for r in allrows),'global_coordinate_range':[min(r['coordinate_x_min'] for r in allrows),max(r['coordinate_x_max'] for r in allrows),min(r['coordinate_y_min'] for r in allrows),max(r['coordinate_y_max'] for r in allrows)]},'hard_rule':'Offsets are analyzed in supplied transformed XY grid only. x/y are never relabeled physical row/column, and the proprietary transform is not reconstructed.'}

def spectrum_weights(args,outpath):
 root=args.repo_root; t2=root/'experiments/RE-GOES19-PROTON-RATE-01'; kt=root/'experiments/RE-CY62167-DIRECT-FLOOR-KILLTEST-01'
 for p in (t2,kt):
  if str(p) not in sys.path:sys.path.insert(0,str(p))
 from goes19_adapter import load_directory
 from rate_pipeline import reconstruct_goes,low_energy_extension,high_energy_gap_bridge,trap_weights,FOUR_PI,SHIELDS_MM
 from sigma_model import load_experimental_points,sigma_hat,zero_crossing_low
 from sigma_closure import load_pub,sigma_phys
 from direct_floor_killtest import load_multiplicity_points,multiplicity_on_grid,N_BITS as NB
 goes=load_directory(args.goes_dir);z=np.load(args.transport);E=np.asarray(z['energy_mev'],float);shields=np.asarray(z['shield_mm'],float);P=np.asarray(z['primary'],float);S=np.asarray(z['secondary'],float)
 exp=load_experimental_points(args.sigma_csv);pe,ps=load_pub(args.published_csv); sig={'main_loglog':sigma_hat(E,exp,'main_loglog'),'published_rpp_fluka_digitized':sigma_phys(E,pe,ps,exp)}; sigh={k:float((sigma_hat(np.array([600.]),exp,'main_loglog') if k=='main_loglog' else sigma_phys(np.array([600.]),pe,ps,exp))[0]) for k in sig}
 pts=load_multiplicity_points(args.multiplicity_csv,args.false_mcu_csv); pm,kb=multiplicity_on_grid(E,pts,'nominal_logE_linear','low_energy_conservative')
 J,_=reconstruct_goes(goes,E);J*=FOUR_PI;L,_=low_energy_extension(goes,E,zero_crossing_low(exp),2.0);L*=FOUR_PI;inp=J+L;gap,*_=high_energy_gap_bridge(goes);tw=trap_weights(E)
 zones={'NO_GEOMETRY_LT0p9':E<0.9,'PARTIAL_DISTANT_TIMESTAMP_ENVELOPE_0p9_5':(E>=0.9)&(E<=5.0),'UNOBSERVABLE_DISTANT_GT5_TO186':(E>5.0)&(E<=186.0),'NO_GEOMETRY_GT186':E>186.0};rows=[]
 for di,dmm in enumerate(shields):
  for sm,sv in sig.items():
   sums={b:{z:0. for z in zones} for b in ('parent_event','multi_upper','bit_flip')}
   for d in range(2):
    v=goes.valid[:,d];out=(inp[v,d]@P[di].T)+(inp[v,d]@S[di].T);dens=NB*out*sv[None,:]
    vals={'bit_flip':dens,'parent_event':dens/kb[None,:],'multi_upper':dens*pm[None,:]/kb[None,:]}
    for b,a in vals.items():
     for zn,m in zones.items():sums[b][zn]+=float(np.nansum(a[:,m]@tw[m]*300.0))/2
     high=NB*FOUR_PI*(goes.p11[v,d]+gap[v,d])*sigh[sm]
     if b=='parent_event':high=high/kb[-1]
     elif b=='multi_upper':high=high*pm[-1]/kb[-1]
     sums[b]['NO_GEOMETRY_GT186']+=float(np.nansum(high*300.0))/2
   for b in sums:
    tot=sum(sums[b].values())
    for zn,val in sums[b].items():rows.append({'sigma_model':sm,'shield_mm':float(dmm),'budget':b,'observability_domain':zn,'expected_count_valid_period':val,'fraction_of_budget':val/tot if tot else math.nan})
 write_csv(outpath,rows);return rows

def make_report(cross,spec,maps):
 ts=[r for r in cross if r['diagnostic_status'].startswith('DIAGNOSTIC')];maxratio=max([float(r['exact16_obs_over_expected']) for r in ts if r['exact16_obs_over_expected']!=''],default=math.nan)
 lines=[f'# {TASK_ID}','','## Scientific semantic','','The previous kill test established only the conservative inequality `p_D(E,W) <= P(K>=2|E)`: its result B meant that this coarse upper bound could not dismiss a direct term. It did **not** establish that the physical direct floor is large. This task asks how much geometry/observability can narrow that bound.','','## 1. What Zenodo actually observes','','Each file record is already a **registered post-processed cluster**, not a raw parent-particle record. The controlled parser preserves cluster id, bounding box, `xadd/yadd`, optional second-resolution timestamp and cell rows. `field0_raw` remains undocumented. The cited clustering lineage uses a ±3-cell window in both supplied XY axes, a temporal criterion, recursive growth, and later merge passes; the exact version that generated Zenodo is not fully published. Raw/pre-clustering bit records are absent.','','Raw reproduction: every registered K=2 proton cluster has `d_inf<=3`. K>=3 clusters can span farther through recursive/transitive growth; some registered clusters also reflect merge semantics not reproducible from the public files alone.','','## 2. Coordinate provenance','','**Classification: TRANSFORMED physical-map coordinate representation; exact transformation proprietary.** Bosser describes manufacturer-provided scrambling/interleaving knowledge as necessary to convert logical addresses to physical bitmaps, and LELAPE states that the relevant Infineon campaigns used proprietary information to map logical bitflip addresses to XY bitcell locations. This supports treating the supplied XY values as a manufacturer-informed physical-map grid, but it does not publish the transform or establish which axis is a physical row versus column. Therefore this report uses only `axis_x/axis_y`. `xadd/yadd` are not given new semantics.','','## 3. Mapping scenarios','','|scenario|status|what is observable|','|---|---|---|']
 for m in maps:lines.append(f"|{m['scenario']}|{m['disposition']}|{m['identified_set']}|")
 lines += ['','For **W16-reg**, the regular ID=16 relation is only a declared comparator consistent with interleaving-distance literature. It is not the proprietary CY62167 map. An isolated exact-16 same-axis pair cannot occur as one registered K=2 cluster under the reproduced `d_inf<=3` observation rule. It can enter one record only through a K>=3 bridge/merge, otherwise it appears as separate registered clusters. Thus the very topology relevant to W16 is censored by the clustering interface.','','## 4. Cross-cluster temporal diagnostic','',f'Timestamp-bearing files allow same-bin and adjacent-bin diagnostics. The largest raw observed/independent-uniform ratio for exact-16 cross-cluster cell pairs was `{maxratio:.4g}`. This is **not** interpreted as a same-parent excess: timestamps are detection/readout-scale labels on already formed clusters, the exact merge chronology is unavailable, and the independent baseline assumes spatial exchangeability. Hence **cross-cluster distant excess = NOT IDENTIFIABLE**. Files without timestamps receive no reconstructed parent linkage.','','## 5. Spectrum relevance','','The previous GOES/RADAR and both sigma(E) responses are reused unchanged. `spectrum_observability_weight.csv` separates `<0.9 MeV` (no geometry data), `0.9-5 MeV` (timestamped measured envelope: partial distant diagnostic), `>5-186 MeV` (registered geometry exists at measured energies but cross-cluster distant inference is unobservable over the continuous envelope), and `>186 MeV` (no measured geometry; includes the high-energy closure terms). Fractions are reported separately for reconstructed parent-event, multi-upper, and bit-flip budgets.','','## 6. Can p_D(E,W) be computed next?','','- **W0:** only as an identified/registered-cluster set; parent truth is not point identified.','- **W16-reg:** only as a broad identified set / sensitivity model. Within-cluster bridge candidates are observable, but isolated distant same-parent pairs are censored.','- **W-unknown:** no. Exact W is an independent blocker in addition to event observability.','','**Parity-cell status: UNKNOWN.** No 38/32 or pair-count multiplier is applied because parity placement is not exchangeable with data-cell placement.','','**Zebrev 1/2 comparator: NOT TESTABLE** for the current CY62167 registered K=2 population under W16-reg. The K=2 observation process contains no pair beyond the ±3 window, while the declared ID16 same-word relation is distant; cross-cluster parent identity is unavailable.','','**PHYSICAL-SPAN BOUND = NOT ESTABLISHED.** Literature on 65-nm bulk SRAM topology is useful context but does not provide a device-specific hard maximum span for this CY62167 dataset.','','## Overall answer','','Direct-term inference is limited by **both factors**: event observability/censoring and W. The current data are valuable for within-cluster geometry, but they do not identify the distant same-parent component needed to validate a regular-ID16 collision probability. The next quantitative p_D task should therefore be formulated as an identified-set/sensitivity study unless pre-clustering logs or manufacturer mapping information become available.']
 return '\n'.join(lines)+'\n'

def main():
 p=argparse.ArgumentParser()
 for n in ('raw-dir','repo-root','out'):p.add_argument('--'+n,type=Path,required=True)
 for n in ('goes-dir','transport','sigma-csv','published-csv','multiplicity-csv','false-mcu-csv'):p.add_argument('--'+n,type=Path)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 cluster,records,stats=analyze_clusters(a.raw_dir,a.repo_root);cross=cross_cluster(records);maps=mapping_rows(stats)
 write_csv(a.out/'cluster_span_by_energy.csv',cluster);write_csv(a.out/'mapping_scenario_observability.csv',maps);write_csv(a.out/'cross_cluster_diagnostics.csv',cross)
 obs=observation_json(stats);coord=coordinate_json(stats);(a.out/'observation_contract.json').write_text(json.dumps(obs,indent=2)+'\n');(a.out/'coordinate_provenance.json').write_text(json.dumps(coord,indent=2)+'\n')
 spec=[]
 if a.goes_dir and a.transport and a.sigma_csv and a.published_csv and a.multiplicity_csv and a.false_mcu_csv:spec=spectrum_weights(a,a.out/'spectrum_observability_weight.csv')
 val={'task_id':TASK_ID,'starting_sha':START,'working_branch':BRANCH,'raw_files_verified_md5':all(md5(a.raw_dir/n)==h for _,n,h in ENERGY_FILES),'K2_dinf_le3_all':all(r['K2_dinf_gt3']==0 for r in cluster),'header_bounds_consistent_all':coord['empirical_checks']['all_header_bounds_match_cells'],'xadd_yadd_anchor_empirical_all':coord['empirical_checks']['all_xadd_yadd_equal_xmin_ymin'],'coordinate_classification':coord['classification'],'cross_cluster_distant_excess':'NOT_IDENTIFIABLE','physical_span_bound':'NOT_ESTABLISHED','parity_cell_status':'UNKNOWN','zebrev_half_comparator':'NOT_TESTABLE','disposition_by_mapping':{r['scenario']:r['disposition'] for r in maps},'can_p_D_be_computed_next':'AS_IDENTIFIED_SET_FOR_DECLARED_W0_W16_REG; NO_FOR_W_UNKNOWN'}
 if spec:val['spectrum_rows']=len(spec)
 (a.out/'validation.json').write_text(json.dumps(val,indent=2)+'\n')
 manifest={'task_id':TASK_ID,'starting_sha':START,'working_branch':BRANCH,'zenodo_doi':'10.5281/zenodo.8314389','raw_inputs':[{'energy_mev':e,'file':n,'md5':h,'sha256':sha256(a.raw_dir/n)} for e,n,h in ENERGY_FILES],'controlled_method_sources':[{'doi':'10.1109/TNS.2014.2313742','role':'clustering lineage'},{'doi':'10.1109/TNS.2015.2496874','role':'physical/logical map and recursive clustering lineage'},{'doi':'10.1109/TNS.2024.3450607','role':'proprietary unscrambling/interleaving provenance and MD comparator'},{'document':'Infineon AN88889','role':'(32,38) Hamming and 16-bit interleaving architecture only'},{'doi':'10.1109/TNS.2010.2042818','role':'regular interleaving-distance comparator'},{'doi':'10.1109/RADECS.2017.8696217','role':'scalar one-half prior-art comparator'}],'unchanged_interfaces':['RE-CY62167-PROTON-01 parser and false-MCU inputs','RE-GOES19-PROTON-RATE-01 GOES/RADAR transport and sigma closure','RE-CY62167-DIRECT-FLOOR-KILLTEST-01 reconstructed event interface']}
 (a.out/'input_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(a.out/'REPORT.md').write_text(make_report(cross,spec,maps));print(json.dumps(val,indent=2))
if __name__=='__main__':main()
