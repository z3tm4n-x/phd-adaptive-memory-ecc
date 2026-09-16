"""Front-end validation only. Requires pinned pyslang==9.1.0."""
import json, os
from pathlib import Path
import pyslang
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT) # pyslang Windows filename conversion: use ASCII relative paths.
c=pyslang.Compilation()
for name in ("reference_slot.sv","reference_schedule.sv"):
    c.addSyntaxTree(pyslang.SyntaxTree.fromFile(name))
diagnostics=c.getAllDiagnostics()
result={"tool":"pyslang","version":pyslang.__version__,"diagnostics":[
    {"code":str(d.code),"error":d.isError(),"location":str(d.location)} for d in diagnostics],
    "status":"PASS" if not diagnostics else "REVIEW_DIAGNOSTICS",
    "scope":"syntax and semantic elaboration only; NOT simulation, synthesis, STA or formal equivalence"}
print(json.dumps(result,indent=2))
assert not diagnostics
