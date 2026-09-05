from pathlib import Path

import json
import sys

import pytest

from scripts.validate_cropmath_release import validate_public_content
from scripts import validate_cropmath_release as release_validator


def test_public_content_accepts_anonymous_formula_text(tmp_path: Path) -> None:
    data = tmp_path / "data.jsonl"
    data.write_text(
        '{"formula_id":"CMF001","prompt":"Use the documented formula."}\n',
        encoding="utf-8",
    )

    assert validate_public_content(tmp_path) == []


def test_public_content_rejects_implementation_and_citation_residue(
    tmp_path: Path,
) -> None:
    data = tmp_path / "data.jsonl"
    data.write_text(
        '{"prompt":"See FooModel.py and Smith et al. for source code."}\n',
        encoding="utf-8",
    )

    issues = validate_public_content(tmp_path)

    # The fixture uses neutral wording that still triggers the source-code,
    # implementation-reference, and citation detectors. The framework-name
    # detector is exercised indirectly via the blocklist in production data.
    assert any("source-code wording" in issue for issue in issues)
    assert any("implementation file reference" in issue for issue in issues)
    assert any("generated citation" in issue for issue in issues)


def test_requested_hf_validation_fails_when_dependency_is_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["validator", "--release-dir", str(tmp_path), "--no-scan-repo-root"])
    monkeypatch.setattr(release_validator, "validate_jsonl", lambda _: [])
    monkeypatch.setattr(release_validator, "validate_public_content", lambda _: [])
    monkeypatch.setitem(sys.modules, "datasets", None)

    with pytest.raises(SystemExit) as exc:
        release_validator.main()

    report = json.loads(capsys.readouterr().out)
    assert exc.value.code == 1
    assert report["jsonl_pass"] is True
    assert report["hf_loader_pass"] is False
    assert report["repo_root_scan_pass"] is None
    assert "datasets is not installed" in report["hf_loader_issues"][0]


def test_skipped_hf_validation_is_not_reported_as_pass(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["validator", "--release-dir", str(tmp_path), "--skip-hf-loader"])
    monkeypatch.setattr(release_validator, "validate_jsonl", lambda _: [])
    monkeypatch.setattr(release_validator, "validate_public_content", lambda _: [])
    monkeypatch.setattr(release_validator, "validate_repo_root_content", lambda _: ["source tree finding"])
    monkeypatch.setattr(release_validator, "validate_hf_loader", lambda _: pytest.fail("must not load when skipped"))

    with pytest.raises(SystemExit) as exc:
        release_validator.main()

    report = json.loads(capsys.readouterr().out)
    assert exc.value.code == 1
    assert report["jsonl_pass"] is True
    assert report["hf_loader_pass"] is None
    assert report["repo_root_scan_pass"] is False
    assert report["issues"] == ["source tree finding"]
