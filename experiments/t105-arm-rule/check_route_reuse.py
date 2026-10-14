"""The software-only continuation does not reuse STA for changed RTL."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    report=json.loads((HERE/'outputs/full-top.json').read_text())
    names=('arm_board_top.sv','arm_executor.sv','arm_physical_top.sv','history_batch.sv',
           'rule_mailbox.sv','interval_guard.sv','interval_link.sv','full_top.tcl','ps_delivery.tcl')
    matched={}
    for name in names:
        digest=hashlib.sha256((HERE/name).read_bytes()).hexdigest()
        assert digest==report['source_hashes']['t105-arm-rule/'+name],name
        matched[name]=digest
    result={'kind':'hash identity of all new production sources/top recipe, not a new route',
      'routed_delivery':'a477950890020cd27845c9a27170efad29dac4b7',
      'matched_sha256':matched,'old_B_sources':'unchanged accepted sources, Git diff checked at delivery',
      'excluded':'simulation-only tb_arm.sv, integration_sim.tcl and new test harnesses'}
    (HERE/'outputs/route-reuse.json').write_text(json.dumps(result,indent=2)+'\n');print('Unchanged route inputs:',len(matched))
if __name__=='__main__':main()
