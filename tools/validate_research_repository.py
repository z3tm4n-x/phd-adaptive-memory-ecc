#!/usr/bin/env python3
"""Conservative repository-integrity checks for research artefacts.

Checks structure and research metadata only; never infers or changes scientific
state. Legacy permanent artefacts without metadata are warnings, not errors.
Metadata v1 supports only top-level scalar fields and scalar lists.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

ID_RE = re.compile(r"\b(?:RQ|PAPER|CLM|EVD|HYP|DEC|EXP|RES|FIG|ART)-\d{3}\b")
FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.S)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
RESEARCH_META_RE = re.compile(r"(?m)^(?:schema_version|artifact_type)\s*:")

DIR_TYPES = {
    "docs/questions": "RQ",
    "docs/decisions": "DEC",
    "docs/claims": "CLM",
    "docs/hypotheses": "HYP",
    "docs/paper_cards": "PAPER",
    "results": "RES",
    "experiments": "EXP",
}
REVIEW_DIR = "docs/scientific_reviews"
ARTEFACT_TYPES = set(DIR_TYPES.values()) | {"EVD", "FIG", "ART", "SCIENTIFIC_REVIEW"}

FIELD_ENUMS = {
    ("RQ", "lifecycle"): {"OPEN", "ANSWERED", "CLOSED_NO_ANSWER", "SUPERSEDED"},
    ("CLM", "lifecycle"): {"ACTIVE", "SUPERSEDED", "WITHDRAWN"},
    ("CLM", "evidence_assessment"): {
        "SUPPORTED", "PARTIALLY_SUPPORTED", "DISPUTED", "INSUFFICIENT", "NOT_VERIFIED"
    },
    ("HYP", "lifecycle"): {"ACTIVE", "SUPERSEDED", "RETIRED"},
    ("HYP", "assessment"): {"UNTESTED", "TESTING", "SUPPORTED", "REJECTED", "INCONCLUSIVE"},
    ("DEC", "lifecycle"): {"ACTIVE", "SUPERSEDED", "REVOKED"},
    ("RES", "lifecycle"): {"ACCEPTED", "SUPERSEDED", "INVALIDATED"},
    ("SCIENTIFIC_REVIEW", "recommendation"): {"PASS", "PASS_WITH_MINOR", "REVISE", "BLOCK"},
}
EXP_ENUMS = {
    "implementation": {"PLANNED", "IMPLEMENTED", "INVALIDATED"},
    "reproduction": {"NOT_RUN", "REPRODUCED", "MISMATCH", "NOT_APPLICABLE"},
    "independent_validation": {"NOT_RUN", "PARTIAL", "PASS", "FAIL", "NOT_APPLICABLE"},
    "independent_falsification": {"YES", "PARTIAL", "NO", "NOT_APPLICABLE"},
    "scientific_review": {"NOT_REVIEWED", "PASS", "PASS_WITH_MINOR", "REVISE", "BLOCK"},
    "promotion": {"NOT_ELIGIBLE", "RES_ELIGIBLE", "PROMOTED"},
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: Path
    message: str


@dataclass
class Doc:
    path: Path
    text: str
    meta: dict[str, Any] | None

    @property
    def id(self) -> str | None:
        value = self.meta.get("id") if self.meta else None
        return value.strip() if isinstance(value, str) and value.strip() else None


def in_dir(rel: str, base: str) -> bool:
    return rel == base or rel.startswith(base + "/")


def md_files(root: Path) -> Iterable[Path]:
    ignored = {".git", ".venv", "venv", "node_modules", "__pycache__"}
    for path in root.rglob("*.md"):
        if not any(part in ignored for part in path.parts):
            yield path


def expected_type(path: Path, root: Path) -> str | None:
    rel = path.relative_to(root).as_posix()
    if in_dir(rel, REVIEW_DIR):
        return "SCIENTIFIC_REVIEW"
    return next((typ for base, typ in DIR_TYPES.items() if in_dir(rel, base)), None)


def legacy_id(path: Path, root: Path) -> str | None:
    rel = path.relative_to(root).as_posix()
    typ = expected_type(path, root)
    if typ is None or typ == "SCIENTIFIC_REVIEW" or rel.startswith("experiments/manifests/"):
        return None
    pattern = re.compile(rf"\b{typ}-\d{{3}}\b")
    ids = list(dict.fromkeys(pattern.findall(path.name)))
    if len(ids) == 1:
        return ids[0]
    head = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:8])
    ids = list(dict.fromkeys(pattern.findall(head)))
    return ids[0] if len(ids) == 1 else None


def filename_id(path: Path, typ: str) -> str | None:
    if typ == "SCIENTIFIC_REVIEW":
        return None
    ids = list(dict.fromkeys(re.findall(rf"\b{typ}-\d{{3}}\b", path.name)))
    return ids[0] if len(ids) == 1 else None


def permanent(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    upper = path.name.upper()
    if path.name.startswith("README") or "DRAFT" in upper or "CANDIDATE" in upper:
        return False
    if rel.startswith("experiments/manifests/"):
        return False
    typ = expected_type(path, root)
    return typ == "SCIENTIFIC_REVIEW" or legacy_id(path, root) is not None


def scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return None
    if value == "[]":
        return []
    if value.lower() in {"null", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith("[") and value.endswith("]"):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            inner = value[1:-1].strip()
            return [] if not inner else [x.strip().strip("'\"") for x in inner.split(",")]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value[1:-1]
    return value


def parse_research_front(path: Path, text: str, force: bool) -> tuple[dict[str, Any] | None, list[Finding]]:
    match = FRONT_RE.match(text)
    if not match:
        return None, []
    block = match.group(1)
    if not force and not RESEARCH_META_RE.search(block):
        return None, []  # ordinary documentation front matter is outside this validator

    data: dict[str, Any] = {}
    list_key: str | None = None
    try:
        for line_no, raw in enumerate(block.splitlines(), 1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            stripped = raw.strip()
            indent = len(raw) - len(raw.lstrip(" "))
            if stripped.startswith("- "):
                if indent <= 0 or list_key is None:
                    raise ValueError(f"line {line_no}: list item has no parent key")
                if data[list_key] is None:
                    data[list_key] = []
                if not isinstance(data[list_key], list):
                    raise ValueError(f"line {line_no}: mixed scalar/list for {list_key}")
                data[list_key].append(scalar(stripped[2:]))
                continue
            if indent or ":" not in raw:
                raise ValueError(
                    f"line {line_no}: metadata v1 permits top-level 'key: value' and scalar lists only"
                )
            key, value = raw.split(":", 1)
            key = key.strip()
            if not key or key in data:
                raise ValueError(f"line {line_no}: empty or duplicate key {key!r}")
            data[key] = scalar(value)
            list_key = key if data[key] is None else None
        for key, value in list(data.items()):
            if value is None:
                data[key] = []
        return data, []
    except ValueError as exc:
        return None, [Finding("ERROR", "METADATA_INVALID", path, str(exc))]


def load_docs(root: Path) -> tuple[list[Doc], list[Finding]]:
    docs: list[Doc] = []
    findings: list[Finding] = []
    for abs_path in md_files(root):
        rel = abs_path.relative_to(root)
        text = abs_path.read_text(encoding="utf-8", errors="replace")
        force = permanent(abs_path, root)
        meta, errors = parse_research_front(rel, text, force)
        docs.append(Doc(rel, text, meta))
        findings.extend(errors)
    return docs, findings


def identity(doc: Doc, root: Path) -> str | None:
    return doc.id or legacy_id(root / doc.path, root)


def known_ids(docs: list[Doc], root: Path) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    for doc in docs:
        ident = identity(doc, root)
        if ident:
            result.setdefault(ident, []).append(doc.path)
    return result


def list_field(meta: dict[str, Any], field: str) -> list[str]:
    value = meta.get(field, [])
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [x for x in value if isinstance(x, str)]
    return []


def metadata_checks(docs: list[Doc], root: Path) -> list[Finding]:
    out: list[Finding] = []
    for doc in docs:
        abs_path = root / doc.path
        if permanent(abs_path, root) and doc.meta is None:
            out.append(Finding(
                "WARNING", "LEGACY_METADATA_MISSING", doc.path,
                "permanent artefact has no research metadata; gradual migration is allowed"
            ))
            continue
        if doc.meta is None:
            continue

        meta = doc.meta
        typ = meta.get("artifact_type")
        ident = meta.get("id")
        path_type = expected_type(abs_path, root)

        if meta.get("schema_version") != 1:
            out.append(Finding("ERROR", "SCHEMA_VERSION", doc.path, "schema_version must be 1"))
        if typ not in ARTEFACT_TYPES:
            out.append(Finding("ERROR", "ARTIFACT_TYPE", doc.path, f"invalid artifact_type {typ!r}"))
            continue
        if path_type and typ != path_type:
            out.append(Finding(
                "ERROR", "PATH_TYPE_MISMATCH", doc.path,
                f"path implies {path_type}, metadata says {typ}"
            ))

        if typ == "SCIENTIFIC_REVIEW":
            if not isinstance(ident, str) or not ident.strip():
                out.append(Finding("ERROR", "ARTIFACT_ID", doc.path, "review record id required"))
        else:
            if not isinstance(ident, str) or not ID_RE.fullmatch(ident):
                out.append(Finding("ERROR", "ARTIFACT_ID", doc.path, f"invalid id {ident!r}"))
            elif not ident.startswith(typ + "-"):
                out.append(Finding(
                    "ERROR", "ID_TYPE_MISMATCH", doc.path,
                    f"id {ident} does not match artifact_type {typ}"
                ))
            file_ident = filename_id(abs_path, typ)
            if file_ident and isinstance(ident, str) and ident != file_ident:
                out.append(Finding(
                    "ERROR", "FILENAME_ID_MISMATCH", doc.path,
                    f"filename identifies {file_ident}, metadata identifies {ident}"
                ))

        for (enum_type, field), allowed in FIELD_ENUMS.items():
            if typ == enum_type and field in meta and meta[field] not in allowed:
                out.append(Finding(
                    "ERROR", "ENUM_VALUE", doc.path,
                    f"{field}={meta[field]!r}; expected one of {sorted(allowed)}"
                ))

        if typ == "EXP":
            required = {
                "implementation", "reproduction", "independent_validation",
                "scientific_review", "promotion"
            }
            missing = sorted(required - meta.keys())
            if missing:
                out.append(Finding(
                    "ERROR", "EXP_METADATA_INCOMPLETE", doc.path,
                    "missing: " + ", ".join(missing)
                ))
            for field, allowed in EXP_ENUMS.items():
                if field in meta and meta[field] not in allowed:
                    out.append(Finding(
                        "ERROR", "ENUM_VALUE", doc.path,
                        f"{field}={meta[field]!r}; expected one of {sorted(allowed)}"
                    ))
            if (
                meta.get("promotion") in {"RES_ELIGIBLE", "PROMOTED"}
                and meta.get("scientific_review") not in {"PASS", "PASS_WITH_MINOR"}
            ):
                out.append(Finding(
                    "ERROR", "EXP_PROMOTION_WITHOUT_PASS", doc.path,
                    "RES_ELIGIBLE/PROMOTED requires scientific_review PASS or PASS_WITH_MINOR"
                ))

        if typ == "RES":
            if "lifecycle" not in meta:
                out.append(Finding("ERROR", "RES_LIFECYCLE_MISSING", doc.path, "lifecycle required"))
            if not meta.get("derived_from"):
                out.append(Finding("ERROR", "RES_NO_PROVENANCE", doc.path, "derived_from required"))
            if not (meta.get("scientific_review") or meta.get("review")):
                out.append(Finding("ERROR", "RES_NO_REVIEW", doc.path, "review provenance required"))
    return out


def duplicate_checks(docs: list[Doc], root: Path) -> list[Finding]:
    out: list[Finding] = []
    for ident, paths in sorted(known_ids(docs, root).items()):
        unique = sorted(set(paths))
        if len(unique) > 1:
            out.append(Finding(
                "ERROR", "DUPLICATE_ID", unique[0],
                f"{ident}: " + ", ".join(map(str, unique))
            ))
    return out


def supersession_checks(docs: list[Doc], root: Path) -> list[Finding]:
    out: list[Finding] = []
    ids = set(known_ids(docs, root))
    metadata_docs = {doc.id: doc for doc in docs if doc.meta and doc.id}
    graph: dict[str, list[str]] = {}

    for doc in docs:
        if not doc.meta or not doc.id:
            continue
        supersedes = list_field(doc.meta, "supersedes")
        superseded_by = list_field(doc.meta, "superseded_by")
        graph[doc.id] = supersedes

        for field, targets in (("supersedes", supersedes), ("superseded_by", superseded_by)):
            for target in targets:
                if target not in ids:
                    out.append(Finding(
                        "ERROR", "RELATION_TARGET_MISSING", doc.path,
                        f"{field} target does not exist: {target}"
                    ))
        for target in supersedes:
            other = metadata_docs.get(target)
            if other and doc.id not in list_field(other.meta or {}, "superseded_by"):
                out.append(Finding(
                    "WARNING", "SUPERSESSION_RECIPROCITY", doc.path,
                    f"{doc.id} supersedes {target}, but {target} does not declare superseded_by: {doc.id}"
                ))
        for target in superseded_by:
            other = metadata_docs.get(target)
            if other and doc.id not in list_field(other.meta or {}, "supersedes"):
                out.append(Finding(
                    "WARNING", "SUPERSESSION_RECIPROCITY", doc.path,
                    f"{doc.id} says superseded_by {target}, but {target} does not declare supersedes: {doc.id}"
                ))

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, stack: list[str]) -> None:
        if node in visiting:
            start = stack.index(node) if node in stack else 0
            cycle = stack[start:] + [node]
            path = metadata_docs[node].path if node in metadata_docs else Path(".")
            out.append(Finding("ERROR", "SUPERSESSION_CYCLE", path, " -> ".join(cycle)))
            return
        if node in visited:
            return
        visiting.add(node)
        for target in graph.get(node, []):
            if target in graph:
                visit(target, stack + [node])
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node, [])
    return out


def link_checks(root: Path) -> list[Finding]:
    out: list[Finding] = []
    for path in md_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw in LINK_RE.findall(text):
            target = raw.strip().split()[0].strip("<>")
            if not target or target.startswith("#") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            resolved = root / target.lstrip("/") if target.startswith("/") else path.parent / target
            if not resolved.resolve().exists():
                out.append(Finding(
                    "ERROR", "BROKEN_LINK", path.relative_to(root),
                    f"target does not exist: {raw}"
                ))
    return out


def draft_checks(root: Path) -> list[Finding]:
    out: list[Finding] = []
    for path in md_files(root):
        upper = path.name.upper()
        if "DRAFT" not in upper and "CANDIDATE" not in upper:
            continue
        ids = ID_RE.findall(path.name)
        if ids:
            out.append(Finding(
                "WARNING", "DRAFT_PERMANENT_ID", path.relative_to(root), ", ".join(ids)
            ))
    return out


def run(root: Path) -> list[Finding]:
    docs, out = load_docs(root)
    out += metadata_checks(docs, root)
    out += duplicate_checks(docs, root)
    out += supersession_checks(docs, root)
    out += link_checks(root)
    out += draft_checks(root)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    root = Path(parser.parse_args(argv).root).resolve()
    if not (root / "README.md").exists():
        print(f"ERROR ROOT_NOT_REPOSITORY {root}", file=sys.stderr)
        return 1

    findings = run(root)
    order = {"ERROR": 0, "WARNING": 1}
    findings.sort(key=lambda f: (order.get(f.severity, 9), str(f.path), f.code, f.message))
    for finding in findings:
        print(f"{finding.severity} {finding.code} {finding.path}: {finding.message}")

    errors = sum(f.severity == "ERROR" for f in findings)
    warnings = sum(f.severity == "WARNING" for f in findings)
    print(f"\nSummary: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
