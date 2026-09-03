from __future__ import annotations
import argparse,csv,json,os
from collections import Counter,defaultdict
from pathlib import Path
from event_partition import load_archive,population_audit,aggregate_population,verify_frozen_addresses,grouped_events,meta_for,frozen_address,word_id,write_csv,sha256_path,RAW_ARCHIVE_SHA256
from mapping_family import build_mapping_family,mapping_id
from cross_section_model import point_cross_sections
from confidence_style import article_direct_upper95_baseline

HERE=Path(__file__).resolve().parent
HI={5.2:(637,1628),15.0:(924,5484),17.0:(950,6707),22.0:(1026,9822),27.0:(998,10876),29.0:(1050,12340),33.0:(476,6230),42.0:(1119,17012),57.0:(1060,21185)}


def sweep(events,maps):
    mappings={(int(m["bit_p"]),int(m["bit_q"])):m for m in maps};pairs=set(mappings);one=defaultdict(set)
    for pq in pairs: one[pq[0]].add(pq);one[pq[1]].add(pq)
    srcN=Counter();srcS=Counter();prepared=[]
    for key,cells in events.items():
        addrs=[frozen_address(c.x,c.y) for c in cells];srcN[key[0]]+=1;srcS[key[0]]+=len(cells);prepared.append((key,cells,addrs))
    nd=defaultdict(Counter);sd=defaultdict(Counter);direct=[]
    for key,cells,addrs in prepared:
        cand=set();K=len(cells)
        for i in range(K):
            for j in range(i+1,K):
                d=addrs[i]^addrs[j];pc=d.bit_count()
                if pc==0:cand.update(pairs)
                elif pc==1:cand.update(one.get(d.bit_length()-1,()))
                elif pc==2:
                    bits=tuple(k for k in range(21) if (d>>k)&1)
                    if bits in pairs:cand.add(bits)
        if not cand: continue
        sf,seg,cid=key;mt=meta_for(sf);xs=[c.x for c in cells];ys=[c.y for c in cells]
        for pq in sorted(cand):
            counts=Counter(word_id(a,*pq) for a in addrs);fail=[v for v in counts.values() if v>=2]
            if not fail: raise AssertionError('candidate classification failed')
            nd[pq][sf]+=1;sd[pq][sf]+=K
            direct.append(dict(source_file=sf,segment_id=seg,cluster_id=cid,radiation_type=mt['radiation_type'],particle=mt['particle'],LET_MeV_cm2_mg='' if mt['LET_MeV_cm2_mg'] is None else mt['LET_MeV_cm2_mg'],energy_MeV='' if mt['energy_MeV'] is None else mt['energy_MeV'],mapping_id=mappings[pq]['mapping_id'],K=K,number_of_failing_words=len(fail),max_same_word_data_cells=max(fail),addresses=json.dumps(addrs,separators=(',',':')),coordinate_summary=f'x=[{min(xs)},{max(xs)}];y=[{min(ys)},{max(ys)}]'))
    out=[];summary=[]
    for pq in sorted(pairs):
        m=mappings[pq]
        for sf in sorted(srcN):
            mt=meta_for(sf);out.append(dict(mapping_id=m['mapping_id'],radiation_type=mt['radiation_type'],particle=mt['particle'],LET_MeV_cm2_mg='' if mt['LET_MeV_cm2_mg'] is None else mt['LET_MeV_cm2_mg'],energy_MeV='' if mt['energy_MeV'] is None else mt['energy_MeV'],source_file=sf,N_events=srcN[sf],N_direct=nd[pq][sf],S_direct_event_cells=sd[pq][sf],S_residual_cells=srcS[sf]-sd[pq][sf]))
        summary.append(dict(mapping_id=m['mapping_id'],bit_p=pq[0],bit_q=pq[1],minimum_spacing=m['minimum_spacing'],N_direct_all_series=sum(nd[pq].values()),N_direct_heavy_ion=sum(v for sf,v in nd[pq].items() if meta_for(sf)['radiation_type']=='heavy_ion'),N_direct_proton=sum(v for sf,v in nd[pq].items() if meta_for(sf)['radiation_type']=='proton'),baseline_mapping=bool(m['baseline_mapping']),retained_55=True))
    direct.sort(key=lambda r:(r['mapping_id'],r['source_file'],r['segment_id'],r['cluster_id']))
    return out,summary,direct

def cross_sections(rows,maps):
    by={(r['mapping_id'],float(r['LET_MeV_cm2_mg'])):r for r in rows if r['LET_MeV_cm2_mg']!='' and meta_for(r['source_file'])['in_P_HI']};out=[]
    for m in maps:
        for L in sorted(HI):
            r=by[(m['mapping_id'],L)];S=int(r['S_direct_event_cells'])+int(r['S_residual_cells'])
            if (int(r['N_events']),S)!=HI[L]: raise AssertionError((L,r['N_events'],S))
            x=point_cross_sections(N_events=int(r['N_events']),S_cells_used=S,N_direct=int(r['N_direct']),S_accumulation=int(r['S_residual_cells']),let_value=L);up,st=article_direct_upper95_baseline(x['sigma_direct_point_cm2'],int(r['N_direct']))
            out.append({'normalization_track':'ARTICLE_COMPAT','mapping_id':m['mapping_id'],'LET_MeV_cm2_mg':L,'N_events':int(r['N_events']),'S_cells_used':S,'N_direct':int(r['N_direct']),'S_direct_event_cells':int(r['S_direct_event_cells']),'S_accumulation':int(r['S_residual_cells']),'F_art_cm-2':x['F_art_cm-2'],'sigma_event':x['sigma_event_cm2'],'sigma_direct_point':x['sigma_direct_point_cm2'],'sigma_accumulation_point':x['sigma_accumulation_point_cm2'],'sigma_direct_article_upper95':'' if up is None else up,'confidence_style_status':st})
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,default=Path(os.environ.get('CY62167_RAW_ARCHIVE','')));ap.add_argument('--output-dir',type=Path,default=Path.cwd());a=ap.parse_args()
    if not str(a.archive): ap.error('--archive or CY62167_RAW_ARCHIVE required')
    outdir=a.output_dir;outdir.mkdir(parents=True,exist_ok=True);parsed=load_archive(a.archive);audit=population_audit(parsed);pop=aggregate_population(audit);checked,bad=verify_frozen_addresses(parsed)
    if bad: raise AssertionError(f'frozen address mismatches: {len(bad)}')
    fam=build_mapping_family();ret=[r for r in fam if r['retained']]
    if len(fam)!=210 or len(ret)!=55: raise AssertionError('210->55 regression failed')
    events=grouped_events(parsed);sweep_rows,summary,direct=sweep(events,ret);dist=Counter(int(r['N_direct_all_series']) for r in summary)
    if dist!=Counter({0:45,4:9,5:1}): raise AssertionError(dist)
    hi=cross_sections(sweep_rows,ret)
    write_csv(outdir/'raw_population_audit.csv',audit);write_csv(outdir/'mapping_family_210.csv',fam);write_csv(outdir/'mapping_family_55.csv',ret);write_csv(outdir/'mapping_sweep_all_series.csv',sweep_rows);write_csv(outdir/'mapping_sweep_summary.csv',summary);write_csv(outdir/'registered_direct_events.csv',direct);write_csv(outdir/'heavy_ion_cross_sections.csv',hi)
    roles={'W_01_02':'W_MIN_REGISTERED_DIRECT','W_00_01':'W_ARTICLE_BASELINE','W_00_11':'W_MAX_REGISTERED_DIRECT'};cos=[]
    for r in hi:
        if r['mapping_id'] in roles:
            mid=r['mapping_id'];role=roles[mid];cos.append(dict(normalization_track=r['normalization_track'],mapping_id=mid,mapping_role=role,LET_MeV_cm2_mg=r['LET_MeV_cm2_mg'],N_events=r['N_events'],N_bit_errors_used=r['S_cells_used'],N_direct_events=r['N_direct'],S_direct_event_cells=r['S_direct_event_cells'],S_accumulation_bits=r['S_accumulation'],sigma_event_cm2=r['sigma_event'],sigma_direct_point_cm2=r['sigma_direct_point'],sigma_accumulation_point_cm2=r['sigma_accumulation_point'],sigma_direct_article_upper95_cm2=r['sigma_direct_article_upper95'],confidence_style_status=r['confidence_style_status']))
    write_csv(outdir/'cosrad_input_cross_sections.csv',cos)
    write_csv(outdir/'heavy_ion_cross_sections_audit_subset.csv',[r for r in hi if r['mapping_id'] in roles])
    write_csv(outdir/'mapping_sweep_audit_subset.csv',[r for r in sweep_rows if r['mapping_id'] in roles])
    print(json.dumps({'archive_sha256':RAW_ARCHIVE_SHA256,'address_records_checked':checked,'population':pop,'mapping_distribution':dict(sorted(dist.items())),'cosrad_sha256':sha256_path(outdir/'cosrad_input_cross_sections.csv')},indent=2,sort_keys=True))
if __name__=='__main__': main()
