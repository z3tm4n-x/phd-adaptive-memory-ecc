#!/usr/bin/env python3
"""Facade/CLI for RE-CY62167-ADDRESS-MAPPING-01."""
from address_mapping_data import *
from address_mapping_parser import *
from address_mapping_gf2 import *
from address_mapping_analysis import run_analysis
import argparse,json
from pathlib import Path

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True,type=Path);p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args(argv)
    r=run_analysis(a.archive,a.output_dir);v=r['validation']
    print(json.dumps({'task_id':TASK_ID,'archive_sha256':r['input_manifest']['provided_archive']['archive_sha256'],'training_eligible':v['training_raw_eligible_count'],'feature_rank':v['gf2_feature_rank'],'training_mismatches':v['training_mismatches'],'heldout_checks':v['heldout_record_checks_after_event_local_dedup'],'heldout_mismatches':v['heldout_mismatches'],'ambiguous_records':v['ambiguous_record_count'],'disposition':v['disposition']},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
