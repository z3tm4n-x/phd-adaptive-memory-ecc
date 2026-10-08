"""Numerical refinement diagnostic, distinct from physical qualification."""
import json
import numpy as np
from transport import Response, ENERGY, HERE


def main():
    # Chosen spectra before profile statistics; curved/nonmonotone cases
    # exercise interpolation, not only exact power laws.
    spectra=np.array([(ENERGY/10)**(-p)*np.exp(-ENERGY/350) for p in (0,1.5,3,6)] +
                     [np.array([1,2,3,2,1,.8,.1,.01,.004,.001,.002])])
    coarse=Response(order=12,slope_step=.02,hermite_order=15)
    fine=Response(order=24,slope_step=.01,hermite_order=31)
    a,fa,_=coarse.calculate(spectra)
    b,fb,_=fine.calculate(spectra)
    rows=[]
    for key in a:
        for i,(x,y) in enumerate(zip(a[key],b[key])):
            rows.append({"variant":key,"spectrum_index":i,"coarse":float(x),
                         "fine":float(y),"relative_change":float(abs(x-y)/y)})
    maximum=max(r["relative_change"] for r in rows)
    from helium import HeliumResponse, ENERGY as HE_ENERGY
    he_spectra=np.array([np.ones(8),(HE_ENERGY/38.03)**-3,
                         [0.,0.,.1,.2,.1,0.,.01,.001]])
    he_a=HeliumResponse(order=12).calculate(he_spectra)
    he_b=HeliumResponse(order=24).calculate(he_spectra)
    helium={k:{"order12":he_a[k].tolist(),"order24":he_b[k].tolist(),
               "relative_delta":(abs(he_a[k]-he_b[k])/he_b[k]).tolist()} for k in he_a}
    he_max=max(max(x["relative_delta"]) for x in helium.values())
    # 0.1% is a predeclared numerical diagnostic threshold, not a bound on
    # response, time binning, solar-population or missing species uncertainty.
    result={"cases":rows,"maximum_relative_change":maximum,"criterion":.001,
            "passed":max(maximum,he_max)<=.001,"integral_flux_exact_across_refinement":bool(np.array_equal(fa,fb)),
            "helium_ASTAR_LET_refinement":helium,"helium_maximum_relative_change":he_max,
            "scope":"numerical refinement diagnostic; not an interval proof or physical qualification",
            "lookup_analytic_bound":coarse.metadata()["lookup_relative_error_bound"]}
    (HERE/"outputs/numerical_checks.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="cases"}))
    if not result["passed"]:
        raise SystemExit("Numerical refinement criterion failed; do not silently accept")


if __name__=="__main__":
    main()
