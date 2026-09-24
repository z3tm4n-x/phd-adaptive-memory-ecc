"""Record immutable inputs, preserved Stage-0 bytes and package hashes."""
import hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
def git(*args):
    return subprocess.check_output(["git",*args],cwd=REPO)
def main():
    base="003c2346c4135b3d2f24dac0981e60cb2f179384"
    pinned="d59de85eb46ae1fa254f3b936ce6fa64c28bcff0"
    preserved={}
    for name in ("REPORT.md","HANDOFF.md","timing_input_gate.json","EXECUTION.md","MANIFEST.json"):
        path=(ROOT.parent/name).relative_to(REPO).as_posix()
        before=git("show",base+":"+path)
        after=(REPO/path).read_bytes()
        assert before==after,path
        preserved[path]={"base_sha256":hashlib.sha256(before).hexdigest(),"current_sha256":hashlib.sha256(after).hexdigest(),"byte_identical":True}
    sources={}
    for path in (
      "docs/research_gates/CY62167-REFERENCE-SUBSYSTEM-01.md",
      "docs/research_gates/CY62167-EXECUTOR-TIMING-STAGE0-DISPOSITION-01.md",
      "docs/research_gates/CY62167-COVERAGE-THRESHOLD-SR-DISPOSITION-01.md",
      "docs/agents/00_GLOBAL_OPERATING_RULES.md",
      "docs/agents/07_RESEARCH_ENGINEER_LOCAL.md",
      "docs/agents/HANDOFF_CONTRACTS.md"):
        raw=git("show",pinned+":"+path)
        sources[path]={"commit":pinned,"blob":git("rev-parse",pinned+":"+path).decode().strip(),"sha256":hashlib.sha256(raw).hexdigest()}
    crlf=[]
    for path in git("diff","--name-only").decode().splitlines():
        if not path.startswith("experiments/RE-CY62167-PAPER-COMPLETION-01/"): continue
        work=(REPO/path).read_bytes(); blob=git("show","HEAD:"+path)
        assert work==blob,("unrelated modification",path)
        crlf.append({"path":path,"raw_blob_equal":True,"sha256":hashlib.sha256(work).hexdigest()})
    files={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(ROOT.iterdir()) if x.is_file() and x.name!="MANIFEST.json"}
    tool_spec=json.loads((ROOT/"TOOLS.json").read_text())
    tool_root=ROOT.parents[3]/"tmp/iverilog"
    tool_hashes={}
    for item in tool_spec["archives"]:
        digest=hashlib.sha256((tool_root/item["local"]).read_bytes()).hexdigest()
        assert digest==item["sha256"],item["file"]
        tool_hashes[item["file"]]=digest
    manifest={"base":base,"additional_input":pinned,
      "preregistration_commit":git("rev-parse","2d349dc").decode().strip(),
      "package_hash_scope":"all sibling files except self; source pins/PDF bytes separately identified",
      "preserved_stage0":preserved,"canonical_inputs":sources,
      "unrelated_status_artifacts":crlf,"files_sha256":files,"verified_tool_archives":tool_hashes}
    (ROOT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("PASS: five Stage-0 files byte-identical; package and input hashes recorded.")
if __name__=="__main__": main()
