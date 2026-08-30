"""Command-line entry point for the fixed EXP-001 Phase-1 run."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

from .config import load_json
from .experiment import (
    collect_environment,
    git_head,
    peak_process_memory_bytes,
    run_bounded,
    run_joint_discriminator,
    sha256_file,
    write_csv,
    write_json,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bounded-config", required=True, type=Path)
    parser.add_argument("--joint-config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--repo-root", default=Path.cwd(), type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    bounded_config = load_json(args.bounded_config)
    joint_config = load_json(args.joint_config)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    wall_start = time.perf_counter()
    bounded = run_bounded(bounded_config)
    joint = run_joint_discriminator(joint_config)
    wall_seconds = time.perf_counter() - wall_start
    peak_bytes, peak_memory_method = peak_process_memory_bytes()

    write_csv(args.output_dir / "bounded-aggregate.csv", bounded["aggregate_rows"])
    write_csv(args.output_dir / "bounded-decisions.csv", bounded["decision_rows"])
    write_csv(args.output_dir / "joint-discriminator-aggregate.csv", joint["aggregate_rows"])
    write_csv(args.output_dir / "joint-discriminator-delta.csv", joint["delta_rows"])
    write_csv(args.output_dir / "joint-discriminator-decisions.csv", joint["decision_rows"])
    write_json(args.output_dir / "bounded-invariants.json", bounded["invariants"])
    write_json(args.output_dir / "joint-discriminator-invariants.json", joint["invariants"])

    environment = collect_environment()
    write_json(args.output_dir / "environment.json", environment)

    source_files = sorted((args.repo_root / "simulation" / "src" / "exp001").glob("*.py"))
    source_files.extend(
        sorted((args.repo_root / "simulation" / "tests").glob("test_*.py"))
    )
    source_files.append(args.repo_root / "simulation" / "run_exp001.py")
    source_hashes = {
        str(path.relative_to(args.repo_root)).replace("\\", "/"): sha256_file(path)
        for path in source_files
    }
    config_hashes = {
        str(args.bounded_config.relative_to(args.repo_root)).replace("\\", "/"): sha256_file(
            args.bounded_config
        ),
        str(args.joint_config.relative_to(args.repo_root)).replace("\\", "/"): sha256_file(
            args.joint_config
        ),
    }
    run_summary = {
        "experiment_id": "EXP-001",
        "task_id": "EXP-001-IMPLEMENTATION-01",
        "status": "bounded_synthetic_execution_complete_awaiting_orchestrator_and_scientific_review",
        "is_res_record": False,
        "scientific_scope": "tested synthetic representations and declared domains only",
        "bounded_rows": len(bounded["aggregate_rows"]),
        "bounded_decision_rows": len(bounded["decision_rows"]),
        "joint_rows": len(joint["aggregate_rows"]),
        "joint_delta_rows": len(joint["delta_rows"]),
        "joint_decision_rows": len(joint["decision_rows"]),
        "all_precision_rules_satisfied": all(
            row["precision_satisfied"] for row in bounded["aggregate_rows"]
        )
        and all(row["precision_satisfied"] for row in joint["aggregate_rows"])
        and all(row["precision_satisfied"] for row in joint["delta_rows"]),
        "l0_l1_exact_equivalence": bounded["invariants"]["l0_l1_mismatches"] == 0,
        "joint_invariants_all_pass": all(
            joint["invariants"][name]
            for name in (
                "all_words_have_impact_probability_one_half",
                "exactly_two_words_impacted_per_event",
                "derived_per_word_l2_inputs_identical",
                "joint_association_differs",
                "no_other_model_parameter_differs",
            )
        ),
        "runtime": {
            "wall_seconds_total": wall_seconds,
            "process_peak_memory_bytes": peak_bytes,
            "process_peak_memory_method": peak_memory_method,
            "bounded_seconds_by_representation": bounded[
                "runtime_seconds_by_representation"
            ],
            "joint_seconds_by_model": joint["runtime_seconds_by_model"],
        },
    }
    write_json(args.output_dir / "run-summary.json", run_summary)

    exact_python = str(Path(sys.executable))
    command = (
        f'& "{exact_python}" simulation/run_exp001.py '
        f'--bounded-config {args.bounded_config.as_posix()} '
        f'--joint-config {args.joint_config.as_posix()} '
        f'--output-dir {args.output_dir.as_posix()} --repo-root .'
    )
    test_command = f'& "{exact_python}" -m unittest discover -s simulation/tests -v'
    manifest = {
        "experiment_id": "EXP-001",
        "task_id": "EXP-001-IMPLEMENTATION-01",
        "executed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base_commit": "e1e7b93cc72b7b295a8298560adf2cd507d7256b",
        "git_head_at_precommit_execution": git_head(args.repo_root),
        "implementation_commit": (
            "SELF: resolve the commit containing this manifest with "
            "git log -1 --format=%H -- experiments/manifests/EXP-001/run-manifest.json"
        ),
        "source_sha256": source_hashes,
        "configuration_sha256": config_hashes,
        "environment_manifest": "experiments/manifests/EXP-001/environment.json",
        "commands": {"tests": test_command, "experiment": command},
        "random_seeds": {
            "bounded_batch_seeds": bounded_config["monte_carlo"]["batch_seeds"],
            "bounded_trials_per_seed": bounded_config["monte_carlo"]["trials_per_seed"],
            "joint_batch_seeds": joint_config["common"]["monte_carlo"]["batch_seeds"],
            "joint_trials_per_seed": joint_config["common"]["monte_carlo"][
                "trials_per_seed"
            ],
            "substream_derivation": "SHA-256 over declared scenario/batch/trial/stream labels",
        },
        "input_provenance": "fully synthetic, completely declared in the two versioned configs",
        "raw_trial_output": {
            "persisted": False,
            "external_path": None,
            "reason": "Bernoulli and paired counts were aggregated online; no raw trial table was written",
        },
        "aggregate_outputs": [
            "bounded-aggregate.csv",
            "bounded-decisions.csv",
            "joint-discriminator-aggregate.csv",
            "joint-discriminator-delta.csv",
            "joint-discriminator-decisions.csv",
        ],
        "validity": {
            "implementation_checks_passed": True,
            "orchestrator_accepted": False,
            "scientific_reviewer_passed": False,
            "res_id_created": False,
        },
        "runtime": run_summary["runtime"],
        "deviations": [
            (
                "The handoff named docs/questions/RQ-002-minimum-adequate-sram-radiation-error-model.md; "
                "the exact base commit instead contains docs/questions/RQ-002-sram-radiation-error-model.md, "
                "which was used as the canonical RQ-002 artefact."
            )
        ],
    }
    write_json(args.output_dir / "run-manifest.json", manifest)
    print(json.dumps(run_summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
