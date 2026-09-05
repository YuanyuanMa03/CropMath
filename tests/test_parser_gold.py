"""Check parsing against serialized public gold solutions, not human audit provenance."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from cropmath.answer_parser import extract_answer, is_correct

GOLD_PATH = REPO_ROOT / "release" / "cropmath-v1" / "data" / "default" / "gold.jsonl"


@pytest.fixture(scope="module")
def gold_rows():
    rows = []
    with GOLD_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    assert len(rows) == 95, f"Expected 95 release gold rows, got {len(rows)}"
    return rows


class TestGoldParseRate:
    """extract_answer must return a value for every gold solution."""

    def test_no_none_extractions(self, gold_rows):
        failures = []
        for row in gold_rows:
            result = extract_answer(row["solution"])
            if result is None:
                failures.append(row["id"])
        assert failures == [], f"Failed to extract from {len(failures)} gold solutions: {failures}"

    def test_all_correct(self, gold_rows):
        failures = []
        for row in gold_rows:
            gt = float(row["answer"])
            precision = int(row["formula"]["precision"])
            extracted = extract_answer(row["solution"])
            if not is_correct(extracted, gt, precision):
                failures.append(
                    f"{row['id']}: extracted={extracted}, gt={gt}, precision={precision}"
                )
        assert failures == [], (
            f"{len(failures)} gold solutions scored incorrectly:\n"
            + "\n".join(failures[:10])
        )


class TestGoldRoundtrip:
    """is_correct(float(answer), float(answer)) must always be True."""

    def test_roundtrip(self, gold_rows):
        for row in gold_rows:
            gt = float(row["answer"])
            precision = int(row["formula"]["precision"])
            assert is_correct(gt, gt, precision), (
                f"Round-trip failed for {row['id']}: gt={gt}, precision={precision}"
            )

