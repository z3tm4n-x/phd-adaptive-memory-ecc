"""Reconstruct conditional primary-proton profiles; never publish raw RDS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import tempfile
import time
import numpy as np
import pandas as pd
from audit import input_files, digest
from transport import Response, HERE, CFG, REPO


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reuse-cache",action="store_true")
    ap.add_argument("--profiles-only",action="store_true")
    args=ap.parse_args()
    path=Path(os.environ["SEPEM_RDS_V2"])
    cache=Path(os.environ.get("SEPEM_CACHE",str(Path(tempfile.gettempdir())/"sepem-profile-derived-cache")))
    if cache.resolve() == REPO or REPO in cache.resolve().parents:
        raise ValueError("Cache must remain outside the Git checkout")
    cache.mkdir(parents=True,exist_ok=True)
    out=HERE/"outputs"
    out.mkdir(exist_ok=True)
    start=time.perf_counter()
    config_digest=hashlib.sha256((HERE/"config.json").read_bytes()).hexdigest()
    cache_meta=cache/"cache_manifest.json"
    if args.reuse_cache:
        meta=json.loads(cache_meta.read_text())
        if meta["config_sha256"]!=config_digest:
            raise ValueError("Cache configuration mismatch")
        for name,sha in meta["code_sha256"].items():
            if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=sha:
                raise ValueError("Cache code mismatch")
    else:
        response=Response()
        print("Response kernels ready",flush=True)
        expected=json.loads((out/"input_audit.json").read_text())
        ref=expected["reference_series"]["SEPEM_H_reference.txt"]
        if not ref["numerically_complete"]:
            raise ValueError("Input gaps require an explicit new policy")
        n=ref["records"]
        arrays=None
        offset=0
        diagnostics=[]
        with input_files(path) as files:
            candidates=[v for v in files if Path(v[0]).name=="SEPEM_H_reference.txt"]
            if len(candidates)!=1:
                raise ValueError("Exactly one H reference required")
            with candidates[0][2]() as stream:
                if digest(stream) != ref["sha256"]:
                    raise ValueError("Reference bytes differ from audited source")
            with candidates[0][2]() as stream:
                for chunk in pd.read_csv(stream,skiprows=1,header=None,chunksize=50000):
                    flux=chunk.iloc[:,1:].to_numpy(dtype=float)
                    rates,integrals,diag=response.calculate(flux)
                    diagnostics.append(diag)
                    if arrays is None:
                        arrays={k:np.lib.format.open_memmap(cache/(k+".npy"),mode="w+",dtype="float64",shape=(n,)) for k in rates}
                        ints=np.lib.format.open_memmap(cache/"integral_flux.npy",mode="w+",dtype="float64",shape=(n,4))
                    stop=offset+len(flux)
                    for key,value in rates.items():
                        arrays[key][offset:stop]=value
                    ints[offset:stop]=integrals
                    offset=stop
                    if offset%500000==0:
                        print(f"{offset}/{n} profiles",flush=True)
        if offset!=n:
            raise ValueError("Reference row count changed")
        for arr in arrays.values():
            arr.flush()
        ints.flush()
        meta={"config_sha256":config_digest,
              "code_sha256":{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in ("transport.py","pipeline.py")},
              "reference_sha256":ref["sha256"], "n":n,"first_bin_start":ref["first_bin_start"],
              "rate_keys":list(arrays),"response":response.metadata(),
              "diagnostics":{"slope_min":min(x["slope_min"] for x in diagnostics),
                             "slope_max":max(x["slope_max"] for x in diagnostics),
                             "tail_slope_limited_rows":sum(x["tail_slope_limited_rows"] for x in diagnostics)}}
        cache_meta.write_text(json.dumps(meta,indent=2)+"\n")
    print("Profiles ready; event analysis",flush=True)
    rates={k:np.load(cache/(k+".npy"),mmap_mode="r") for k in meta["rate_keys"]}
    integrals=np.load(cache/"integral_flux.npy",mmap_mode="r")
    times=np.datetime64(meta["first_bin_start"],"s")+np.arange(meta["n"])*np.timedelta64(300,"s")
    (out/"transport_manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
    if args.profiles_only:
        print("Profile cache complete; statistics not yet run",flush=True)
        return
    from analysis import analyze
    analyze(times,rates,integrals,out,CFG)
    (out/"pipeline_run.json").write_text(json.dumps({"python":platform.python_version(),
        "platform":platform.platform(),"elapsed_seconds":time.perf_counter()-start,
        "derived_cache_outside_git":str(cache),"scope":"conditional primary-proton profiles only"},indent=2)+"\n")


if __name__ == "__main__":
    main()
