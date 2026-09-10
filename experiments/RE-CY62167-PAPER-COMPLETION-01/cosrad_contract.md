# PI COSRAD contract

Phase A does not run COSRAD. `cosrad_input_cross_sections.csv` contains deterministic mappings `W_MIN_REGISTERED_DIRECT=W_01_02`, `W_ARTICLE_BASELINE=W_00_01`, `W_MAX_REGISTERED_DIRECT=W_00_11`, each at nine heavy-ion LET points. `CURRENT_CLEAN` equals `ARTICLE_COMPAT` for P_HI and is not duplicated.

Units: LET in MeV cm^2/mg; all cross sections in cm^2; returned rates in s^-1. Direct and accumulation populations are disjoint. `F_art=S/(2^24 sigma_b)` is ARTICLE-NORMALIZED EFFECTIVE FLUENCE, not independently measured fluence. `sigma_direct_article_upper95_cm2`, when present, is ARTICLE-CONFIDENCE-STYLE EFFECTIVE-FLUENCE NORMALIZATION and not established as a normative experimental 95% confidence bound.

PI must document interpolation/step/extrapolation used by COSRAD between or outside the nine LET support points.

Minimum PI return for Phase B:
`shield_g_cm2,mapping_id,estimate_type,nu_direct_s-1,nu_accumulation_bit_s-1`, with `estimate_type=POINT` or `ARTICLE_CONFIDENCE_STYLE`, for 2.0, 2.5 and 3.0 g/cm^2.

For model-conditional reference calculations additionally return LET-resolved `shield_g_cm2,LET_MeV_cm2_mg,lambda_registered_event_s-1` or an equivalent registered-event mixture. Without this input use `TAU_MAX_REFERENCE_BLOCKED_BY_MISSING_EVENT_RATE_WEIGHTS`; do not invent a mark distribution.
