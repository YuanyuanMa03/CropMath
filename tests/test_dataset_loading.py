"""Load real local configurations and check their relationships in either package."""

from pathlib import Path

from datasets import load_dataset
import pytest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "release" / "cropmath-v1" if (ROOT / "release" / "cropmath-v1").is_dir() else ROOT


@pytest.fixture(scope="module")
def configurations():
    return {name: load_dataset(str(DATA), name) for name in ("default", "eval_prompts", "hidden_public")}


def test_actual_loader_split_sizes(configurations):
    expected = {
        "default": {"dev": 252, "test": 751, "gold": 95},
        "eval_prompts": {"dev": 1512, "test": 4506, "gold": 570},
        "hidden_public": {"hidden_public": 160},
    }
    for name, splits in expected.items():
        assert {split: len(rows) for split, rows in configurations[name].items()} == splits


def test_public_pairing_and_gold_subset(configurations):
    default = configurations["default"]
    dev, test, gold = ({row["id"] for row in default[split]} for split in ("dev", "test", "gold"))
    assert not dev & test
    assert gold <= test
    for split in ("dev", "test", "gold"):
        rows = configurations["eval_prompts"][split]
        grouped = {}
        for row in rows:
            assert (row["sample_id"], row["condition"]) not in grouped
            grouped[row["sample_id"], row["condition"]] = row["answer_float"]
        for row in default[split]:
            answers = [grouped[row["id"], condition] for condition in
                       ("C", "K_name", "K_formula", "K_domain", "K_distractor", "K_wrong")]
            assert answers == [float(row["answer"])] * 6


def test_auxiliary_set_has_questions_but_no_labels(configurations):
    rows = configurations["hidden_public"]["hidden_public"]
    ids = {row["id"] for row in rows}
    assert len(ids) == 160
    default = configurations["default"]
    assert not ids & {row["id"] for split in default.values() for row in split}
    for row in rows:
        assert not {"answer", "answer_float", "solution", "ground_truth", "effective_parameters"} & row.keys()
        assert row["answer_hidden"] is True
        assert row["formula"]["expression"] and row["parameters"] and row["prompts"]
