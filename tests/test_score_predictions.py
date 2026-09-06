"""Coverage errors must never inflate public benchmark accuracy."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("score_predictions", Path(__file__).resolve().parents[1] / "scripts/score_predictions.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def reference():
    return [dict(id=f"q{i}__C", sample_id=f"q{i}", condition="C", answer_float=answer, precision=2)
            for i, answer in enumerate((0.0, 100.0, -5.0))]


def predictions():
    return [dict(id=row["id"], response=text) for row, text in zip(
        reference(), ("The answer is 0.004", "The answer is 101", "unable to calculate"))]


def test_tolerance_and_parse_failure_denominator():
    result = module.score_predictions(reference(), predictions(), ["C"])
    assert result["conditions"]["C"] == dict(total=3, parsed=2, correct=2, unparseable=1, accuracy=2/3)


@pytest.mark.parametrize("kind", ["missing", "duplicate", "unknown", "bad_response"])
def test_reject_ambiguous_or_incomplete_predictions(kind):
    rows = predictions()
    if kind == "missing":
        rows.pop()
    elif kind == "duplicate":
        rows.append(rows[0])
    elif kind == "unknown":
        rows[0]["id"] = "not-in-selected-split"
    else:
        rows[0]["response"] = None
    with pytest.raises(ValueError):
        module.score_predictions(reference(), rows, ["C"])


def test_reject_unpaired_reference_conditions():
    rows = reference() + [dict(id="different__K_wrong", sample_id="different", condition="K_wrong", answer_float=1.0, precision=2)]
    with pytest.raises(ValueError, match="same sample IDs"):
        module.score_predictions(rows, [], ["C", "K_wrong"])


def test_wrong_formula_condition_uses_original_reference():
    row = dict(id="q__K_wrong", sample_id="q", condition="K_wrong", answer_float=100.0, precision=2)
    result = module.score_predictions([row], [dict(id=row["id"], response="The answer is 10")], ["K_wrong"])
    assert result["conditions"]["K_wrong"]["correct"] == 0
