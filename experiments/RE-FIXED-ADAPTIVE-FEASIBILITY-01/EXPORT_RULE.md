# EXPORT RULE — RE-FIXED-ADAPTIVE-FEASIBILITY-01

Purpose: close Scientific Review MINOR-02 by making the packaging layer explicit. This file does **not** change scientific numbers and does not replace the historical execution record.

Reviewed delivery: `03e6c4ad8570fa3351378c9c77b1f9c2fe943f15`.  
Scientific Review: `619492db33cb8793710fb4e454616f543993c982`.

## 1. Historical execution record remains historical

`outputs/execution_record.json`, current Git blob `2eee173da3ef1a29a3314c5d23c59e388eb4e6e8`, is preserved unchanged. It records an earlier execution state and is **not** the byte manifest of the post-repair/post-review package.

No SHA in that historical file is rewritten to make it appear to describe later files.

## 2. repair_checks.py raw outputs

Current `repair_checks.py` Git blob: `13472d61cd97115a663d7ddbf1bd567e225742af`.

Running `python repair_checks.py` writes three raw JSON files:

1. `outputs/repair_verification.json`;
2. `outputs/executor_schedule.json`;
3. `outputs/budget_domains.json`.

The published repair JSONs in reviewed commit `03e6c4ad…` are deliberate documentary projections of those raw structures, not literal raw-file copies.

## 3. Export projection: executor schedule

Raw source: `outputs/executor_schedule.json` from `repair_checks.py`.
Published file: `outputs/executor_schedule_repair.json`, current blob `bbf62e41e579fc037555afc9936f15787c3808d8`.

Rule:

- rename file `executor_schedule.json` -> `executor_schedule_repair.json`;
- copy every scalar scientific field unchanged;
- omit only the raw `trace` field, which contains 16 word-release records used for local checking;
- no numerical field is recomputed during export.

The omitted raw trace is therefore an **excluded diagnostic trace**, not missing scientific input.

## 4. Export projection: budget domains

Raw source: `outputs/budget_domains.json` from `repair_checks.py`.
Published file: `outputs/budget_domains_repair.json`, current blob `8f4371ff7b8c608c3e7e5632778dc8d893f78f17`.

Rule:

- rename file `budget_domains.json` -> `budget_domains_repair.json`;
- copy the three resource-domain numeric objects unchanged:
  - `nominal_warm_start`;
  - `fallback_148h_warm_start`;
  - `cold_start_plus_148h_fallback`;
- copy the machine-readable information-contract fields as documentary text;
- the published phrase in `information_contract.first_hour_warm_start` is a shortened manual annotation (`...; explicit assumption`) relative to the raw wording (`...; this is an explicit warm-start assumption`); this changes no numerical field.

After Scientific Review, the two warm-start rows are historical/non-certified for arbitrary initial estimates. Their preservation in this JSON is provenance, not limited acceptance.

## 5. Export projection: repair verification

Raw source: `outputs/repair_verification.json` written by `repair_checks.py` before packaging.
Published file: `outputs/repair_verification.json`, current blob `4e839ba9d3bc5a5b8113b985aa77327c26f58592`.

Projection rule:

- copy unchanged: `passed`, `semantic_checks`, `schedule_checks`, `semantic_check_count`, `schedule_check_count`;
- rename raw object `executor` -> published object `principal_executor`;
- from raw `executor`, publish these fields unchanged:
  - `release_spacing_s_at_peak`;
  - `scrub_grab_s`;
  - `app_word_max_s`;
  - `max_scrub_lateness_s`;
  - `rho_scrub_peak`;
  - `phase_integral_inflation_max`;
  - `risk_upper_with_word_boundary_lateness`;
  - `service_curve_delay_us`;
  - `busy_period_delay_us`;
- omit from this compact projection:
  - `application_sigma_service_s`;
  - `application_rho`;
  - `leftover_service_rate`;
  - `trace`;
- replace the nested raw `budget_domains` object with compact `resource_domains` scalar fields:
  - `nominal_warm_start_lower_fraction` <- `budget_domains.nominal_warm_start.lower_fraction`;
  - `fallback_148h_warm_start_lower_fraction` <- `budget_domains.fallback_148h_warm_start.lower_fraction`;
  - `cold_start_plus_148h_lower_fraction` <- `budget_domains.cold_start_plus_148h_fallback.lower_fraction`;
  - `fixed_separator_upper_fraction` <- the common `upper_fixed_separator_fraction`;
- add the manual documentary annotation `old_verify_dictionary_fixtures_are_semantic_evidence=false`.

No scientific field in this projection is recomputed.

## 6. Current independent-check bytes and verification records

Current reviewed bytes are identified by Git content IDs:

- `independent_check.py`: blob `090384581915943d3de9a252355957cd5b34d871`;
- `outputs/independent_check.json`: blob `d92c58710743358f932b4757de212d5eea86e52a`;
- frozen `outputs/verification.json`: blob `3e9061f3f433df9700a2df61c37a9e208b40b03e`;
- repair `outputs/repair_verification.json`: blob `4e839ba9d3bc5a5b8113b985aa77327c26f58592`.

`outputs/independent_check.json` is retained as the current output associated with the current `independent_check.py` bytes in the reviewed package. Its fallback sensitivity fields are historical/superseded and are **not** the selected post-SR cold-start acceptance metadata. The post-SR acceptance scope is recorded separately in `outputs/sr_disposition_cold_start.json`.

Scientific Review also reran `python independent_check.py` successfully and reported that all numerical results matched except the environment-dependent Python-version field. That reviewer rerun does not rewrite the historical RE output.

## 7. Manual annotations versus generated fields

Manual/documentary annotations in the packaged repair include:

- shortened information-contract prose described above;
- `old_verify_dictionary_fixtures_are_semantic_evidence=false`;
- filenames with `_repair` suffix;
- post-SR acceptance/status prose in the new disposition files.

These annotations are not presented as generated numerical results.

## 8. Reproduction meaning

The scientific fields are reproducible by:

1. using the reviewed source bytes;
2. running the recorded commands;
3. applying the explicit projection rules above.

This export rule explains the filename/schema differences noted by Scientific Review without changing `outputs/execution_record.json`, numerical results, or scientific assumptions.
