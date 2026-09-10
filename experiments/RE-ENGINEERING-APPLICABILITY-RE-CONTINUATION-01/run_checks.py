"""Run only this continuation. Never import or write accepted experiment packages."""
import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
import numerical_checks
import protocol_checks

ROOT=Path(__file__).resolve().parent

def main():
    cfg=json.loads((ROOT/'config.json').read_text())
    num=numerical_checks.run(cfg)
    protocol=protocol_checks.run(cfg)
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    (out/'numerical_checks.json').write_text(json.dumps(num,indent=2)+'\n')
    result=dict(task=cfg['task'],executed_at_utc=datetime.now(timezone.utc).isoformat(),input_commit=cfg['input_commit'],
        executor=cfg['executor'],python=sys.version,platform=platform.platform(),
        tool_paths={x:shutil.which(x) for x in ['git','iverilog','verilator','yosys','vivado']},
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ROOT.iterdir()) if p.suffix=='.py' or p.name=='config.json'},
        checks=protocol,all_checks_passed=all(r['passed'] for r in protocol),
        numerical_assertions_passed=True,large_MC_run=False,RTL_run=False,
        synthesis_or_placement=False,scientific_PASS=False,
        environment_note='ChatGPT container; no claim of access to user PC or full private checkout')
    (out/'execution_record.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':len(protocol),'passed':result['all_checks_passed'],
        'backup_cases':num['backup_cases'],'threshold':num['rate_threshold'],
        'tools':result['tool_paths']},indent=2))

if __name__=='__main__': main()
