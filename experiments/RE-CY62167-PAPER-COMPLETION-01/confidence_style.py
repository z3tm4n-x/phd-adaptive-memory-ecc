from __future__ import annotations

ARTICLE_RELATIVE_FLUENCE_UNCERTAINTY = 0.10
ARTICLE_T_H_FOR_3 = 2.4
ARTICLE_OFFSET = 0.67
NORMATIVE_STATUS = "NOT ESTABLISHED AS NORMATIVE CONFIDENCE BOUND WITHOUT INDEPENDENT FLUENCE PROVENANCE"
GENERALIZATION_STATUS = "ARTICLE_CONFIDENCE_STYLE_GENERALIZATION_REQUIRES_PI_DECISION"


def article_direct_upper95_baseline(sigma_direct_point_cm2: float, direct_event_count: int):
    """Reproduce only the formula explicitly instantiated in the manuscript for N_D=3.

    Manuscript construction:
      sigma* = sigma_hat * t_H(0.95;3) * (3+0.67) / [3*(1-theta)]
    with t_H=2.4 and theta=0.10.
    """
    if direct_event_count != 3:
        return None, GENERALIZATION_STATUS
    result = (
        sigma_direct_point_cm2
        * ARTICLE_T_H_FOR_3
        * (3.0 + ARTICLE_OFFSET)
        / (3.0 * (1.0 - ARTICLE_RELATIVE_FLUENCE_UNCERTAINTY))
    )
    return result, "ARTICLE-CONFIDENCE-STYLE EFFECTIVE-FLUENCE NORMALIZATION"


def confidence_contract(result: float | None, direct_event_count: int):
    return {
        "direct_event_count": direct_event_count,
        "effective_fluence_definition": "F_art(L)=S(L)/(2^24*sigma_b(L)); ARTICLE-NORMALIZED EFFECTIVE FLUENCE",
        "fluence_is_independently_measured": False,
        "assumed_relative_fluence_uncertainty": ARTICLE_RELATIVE_FLUENCE_UNCERTAINTY,
        "confidence_coefficient": ARTICLE_T_H_FOR_3 if direct_event_count == 3 else None,
        "formula": "sigma_hat * 2.4 * (3+0.67) / (3*(1-0.10))" if direct_event_count == 3 else None,
        "result": result,
        "normative_status": NORMATIVE_STATUS,
    }
