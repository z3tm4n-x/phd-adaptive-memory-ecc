"""Capture package identities without editing any historical input."""
import hashlib,importlib.metadata,json,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    canonical=['docs/agents/00_GLOBAL_OPERATING_RULES.md','docs/agents/07_RESEARCH_ENGINEER_LOCAL.md','docs/agents/HANDOFF_CONTRACTS.md','docs/current_status.md','docs/research_spec.md','docs/decisions/DEC-004-dissertation-architecture-A.md','docs/dissertation_concept.md','results/RES-003-internal-count-control.md','experiments/RE-INTERNAL-COUNT-CONTROL-01/derivation.md','docs/scientific_reviews/INTERNAL_COUNT_CONTROL_REVIEW_01.md','docs/publication_plans/RES-003-PUBLICATION-HANDOFF.md']
    historical={}
    for relative in canonical:
        historical[relative]=dict(sha256=sha(REPO/relative),git_blob=subprocess.check_output(['git','rev-parse','268e0d772aa718226ce7d3c2c18ded96306bdcf2:'+relative],cwd=REPO,text=True).strip())
    artifacts={str(p.relative_to(ROOT)).replace('\\','/'):dict(sha256=sha(p),bytes=p.stat().st_size) for folder in ['inputs','outputs','figures'] for p in (ROOT/folder).glob('*') if p.is_file() and not (p.name.startswith('tune_') and p.suffix=='.npz') and p.name!='provenance.json'}
    code={p.name:sha(p) for p in ROOT.glob('*.py')}
    protected=[]
    changed=subprocess.check_output(['git','diff','--name-only'],cwd=REPO,text=True).splitlines()
    for relative in changed:
        if '/continuation-02/' in relative:continue
        old=subprocess.check_output(['git','show','268e0d772aa718226ce7d3c2c18ded96306bdcf2:'+relative],cwd=REPO)
        protected.append(dict(path=relative,raw_equal_to_base=old==(REPO/relative).read_bytes(),sha256=sha(REPO/relative)))
    result=dict(base='268e0d772aa718226ce7d3c2c18ded96306bdcf2',preregistration='c09928f2ad0e483539426ec2c0d20e84adbb3d86',pretest_execution_commit='8ed0035d8b75b43733d9dcce4473835031d21f49',python=sys.version,platform=platform.platform(),dependencies={p:importlib.metadata.version(p) for p in ['numpy','scipy','numba','llvmlite','matplotlib','psutil']},source_identities=historical,code_sha256=code,artifacts=artifacts,preexisting_out_of_scope_worktree_markers=protected)
    (ROOT/'outputs/provenance.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(f'{len(artifacts)} artifact hashes')

if __name__=='__main__':main()
