#!/usr/bin/env python3
"""Validate CropMath model-result JSONL files before statistical analysis."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path


CONDITIONS = ["C", "K_name", "K_formula", "K_domain", "K_distractor", "K_wrong"]


def parse_condition_from_stem(stem: str) -> tuple[str, str | None]:
    for condition in sorted(CONDITIONS, key=len, reverse=True):
        suffix = f"_{condition}"
        if stem.endswith(suffix):
            return stem[: -len(suffix)], condition
    return stem, None


def main() -> None:
    parser = argparse.ArgumentParser(description="Check model-condition result completeness")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--expected-rows", type=int, default=751)
    parser.add_argument("--require-all-conditions", action="store_true")
    parser.add_argument("--formal-config", action="store_true", help="Require the deterministic A100 core-model generation protocol")
    parser.add_argument(
        "--prompt-style",
        help="Only validate rows with this prompt_style, for example baseline_cot or formula_audit",
    )
    parser.add_argument(
        "--include-auxiliary-prompt-styles",
        action="store_true",
        help="With --formal-config, include non-baseline prompt styles instead of treating them as auxiliary runs",
    )
    parser.add_argument("--hidden-aggregate", action="store_true", help="Validate aggregate-only hidden summary files")
    args = parser.parse_args()

    issues: list[str] = []
    if args.hidden_aggregate:
        for file_text in args.files:
            path = Path(file_text)
            data = json.loads(path.read_text(encoding="utf-8"))
            if any(key in data for key in ["rows", "predictions", "responses"]):
                issues.append(f"{path}: hidden aggregate must not include row-level predictions/responses")
            for field in ["model_tag", "hidden_samples", "accuracy", "correct", "data_sha256"]:
                if field not in data:
                    issues.append(f"{path}: missing aggregate field {field}")
        report = {"files": len(args.files), "pass": not issues, "issues": issues}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if issues:
            raise SystemExit(1)
        return

    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    skipped_auxiliary = 0

    for file_text in args.files:
        path = Path(file_text)
        stem_model, stem_condition = parse_condition_from_stem(path.stem)
        with path.open(encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                model = row.get("model_tag") or stem_model
                condition = row.get("condition") or stem_condition
                if condition not in CONDITIONS:
                    issues.append(f"{path}:{line_num}: invalid/missing condition {condition}")
                    continue
                prompt_style = row.get("prompt_style")
                if args.prompt_style and prompt_style != args.prompt_style:
                    skipped_auxiliary += 1
                    continue
                if (
                    args.formal_config
                    and not args.prompt_style
                    and not args.include_auxiliary_prompt_styles
                    and prompt_style
                    and prompt_style != "baseline_cot"
                ):
                    skipped_auxiliary += 1
                    continue
                cells[(model, condition)].append(row)

    for (model, condition), rows in sorted(cells.items()):
        ids = [row.get("id") for row in rows]
        unique_ids = set(ids)
        if len(rows) != args.expected_rows:
            issues.append(f"{model}/{condition}: {len(rows)} rows, expected {args.expected_rows}")
        if len(unique_ids) != len(ids):
            issues.append(f"{model}/{condition}: duplicate item IDs")
        missing_fields = [
            field
            for field in [
                "data_sha256",
                "prompt_sha256",
                "sample_sha256",
                "response_sha256",
                "generation_config",
                "input_tokens",
                "output_tokens",
                "model_config_sha256",
                "tokenizer_config_sha256",
            ]
            if any(field not in row for row in rows)
        ]
        if missing_fields:
            issues.append(f"{model}/{condition}: missing reproducibility fields {missing_fields}")
        if args.formal_config:
            for index, row in enumerate(rows, 1):
                config = row.get("generation_config")
                if not isinstance(config, dict):
                    issues.append(f"{model}/{condition}: row {index} generation_config is not an object")
                    continue
                expected_config = {
                    "max_new_tokens": 2048,
                    "temperature": 0.0,
                    "thinking_mode": "off",
                    "torch_dtype": "bf16",
                }
                for field, expected in expected_config.items():
                    actual = config.get(field)
                    if actual != expected:
                        issues.append(
                            f"{model}/{condition}: row {index} generation_config.{field}={actual!r}, expected {expected!r}"
                        )
                if config.get("do_sample") is not False:
                    issues.append(f"{model}/{condition}: row {index} generation_config.do_sample must be false")

    if args.require_all_conditions:
        models = {model for model, _ in cells}
        for model in sorted(models):
            observed = {condition for cell_model, condition in cells if cell_model == model}
            missing = sorted(set(CONDITIONS) - observed)
            if missing:
                issues.append(f"{model}: missing conditions {missing}")

    report = {
        "cells": len(cells),
        "expected_rows": args.expected_rows,
        "skipped_auxiliary_rows": skipped_auxiliary,
        "pass": not issues,
        "issues": issues,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
