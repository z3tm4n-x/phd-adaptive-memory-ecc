"""Immutable local staging and retained provenance for the changed full top."""
import hashlib,json,os,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    build=HERE/".build"/("full-"+str(time.time_ns()));build.mkdir(parents=True)
    hashes={}
    for root in (HERE,HERE.parent/"t104-rtl-resume"):
        for src in root.rglob("*"):
            if any(x.startswith(".") or x=="outputs" for x in src.relative_to(root).parts):continue
            if src.suffix not in (".sv",".xdc",".tcl"):continue
            target=build/"source"/root.name/src.relative_to(root)
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(src.read_bytes())
            hashes[str(src.relative_to(HERE.parent))]=hashlib.sha256(src.read_bytes()).hexdigest()
    command=[os.environ.get("VIVADO","/home/z3tm4n/bin/vivado-wsl"),"-mode","batch","-nojournal","-nolog",
        "-source",str(build/"source/t105-arm-rule/full_top.tcl"),"-tclargs",str(build/"run")]
    print("BUILD",build,flush=True);before=time.monotonic()
    with (build/"vivado.log").open("w") as log:
        result=subprocess.run(command,cwd=build,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
    meta={"build":str(build),"source_hashes":hashes,"command":command,
          "returncode":result.returncode,"elapsed_s":time.monotonic()-before}
    (build/"manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps({k:v for k,v in meta.items() if k not in ("source_hashes","command")},indent=2))
    assert result.returncode==0,(build/"vivado.log").read_text()[-5000:]
    return build
if __name__=="__main__":main()
