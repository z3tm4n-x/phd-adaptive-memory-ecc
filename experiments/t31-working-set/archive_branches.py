"""Archive the published pre-v2.2 branches without changing existing refs.

Default: read-only plan. --apply: create missing tags, then verify the server.
The active T0 branch is excluded explicitly. No branch is moved or deleted.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import subprocess


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def remote_refs():
    return {ref: sha for sha, ref in
            (line.split() for line in git("ls-remote", "--heads", "--tags", "origin").splitlines())}


def planned_tags(snapshot):
    wanted = {}
    for row in snapshot["branches"]:
        branch, tag, sha = row["branch"], row["tag"], row["sha"]
        if (not branch.startswith("refs/heads/")
                or branch == snapshot["excluded_active_branch"]
                or tag != "refs/tags/v1/" + branch.removeprefix("refs/heads/")
                or tag in wanted or not re.fullmatch("[0-9a-f]{40}", sha)):
            raise ValueError("Invalid or duplicate archive target")
        wanted[tag] = sha
    if wanted.get("refs/tags/v1/main") != snapshot["base_sha"]:
        raise ValueError("Archive base does not match main snapshot")
    wanted["refs/tags/v1-archive"] = snapshot["base_sha"]
    return wanted


def missing_tags(refs, wanted):
    for ref, sha in wanted.items():
        if ref in refs and refs[ref] != sha:
            raise ValueError(f"Existing tag differs: {ref}; will not overwrite")
    return {ref: sha for ref, sha in wanted.items() if ref not in refs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify", type=Path,
                        help="Verify a saved snapshot, without changing refs or files")
    args = parser.parse_args()
    refs = remote_refs()
    if args.verify:
        snapshot = json.loads(args.verify.read_text(encoding="utf-8"))
        failures = []
        moved = []
        for row in snapshot["branches"]:
            if refs.get(row["tag"]) != row["sha"]:
                failures.append(row["tag"])
            if refs.get(row["branch"]) != row["sha"]:
                moved.append(row["branch"])
        if refs.get("refs/tags/v1-archive") != snapshot["base_sha"]:
            failures.append("refs/tags/v1-archive")
        print(json.dumps({"tags_checked": len(snapshot["branches"]) + 1,
                          "tag_failures": failures,
                          "branches_changed_since_snapshot": moved}, indent=2))
        raise SystemExit(bool(failures))

    targets = json.loads(Path(__file__).with_name("archive_targets.json").read_text(encoding="utf-8"))
    expected_base = targets["base_sha"]
    excluded = targets["excluded_active_branch"]
    rows = targets["branches"]
    wanted = planned_tags(targets)
    path = Path(__file__).with_name("archive_snapshot.json")
    if args.apply and path.exists():
        raise SystemExit("STOP: snapshot exists; not overwriting it")
    if refs.get("refs/heads/main") != expected_base:
        raise SystemExit("STOP: main changed; reassess the archive baseline")
    for row in rows:
        if refs.get(row["branch"]) != row["sha"]:
            raise SystemExit(f"STOP: branch changed: {row['branch']}")
    missing = missing_tags(refs, wanted)
    for ref, sha in wanted.items():
        git("check-ref-format", ref)
        git("cat-file", "-e", sha + "^{commit}")
    print(json.dumps({"branches": len(rows), "tags_to_create": len(missing),
                      "excluded": excluded, "apply": args.apply}, indent=2))
    if not args.apply:
        return
    fresh = remote_refs()
    if fresh != refs:
        raise SystemExit("STOP: remote refs changed after planning; retry after inspection")
    # Explicit refspecs and atomic push: no force, wildcard, or branch update.
    if missing:
        subprocess.run(["git", "push", "--atomic", "origin",
                        *(sha + ":" + ref for ref, sha in missing.items())], check=True)
    verified = remote_refs()
    for ref, sha in wanted.items():
        if verified.get(ref) != sha:
            raise SystemExit(f"STOP: server tag verification failed: {ref}")
    changed = [row["branch"] for row in rows
               if verified.get(row["branch"]) != row["sha"]]
    snapshot = {
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository": "z3tm4n-x/phd-adaptive-memory-ecc",
        "base_sha": expected_base,
        "excluded_active_branch": excluded,
        "branches": rows,
        "branches_changed_during_archival": changed,
        "server_tags_verified": True,
    }
    path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(wanted)} tags; snapshot: {path}")
    if changed:
        raise SystemExit("STOP: branch changed during archival; snapshot requires inspection")


if __name__ == "__main__":
    main()
