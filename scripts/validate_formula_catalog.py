#!/usr/bin/env python3
"""Validate CropMath clean formula catalog metadata."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re


REQUIRED_FIELDS = [
    "formula_id",
    "family",
    "name_en",
    "unit",
    "precision",
    "expression",
    "latex",
    "math_type",
    "sample_count",
]

EXPECTED_FORMULAS = 62
PUBLIC_ID_RE = re.compile(r"CMF\d{3}")
PUBLIC_CATEGORIES = {
    "growth_yield",
    "carbon_nitrogen_cycle",
    "methane_emission",
    "environmental_response",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate clean formula catalog table")
    parser.add_argument("--path", default="release/cropmath-v1/metadata/formula_catalog.csv")
    args = parser.parse_args()

    path = Path(args.path)
    issues: list[str] = []
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    ids = [row.get("formula_id", "") for row in rows]
    if len(ids) != len(set(ids)):
        issues.append("duplicate formula_id rows")
    if len(ids) != EXPECTED_FORMULAS:
        issues.append(f"formula count {len(ids)}, expected {EXPECTED_FORMULAS}")
    invalid_ids = [formula_id for formula_id in ids if not PUBLIC_ID_RE.fullmatch(formula_id)]
    if invalid_ids:
        issues.append(f"invalid public formula IDs: {invalid_ids[:5]}")

    for row in rows:
        fid = row.get("formula_id", "")
        missing = [field for field in REQUIRED_FIELDS if not str(row.get(field, "")).strip()]
        if missing:
            issues.append(f"{fid}: missing required fields {missing}")
        if row.get("family") not in PUBLIC_CATEGORIES:
            issues.append(f"{fid}: invalid public category {row.get('family')!r}")

    report = {
        "path": str(path),
        "formulas": len(rows),
        "expected_formulas": EXPECTED_FORMULAS,
        "pass": not issues,
        "issues": issues,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
