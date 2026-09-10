# RE-CY62167-DIRECT-FLOOR-KILLTEST-01

This is a pre-W conservative kill test. `K>=2` is not an ECC failure statement; the only retained inequality is `p_D(E,W) <= P(K>=2|E)`.

For E<0.9 MeV the conservative representative scenario uses P(K>=2)=0.0129539, the maximum raw observed value over 0.9-3 MeV; this is not a confidence bound.

## Nominal results

|sigma|Al mm|q_M period|r_M median s^-1|r_M p99 s^-1|r_M peak s^-1|tau background|tau peak|E<0.9 bit fraction|peak|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
|main_loglog|0|0.8493%|4.8181e-03|5.9788e-01|9.2813e+01|207.5s|0.01077s|44.220%|2026-01-19T19:30:00+00:00|
|main_loglog|1|0.7844%|1.4481e-06|2.6939e-03|4.5413e-01|6.905e+05s|2.202s|33.184%|2026-01-19T19:20:00+00:00|
|main_loglog|2|0.8151%|1.1312e-06|7.6932e-04|9.8896e-02|8.84e+05s|10.11s|32.787%|2026-01-19T19:20:00+00:00|
|main_loglog|3|0.8316%|8.8334e-07|4.1803e-04|4.9674e-02|1.132e+06s|20.13s|32.705%|2026-01-19T19:20:00+00:00|
|main_loglog|5|0.8871%|7.1152e-07|1.3202e-04|1.2984e-02|1.405e+06s|77.02s|32.201%|2026-01-19T19:15:00+00:00|
|main_loglog|7|0.8870%|6.9873e-07|7.5089e-05|7.2112e-03|1.431e+06s|138.7s|32.304%|2026-01-19T19:15:00+00:00|
|main_loglog|10|0.9793%|6.8243e-07|3.0000e-05|2.6507e-03|1.465e+06s|377.3s|32.369%|2026-01-19T19:15:00+00:00|
|published_rpp_fluka_digitized|0|0.8603%|5.4734e-03|6.7584e-01|1.0476e+02|182.7s|0.009546s|44.996%|2026-01-19T19:30:00+00:00|
|published_rpp_fluka_digitized|1|0.7953%|1.4065e-06|2.9949e-03|5.0525e-01|7.11e+05s|1.979s|35.239%|2026-01-19T19:20:00+00:00|
|published_rpp_fluka_digitized|2|0.8171%|1.0617e-06|8.3519e-04|1.0821e-01|9.419e+05s|9.241s|35.002%|2026-01-19T19:20:00+00:00|
|published_rpp_fluka_digitized|3|0.8304%|7.8924e-07|4.5176e-04|5.4189e-02|1.267e+06s|18.45s|34.942%|2026-01-19T19:20:00+00:00|
|published_rpp_fluka_digitized|5|0.8707%|5.9973e-07|1.4050e-04|1.3875e-02|1.667e+06s|72.07s|34.653%|2026-01-19T19:15:00+00:00|
|published_rpp_fluka_digitized|7|0.8713%|5.8785e-07|8.0513e-05|7.7678e-03|1.701e+06s|128.7s|34.718%|2026-01-19T19:15:00+00:00|
|published_rpp_fluka_digitized|10|0.9485%|5.7317e-07|3.2018e-05|2.8808e-03|1.745e+06s|347.1s|34.680%|2026-01-19T19:15:00+00:00|

## Maximum actual-window F_D^upper

|sigma|Al mm|5min|1h|24h|7d|
|---|---:|---:|---:|---:|---:|
|main_loglog|0|100.0000%|100.0000%|100.0000%|100.0000%|
|main_loglog|1|100.0000%|100.0000%|100.0000%|100.0000%|
|main_loglog|2|100.0000%|100.0000%|100.0000%|100.0000%|
|main_loglog|3|100.0000%|100.0000%|100.0000%|100.0000%|
|main_loglog|5|97.9662%|100.0000%|100.0000%|100.0000%|
|main_loglog|7|88.5063%|100.0000%|100.0000%|100.0000%|
|main_loglog|10|54.8508%|99.9254%|100.0000%|100.0000%|
|published_rpp_fluka_digitized|0|100.0000%|100.0000%|100.0000%|100.0000%|
|published_rpp_fluka_digitized|1|100.0000%|100.0000%|100.0000%|100.0000%|
|published_rpp_fluka_digitized|2|100.0000%|100.0000%|100.0000%|100.0000%|
|published_rpp_fluka_digitized|3|100.0000%|100.0000%|100.0000%|100.0000%|
|published_rpp_fluka_digitized|5|98.4430%|100.0000%|100.0000%|100.0000%|
|published_rpp_fluka_digitized|7|90.2738%|100.0000%|100.0000%|100.0000%|
|published_rpp_fluka_digitized|10|57.8627%|99.9602%|100.0000%|100.0000%|

## Sensitivity

False-MCU: `{"min_relative": -0.0733671873288465, "max_relative": -0.0020078029340280246, "max_abs_relative": 0.0733671873288465}`
Raw observed interpolation: `{"min_relative": -0.013573330913552506, "max_relative": 0.010797270073969134, "max_abs_relative": 0.013573330913552506}`
Sigma model: `{"min_relative": -0.16072693375449953, "max_relative": 0.14107541934063783, "max_abs_relative": 0.16072693375449953}`
Low-energy multiplicity: `{"min_relative": 0.017482115360663464, "max_relative": 2.5470676564200487, "max_abs_relative": 2.5470676564200487}`

## Answers

1. `q_M` is spectrum-weighted under the energy integral and is reconstructed, not a measured sigma_k.
2. Absolute `r_M(t,d)` is stored in `weighted_parent_event_rate.csv` for the nominal conservative branch.
3. `tau_D^upper=1/r_M` is reported for background, p95, p99 and peak.
4. NHPP `F_D^upper` is swept over 5 min, 1 h, 6 h, 24 h, 7 d, 30 d and the valid Jan-Feb exposure.
5. Geometry/W/M1 is necessary if disposition B, because only W can reduce `P(K>=2|E)` to the true direct probability.

## Validation

Task-2 bit-rate reconstruction max rel: `4.965e-08`
Multiplicity invariants: `True`
Nonnegative rates: `True`

## Disposition: **B**

At least one requested actual reporting window has upper NHPP hazard >=1; direct risk cannot be dismissed without W/geometry.

No ECC, F_A or T_scrub calculation was performed.
