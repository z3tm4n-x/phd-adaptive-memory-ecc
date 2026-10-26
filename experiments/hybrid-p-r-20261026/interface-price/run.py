"""Reproduce only new interface/price diagnostics."""
import argparse
import hashlib
import json
from common import HERE,encoded,load
import interface
import price

def run(historical_root=None):
    manifest,inp,cfg,history=load(historical_root)
    return dict(base_main=manifest['base_main'],input_sha256=manifest['canonical_input_sha256'],
                current_source_hashes=len(manifest['source_sha256']),
                historical_source_hashes=len(manifest['historical_sources']),
                interface=interface.calculate(inp,cfg,history),
                lower_price=price.calculate(inp,cfg,manifest),
                acceptance=False,old_Q_recomputed=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical-root')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=run(args.historical_root);payload=encoded(result);target=HERE/'result.json'
    if args.check:
        if target.read_bytes()!=payload:raise AssertionError('Byte replay mismatch')
    else: target.write_bytes(payload)
    p=result['lower_price'];e=p['expected_price'];i=result['interface']
    print(json.dumps(dict(sha256=hashlib.sha256(payload).hexdigest(),
      necessary_visits=p['inversion']['necessary_integer_visits_lower'],
      expected_bus_lower=float(e['protection_read_bus_fraction_lower']),
      expected_core_lower=float(e['protection_read_core_fraction_lower']),
      finalize_budget_ns=float(i['timing']['post_fresh_finalize_invert_install_budget_lower_ns']),
      full_decisions_upper=i['counts']['full_decisions_upper'],
      complete_C=i['witnesses']['complete_two_ERR']['C'],wire_only_complete=False,
      counter_error_budget=None,old_Q_recomputed=False),indent=2))
