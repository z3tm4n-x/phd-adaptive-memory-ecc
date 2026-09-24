"""Read-only T31 integrity/syntax/arithmetic audit; no scientific simulations.

Run from the repository root. Verifies staged Git blobs, including CRLF, against
their exact source commits. A normal committed checkout has the same index.
"""
import ast
import hashlib
import io
import json
from fractions import Fraction
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def entries(ref, path):
    result = {}
    for record in git("ls-tree", "-r", "-z", ref, "--", path).split(b"\0"):
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, kind, sha = metadata.decode().split()
        if kind != "blob":
            raise AssertionError((path, kind))
        result[name.decode()] = (mode, sha)
    assert result, (ref, path)
    return result


def main():
    spec = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    selections = spec["selections"] + [
        {"source_sha": "3fd5d792a0dd55ee9d46c0b7ca46c72d4eba5ea2",
         "path": "manuscripts/internal-count-method-01"},
        {"source_sha": "5e75ab9979b7573ffb95cd8211baa4237e65bb93",
         "path": "experiments/RE-INTERNAL-COUNT-COSRAD-GOES-01"},
    ]
    staged = {}
    for record in git("ls-files", "--stage", "-z").split(b"\0"):
        if record:
            metadata, name = record.split(b"\t", 1)
            mode, sha, stage = metadata.decode().split()
            assert stage == "0", "Unresolved index conflict"
            staged[name.decode()] = (mode, sha)
    audited = {}
    groups = []
    newline_only = []
    counts = {"python_syntax": 0, "json_syntax": 0, "zip_crc": 0}
    for row in selections:
        source = entries(row["source_sha"], row["path"])
        for path, identity in source.items():
            assert staged.get(path) == identity, ("Git identity mismatch", path)
            if path in audited:
                assert audited[path] == identity
                continue
            audited[path] = identity
            payload = git("cat-file", "blob", identity[1])
            working = (ROOT / path).read_bytes()
            if working != payload:
                assert working.replace(b"\r\n", b"\n") == payload.replace(b"\r\n", b"\n"), ("Working bytes differ", path)
                newline_only.append(path)
            if path.endswith(".py"):
                ast.parse(payload.decode("utf-8-sig"), filename=path)
                counts["python_syntax"] += 1
            elif path.endswith(".json"):
                json.loads(payload.decode("utf-8-sig"))
                counts["json_syntax"] += 1
            elif path.endswith((".zip", ".npz")):
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    assert archive.testzip() is None, path
                counts["zip_crc"] += 1
        groups.append({**row, "verified_files": len(source)})
    protected = {}
    for path in ["results", "docs/dissertation_concept.md",
                 "experiments/RE-INTERNAL-COUNT-CONTROL-01",
                 "experiments/RE-INTERNAL-COUNT-UNKNOWN-D-01",
                 "experiments/RE-GOES-REAL-TEMPORAL-01"]:
        for name, identity in entries(spec["base_sha"], path).items():
            assert staged.get(name) == identity, ("Protected file changed", name)
            protected[name] = identity
    preserved_base = entries(spec["base_sha"], ".")
    permitted_updates = {"STATUS.md", "experiments/t31-working-set/README.md"}
    for name, identity in preserved_base.items():
        if name not in permitted_updates:
            assert staged.get(name) == identity, ("Unexpected baseline edit", name)
    external_sources = {
        "external/chapter4-risk-limited-scrubber": "cf7ab706224f7872fdafcf34febda70e3f6c8dd1",
        "external/chapter4-rate-burst-stress": "76a4ed5b0622625e3e7a40b3b9d9f79b5ea2a1ee",
    }
    for path, sha in external_sources.items():
        assert staged.get(path) == ("160000", sha), ("Submodule pin drift", path)
        actual = subprocess.check_output(["git", "-C", str(ROOT / path), "rev-parse", "HEAD"], text=True).strip()
        assert actual == sha, ("Initialize pinned submodule", path)
        assert not subprocess.check_output(["git", "-C", str(ROOT / path), "status", "--porcelain"]), path
    words = 2 ** 20
    slot = Fraction(300, 10 ** 9)
    passage = words * slot
    period_min = passage / Fraction(25, 10000)
    assert passage == Fraction("0.3145728")
    assert period_min == Fraction("125.82912")
    arithmetic = {"words": words, "useful_bytes": words * 4,
                  "active_bits": words * 39, "physical_bits": words * 48,
                  "unused_bits": words * 9, "dense_pass_s": float(passage),
                  "min_period_full_slot_reservation_s": float(period_min),
                  "meaning": "Exact project arithmetic, not reliability or WCET evidence"}
    # Check byte contracts used by GOES16 without loading or running its model.
    manifest = json.loads((ROOT / "experiments/RE-INTERNAL-COUNT-GOES16-VALIDATION-01/input_manifest.json").read_text())
    upstream = manifest["pipeline_hashes"]
    assert upstream, "Missing GOES16 byte contract"
    upstream_checks = []
    if upstream:
        for path, digest in upstream.items():
            payload = git("cat-file", "blob", staged[path][1])
            upstream_checks.append({"path": path,
                                    "git_bytes_match": hashlib.sha256(payload).hexdigest() == digest,
                                    "working_bytes_match": hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest})
            assert upstream_checks[-1]["git_bytes_match"], ("Upstream Git bytes differ", path)
            assert upstream_checks[-1]["working_bytes_match"], ("Upstream working bytes differ", path)
    frozen_prereg = "870a3c5d725793dd45ff2cc2feaf6e8885df0df9"
    ancestry = subprocess.run(["git", "merge-base", "--is-ancestor", frozen_prereg, "HEAD"], cwd=ROOT).returncode
    assert ancestry in (0, 1)
    # The old COSRAD manifest covers delivery A, followed by two approved files.
    cosrad = ROOT / "experiments/RE-INTERNAL-COUNT-COSRAD-GOES-01"
    old_manifest = json.loads((cosrad / "provenance/package_manifest.json").read_text())
    for record in old_manifest["files"]:
        raw = (cosrad / record["path"]).read_bytes()
        assert len(raw) == record["bytes"]
        assert hashlib.sha256(raw).hexdigest() == record["sha256"], record["path"]
    expected_extra = {"delivery_b/PI_TRAINING_WINDOW_AMENDMENT_2024_05.md",
                      "delivery_b/training_window_override.json"}
    actual = {str(p.relative_to(cosrad)).replace("\\", "/") for p in cosrad.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    extra = actual - {r["path"] for r in old_manifest["files"]} - {"provenance/package_manifest.json"}
    assert extra == expected_extra, extra
    print(json.dumps({"scope": "T31 integration only; no new scientific acceptance",
                      "verified_source_files": len(audited), "protected_files": len(protected),
                      "baseline_files_preserved_except_named_docs": len(preserved_base) - len(permitted_updates),
                      "external_sources": external_sources,
                      "checks": counts, "groups": groups,
                      "checkout_newline_only": newline_only,
                      "r0_arithmetic": arithmetic,
                      "cosrad_original_manifest_files_valid": len(old_manifest["files"]),
                      "cosrad_original_verifier_extra_paths": sorted(extra),
                      "goes16_prereg_is_head_ancestor": ancestry == 0,
                      "goes16_upstream_contract": upstream_checks}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
