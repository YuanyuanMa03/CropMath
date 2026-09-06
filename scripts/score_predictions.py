#!/usr/bin/env python3
"""Score one model/run against a complete selected public split and conditions."""

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cropmath.answer_parser import extract_answer, is_correct
from cropmath.prompts import CONDITIONS


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Line {line_number}: expected a JSON object")
            rows.append(value)
    return rows


def score_predictions(reference, predictions, conditions):
    """Reject incomplete/ambiguous input; unparseable responses stay in denominator."""
    if not conditions or len(set(conditions)) != len(conditions) or set(conditions) - set(CONDITIONS):
        raise ValueError("Select distinct supported conditions")
    expected = {}
    samples = {condition: set() for condition in conditions}
    for row in reference:
        if row["condition"] not in conditions:
            continue
        if row["id"] in expected or row["sample_id"] in samples[row["condition"]]:
            raise ValueError("Duplicate reference ID or sample/condition pair")
        if not math.isfinite(row["answer_float"]):
            raise ValueError("Reference answer must be finite")
        expected[row["id"]] = row
        samples[row["condition"]].add(row["sample_id"])
    if not expected or any(not ids for ids in samples.values()):
        raise ValueError("Selected reference conditions must be nonempty")
    if any(ids != samples[conditions[0]] for ids in samples.values()):
        raise ValueError("Reference conditions must contain the same sample IDs")
    received = {}
    for row in predictions:
        identifier = row.get("id")
        if not isinstance(identifier, str) or identifier not in expected:
            raise ValueError("Unknown prediction ID (including unselected split/condition)")
        if identifier in received:
            raise ValueError("Duplicate prediction ID")
        if not isinstance(row.get("response"), str):
            raise ValueError("Each prediction requires a string response; use empty text for failed runs")
        received[identifier] = row["response"]
    missing = set(expected) - received.keys()
    if missing:
        raise ValueError(f"Missing predictions: {len(missing)}; full selected coverage is required")
    metrics = {condition: {"total": 0, "parsed": 0, "correct": 0} for condition in conditions}
    for identifier, row in expected.items():
        prediction = extract_answer(received[identifier])
        if prediction is not None and not math.isfinite(prediction):
            prediction = None
        cell = metrics[row["condition"]]
        cell["total"] += 1
        cell["parsed"] += prediction is not None
        cell["correct"] += is_correct(prediction, row["answer_float"], row["precision"])
    for cell in metrics.values():
        cell["unparseable"] = cell["total"] - cell["parsed"]
        cell["accuracy"] = cell["correct"] / cell["total"]
    return {"coverage": "complete", "prediction_count": len(received), "conditions": metrics}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--split", choices=("dev", "test", "gold"), default="test")
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    parser.add_argument("--release-dir", type=Path, default=ROOT / "release/cropmath-v1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new report path")
    try:
        report = score_predictions(
            read_jsonl(args.release_dir / "data/eval_prompts" / f"{args.split}.jsonl"),
            read_jsonl(args.predictions), args.conditions,
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    report.update({"split": args.split, "scope": "public numeric scoring for one model/run; no inferential statistics"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"Scored {report['prediction_count']} responses with complete selected coverage.")


if __name__ == "__main__":
    main()
