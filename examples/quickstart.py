"""Exercise public APIs with reference fixtures; no model is invoked."""

from pathlib import Path
import sys

from datasets import load_dataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cropmath.answer_parser import extract_answer, is_correct
from cropmath.prompts import CONDITIONS, build_messages


def main():
    data = load_dataset(str(ROOT / "release" / "cropmath-v1"), "default")
    sample = data["dev"][0]
    for condition in CONDITIONS:
        messages = build_messages(sample, condition)
        assert [message["role"] for message in messages] == ["system", "user"]
        assert all(message["content"] for message in messages)
    for row in data["gold"]:
        assert is_correct(extract_answer(row["solution"]), float(row["answer"]), row["formula"]["precision"])
    print("Local smoke check passed: 6 prompt conditions and 95 supplied gold solutions.")
    print("Reference-fixture validation only; no model performance was measured.")


if __name__ == "__main__":
    main()
