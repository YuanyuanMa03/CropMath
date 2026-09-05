#!/usr/bin/env python3
"""Validate the CropMath Hugging Face release package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


EXPECTED = {
    "default": {"dev": 252, "test": 751, "gold": 95},
    "eval_prompts": {"dev": 1512, "test": 4506, "gold": 570},
}
EXPECTED_HIDDEN_PUBLIC = 160
CONDITIONS = {"C", "K_name", "K_formula", "K_domain", "K_distractor", "K_wrong"}
PUBLIC_CONTENT_SUFFIXES = {".json", ".jsonl", ".csv", ".yaml", ".yml"}
FORBIDDEN_PUBLIC_CONTENT = {
    "specific framework name": re.compile(
        r"RiceGrow|CH4MOD|AgroC|\bSIMPLE\b|\bDSSAT\b|\bAPSIM\b|"
        r"\bWOFOST\b|\bORYZA\b|\bDNDC\b|\bCENTURY\b|\bDayCent\b|"
        r"\bCERES\b|\bAquaCrop\b|\bSTICS\b|\bEPIC\b"
    ),
    "source-code wording": re.compile(
        r"source[ -]?code|codebase|源代码|源码|代码溯源|代码实现|代码位置",
        re.IGNORECASE,
    ),
    "implementation file reference": re.compile(
        r"(?:^|[\s'\"])(?:src|scripts)/[^\s'\"]+|\b[^\s/]+\.(?:py|R)\b",
        re.IGNORECASE,
    ),
    "generated citation": re.compile(
        r"\bet\s+al\.?\b|\bdoi\s*:|https?://|\bcited in\b|\bcitation\b",
        re.IGNORECASE,
    ),
}

# Code-area scan: catches model-name and provenance leaks in the public repo's
# Python/Markdown sources. Unlike FORBIDDEN_PUBLIC_CONTENT this does NOT reject
# legitimate ``.py`` references (code files legitimately live in the repo) and
# does NOT reject generic URLs (eval scripts reference model hubs); it focuses
# on the specific residue that would reveal the private formula provenance.
REPO_ROOT_SCAN_DIRS = ("src", "evaluation", "scripts", "tests")
REPO_ROOT_SCAN_FILES = ("README.md", "AGENTS.md")
REPO_ROOT_CODE_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".sh"}
REPO_ROOT_FORBIDDEN = {
    "specific framework name": re.compile(
        r"RiceGrow|CH4MOD|AgroC|\bSIMPLE crop\b|\bSIMPLE model\b|"
        r"\bDSSAT\b|\bAPSIM\b|\bWOFOST\b|\bORYZA\b|\bDNDC\b|"
        r"\bCENTURY\b|\bDayCent\b|\bCERES\b|\bAquaCrop\b|\bSTICS\b|\bEPIC\b"
    ),
    "provenance citation in code": re.compile(
        r"\b(?:Tang|Huang|Herbst|Zhao)\s+(?:19|20)\d{2}\b|"
        r"\bfrom\s+(?:CH4MOD|RiceGrow|AgroC)\s+code\b|"
        r"\bCommon\.R\b|\bfunc_[A-Za-z][A-Za-z0-9_]+",
        re.IGNORECASE,
    ),
    "implementation file reference": re.compile(
        r"\bcropmath\.formulas\b|\bcropmath\.generator\b|"
        r"\b[^\s/]+\.R\b",
        re.IGNORECASE,
    ),
}
# Files that legitimately encode the forbidden patterns as a *defense* (the
# validator itself and the clean-release builder, both of which carry the
# blocklist). Scanned but whitelisted by relative path so the defense keeps
# working without false positives.
REPO_ROOT_SCAN_ALLOWLIST = {
    "scripts/validate_cropmath_release.py",
    "scripts/build_clean_public_release.py",
}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def require(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def validate_public_content(release_dir: Path) -> list[str]:
    """Reject private implementation and citation residue in public data files."""
    issues: list[str] = []
    for path in sorted(release_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in PUBLIC_CONTENT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in FORBIDDEN_PUBLIC_CONTENT.items():
            match = pattern.search(text)
            if match:
                relative = path.relative_to(release_dir)
                issues.append(f"{relative}: {label}: {match.group(0)!r}")
    return issues


def validate_repo_root_content(repo_root: Path) -> list[str]:
    """Reject private provenance residue in the public repo's own source files.

    Scans ``src/``, ``evaluation/``, ``scripts/``, ``tests/`` plus top-level
    markdown for crop-model names, paper-year citations, and implementation
    references that would reveal the private formula provenance. The validator
    itself is allowlisted so its defensive blocklist keeps working.
    """
    issues: list[str] = []
    candidates: list[Path] = []
    for name in REPO_ROOT_SCAN_DIRS:
        directory = repo_root / name
        if directory.is_dir():
            for path in directory.rglob("*"):
                if path.is_file() and path.suffix.lower() in REPO_ROOT_CODE_SUFFIXES:
                    candidates.append(path)
    for name in REPO_ROOT_SCAN_FILES:
        path = repo_root / name
        if path.is_file():
            candidates.append(path)
    for path in sorted(candidates):
        try:
            relative = path.relative_to(repo_root).as_posix()
        except ValueError:
            relative = str(path)
        if relative in REPO_ROOT_SCAN_ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in REPO_ROOT_FORBIDDEN.items():
            match = pattern.search(text)
            if match:
                issues.append(f"{relative}: {label}: {match.group(0)!r}")
    return issues


def validate_jsonl(release_dir: Path) -> list[str]:
    issues: list[str] = []
    rows: dict[tuple[str, str], list[dict]] = {}
    for config, split_counts in EXPECTED.items():
        for split, expected_n in split_counts.items():
            path = release_dir / "data" / config / f"{split}.jsonl"
            require(path.exists(), f"missing file: {path}", issues)
            if not path.exists():
                continue
            data = load_jsonl(path)
            rows[(config, split)] = data
            ids = [row["id"] for row in data]
            require(len(data) == expected_n, f"{config}/{split}: {len(data)} rows, expected {expected_n}", issues)
            require(len(ids) == len(set(ids)), f"{config}/{split}: duplicate IDs", issues)
            require(all(row.get("answer") not in (None, "") for row in data), f"{config}/{split}: missing answer", issues)
            if config == "eval_prompts":
                require(all(row.get("prompt") for row in data), f"{config}/{split}: missing prompt", issues)
                require({row.get("condition") for row in data} <= CONDITIONS, f"{config}/{split}: invalid condition", issues)

    dev_ids = {row["id"] for row in rows.get(("default", "dev"), [])}
    test_ids = {row["id"] for row in rows.get(("default", "test"), [])}
    gold_ids = {row["id"] for row in rows.get(("default", "gold"), [])}
    require(not (dev_ids & test_ids), "default/dev and default/test overlap", issues)
    require(gold_ids <= test_ids, "default/gold is not a subset of default/test", issues)

    for split in ["dev", "test", "gold"]:
        default_ids = {row["id"] for row in rows.get(("default", split), [])}
        eval_rows = rows.get(("eval_prompts", split), [])
        eval_sample_ids = [row["sample_id"] for row in eval_rows]
        require(set(eval_sample_ids) == default_ids, f"eval_prompts/{split}: sample IDs do not match default/{split}", issues)
        for sample_id in default_ids:
            sample_conditions = {row["condition"] for row in eval_rows if row["sample_id"] == sample_id}
            require(sample_conditions == CONDITIONS, f"eval_prompts/{split}: {sample_id} does not have all six conditions", issues)

    hidden_path = release_dir / "hidden_public" / "hidden_public.jsonl"
    require(hidden_path.exists(), "missing hidden public file", issues)
    if hidden_path.exists():
        hidden_rows = load_jsonl(hidden_path)
        hidden_ids = {row["id"] for row in hidden_rows}
        require(len(hidden_rows) == EXPECTED_HIDDEN_PUBLIC, f"hidden_public: {len(hidden_rows)} rows, expected {EXPECTED_HIDDEN_PUBLIC}", issues)
        require(len(hidden_rows) == len(hidden_ids), "hidden_public: duplicate IDs", issues)
        require(not (hidden_ids & (dev_ids | test_ids | gold_ids)), "hidden_public overlaps dev/test/gold IDs", issues)
        forbidden = {"answer", "solution", "effective_parameters", "answer_float"}
        leaked = [row["id"] for row in hidden_rows if forbidden & set(row)]
        require(not leaked, f"hidden_public leaks answer-bearing fields: {leaked[:5]}", issues)
        require(all(row.get("answer_hidden") is True for row in hidden_rows), "hidden_public rows must set answer_hidden=true", issues)
        bad_sensitivity = [row["id"] for row in hidden_rows if row.get("mode") == "sensitivity" and not row.get("change")]
        require(not bad_sensitivity, f"hidden_public sensitivity rows missing change: {bad_sensitivity[:5]}", issues)

    private_markers = list(release_dir.rglob("*private*")) + list(release_dir.rglob("*answer*.jsonl"))
    leaked_private = [str(path.relative_to(release_dir)) for path in private_markers if "hidden_public" not in str(path)]
    require(not leaked_private, f"private answer-like files found in public release: {leaked_private}", issues)

    return issues


def validate_hf_loader(release_dir: Path) -> list[str]:
    try:
        from datasets import load_dataset
    except ImportError:
        return ["datasets is not installed; HF loader validation requires this dependency"]

    issues: list[str] = []
    for config, split_counts in EXPECTED.items():
        dataset = load_dataset(str(release_dir), config)
        observed = {split: len(dataset[split]) for split in split_counts}
        if observed != split_counts:
            issues.append(f"HF loader {config}: {observed}, expected {split_counts}")
    hidden_dataset = load_dataset(str(release_dir), "hidden_public")
    hidden_observed = len(hidden_dataset["hidden_public"])
    if hidden_observed != EXPECTED_HIDDEN_PUBLIC:
        issues.append(f"HF loader hidden_public: {hidden_observed}, expected {EXPECTED_HIDDEN_PUBLIC}")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate CropMath release/cropmath-v1")
    parser.add_argument("--release-dir", default="release/cropmath-v1")
    parser.add_argument("--skip-hf-loader", action="store_true")
    parser.add_argument(
        "--no-scan-repo-root",
        dest="scan_repo_root",
        action="store_false",
        default=True,
        help="Skip scanning the public repo source tree for provenance residue.",
    )
    args = parser.parse_args()

    release_dir = Path(args.release_dir).resolve()
    repo_root = release_dir.parents[1] if release_dir.name == "cropmath-v1" else Path.cwd().resolve()
    try:
        release_label = str(release_dir.relative_to(Path.cwd().resolve()))
    except ValueError:
        release_label = str(Path(args.release_dir))
    issues = validate_jsonl(release_dir)
    issues.extend(validate_public_content(release_dir))
    repo_root_issues: list[str] = []
    if args.scan_repo_root:
        repo_root_issues = validate_repo_root_content(repo_root)
    hf_issues = [] if args.skip_hf_loader else validate_hf_loader(release_dir)
    all_hard_issues = issues + repo_root_issues + hf_issues

    report = {
        "release_dir": release_label,
        "jsonl_pass": not issues,
        "hf_loader_pass": None if args.skip_hf_loader else not hf_issues,
        "repo_root_scan_pass": None if not args.scan_repo_root else not repo_root_issues,
        "issues": issues + repo_root_issues,
        "hf_loader_issues": hf_issues,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if all_hard_issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
