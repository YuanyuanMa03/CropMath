import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_eval_results.py"


def _row(sample_id: str, prompt_style: str) -> dict:
    return {
        "id": sample_id,
        "model_tag": "qwen3_14b",
        "condition": "K_wrong",
        "prompt_style": prompt_style,
        "data_sha256": "d",
        "prompt_sha256": "p",
        "sample_sha256": "s",
        "response_sha256": "r",
        "model_config_sha256": "m",
        "tokenizer_config_sha256": "t",
        "input_tokens": 1,
        "output_tokens": 1,
        "generation_config": {
            "max_new_tokens": 2048,
            "temperature": 0.0,
            "thinking_mode": "off",
            "torch_dtype": "bf16",
            "do_sample": False,
        },
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_formal_config_skips_auxiliary_prompt_styles(tmp_path: Path) -> None:
    main = tmp_path / "qwen3_14b_K_wrong.jsonl"
    audit = tmp_path / "qwen3_14b_K_wrong_formula_audit.gpu0.jsonl"
    _write_jsonl(main, [_row("item-1", "baseline_cot")])
    _write_jsonl(audit, [_row("item-1", "formula_audit")])

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(main),
            str(audit),
            "--expected-rows",
            "1",
            "--formal-config",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(result.stdout)
    assert report["pass"] is True
    assert report["cells"] == 1
    assert report["skipped_auxiliary_rows"] == 1


def test_can_validate_auxiliary_prompt_style_explicitly(tmp_path: Path) -> None:
    audit = tmp_path / "qwen3_14b_K_wrong_formula_audit.gpu0.jsonl"
    _write_jsonl(audit, [_row("item-1", "formula_audit")])

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(audit),
            "--expected-rows",
            "1",
            "--prompt-style",
            "formula_audit",
            "--formal-config",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(result.stdout)
    assert report["pass"] is True
    assert report["cells"] == 1
