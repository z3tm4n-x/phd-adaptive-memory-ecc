"""Statistics and source-matched GOST convolution of the verified profile cache."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import tempfile
import time
import numpy as np
from transport import HERE, CFG, Response
from gost import summary as gost_summary
from analysis import analyze


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--with-helium",action="store_true")
    args=ap.parse_args()
    start=time.perf_counter()
    cache=Path(os.environ.get("SEPEM_CACHE",str(Path(tempfile.gettempdir())/"sepem-profile-derived-cache")))
    meta=json.loads((cache/"cache_manifest.json").read_text())
    if meta["config_sha256"]!=hashlib.sha256((HERE/"config.json").read_bytes()).hexdigest():
        raise ValueError("Cache configuration mismatch")
    for p,sha in meta["code_sha256"].items():
        if hashlib.sha256((HERE/p).read_bytes()).hexdigest()!=sha:
            raise ValueError("Cache implementation mismatch: "+p)
    out=HERE/"outputs"
    response=Response()
    for name,upper in (("csda_3_cut289",289.2),("csda_3_cut1000",1000.)):
        e,w=response.quadratures["csda_3_pdi"]
        response.quadratures[name]=(e[e<upper],w[e<upper])
    normative=gost_summary(response,CFG["mission_mean_events"])
    (out/"gost_convolution.json").write_text(json.dumps(normative,indent=2)+"\n")
    cfg=dict(CFG)
    cfg["gost"]=normative["gost"]
    cfg["monte_carlo_missions"]=CFG["bootstrap_missions"]
    cfg["mission_seed"]=CFG["bootstrap_seed"]
    rates={k:np.load(cache/(k+".npy"),mmap_mode="r") for k in meta["rate_keys"]}
    if args.with_helium:
        from helium import compute_helium
        he=compute_helium(Path(os.environ["SEPEM_RDS_V2"]),cache,meta["n"])
        extra,helium_meta=he["arrays"],he["metadata"]
        rates["csda_3_pdi_plus_He_model"]=rates["csda_3_pdi"]+extra["helium_3"]
        rates["csda_2p5_pdi_plus_He_model"]=rates["csda_2p5_pdi"]+extra["helium_2p5"]
        if "helium_3_tail250" in extra:
            rates["csda_3_pdi_plus_He_tail250_model"]=rates["csda_3_pdi"]+extra["helium_3_tail250"]
        (out/"helium_manifest.json").write_text(json.dumps(helium_meta,indent=2)+"\n")
    integrals=np.load(cache/"integral_flux.npy",mmap_mode="r")
    times=np.datetime64(meta["first_bin_start"],"s")+np.arange(meta["n"])*np.timedelta64(300,"s")
    result=analyze(times,rates,integrals,out,cfg)
    run={"elapsed_seconds":time.perf_counter()-start,"python":platform.python_version(),
         "platform":platform.platform(),"profile_cache":str(cache),"helium_enabled":args.with_helium,
         "scientific_status":"conditional model, not a replacement R0-A environment envelope"}
    try:
        import psutil
        mem=psutil.Process().memory_info()
        run["peak_process_working_set_bytes"]=getattr(mem,"peak_wset",None)
        run["final_rss_bytes"]=mem.rss
    except ImportError:
        run["memory_measurement"]="psutil unavailable"
    (out/"statistics_run.json").write_text(json.dumps(run,indent=2)+"\n")
    print(json.dumps({"run":run,"nominal_B":result["mission_model_B"]["order_statistic_interval"]},indent=2))


if __name__ == "__main__":
    main()
