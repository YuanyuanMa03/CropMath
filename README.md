# CropMath

**English** | [简体中文](README.zh-CN.md)

CropMath evaluates numerical execution of agricultural mechanistic formulas under
six controlled knowledge conditions. This repository contains the dataset,
prompt builders, numeric answer parser, batch scorer and validation tests.
The dataset is also available on the
[Hugging Face Hub](https://huggingface.co/datasets/myy555/CropMath); both
platforms carry the same `cropmath-v1` data payload.

See [reproducibility scope](release/cropmath-v1/REPRODUCIBILITY.md) for the
relationship between these artifacts and the paper.

## Get started locally

Use Python 3.12 and uv. From this directory:

```bash
uv sync --locked
uv run --locked pytest -q -ra tests
uv run --locked python examples/quickstart.py
uv run --locked python scripts/validate_cropmath_release.py
uv run --locked python scripts/validate_formula_catalog.py
```

The quickstart loads the public data and exercises prompt construction and
answer parsing with supplied gold solutions. It makes no model requests and
does not report model performance. The release check runs Hugging Face loading
and the selected public-source scan; a skipped check is never reported as passed.

## What is included

| Path | Purpose |
|---|---|
| `src/cropmath/` | Prompt builders and numeric extraction/tolerance scoring |
| `release/cropmath-v1/` | The same dataset payload as the standalone Hugging Face dataset |
| `scripts/` | Batch scorer, dataset, formula catalog and result-record validators |
| `tests/` | Public parser, validation and actual dataset-loading tests |
| `examples/quickstart.py` | Local data and public-API smoke example |
| `pyproject.toml`, `uv.lock` | Reproducible local test and dataset-loading environment |

The dataset has 252 development questions and 751 test questions. Gold is a
95-question test subset. Six knowledge conditions produce 4,506 test prompts.
There are 62 formula identifiers and 160 additional answer-withheld questions.
See the [dataset card](release/cropmath-v1/README.md) for schema, license,
split relationships and scientific limitations.

## Evaluate your own model outputs

Prepare one JSONL file per model/run. Each row must contain `id` (copied exactly
from the selected `eval_prompts` row) and `response` (the model's output text).
Send only the prompt content to your model; never send reference answer fields.
Use an empty response for a failed generation so it remains in the denominator.

```bash
uv run --locked python scripts/score_predictions.py --predictions predictions.jsonl --split test --output scores.json
```

This scores all six conditions by default: 4,506 responses for test. To score only
C, add `--conditions C` and provide exactly its 751 responses. Other public splits
are available through `--split dev` or `--split gold`. Duplicate, unknown and
missing IDs are rejected; unparseable outputs count as incorrect. Existing report
files are never overwritten. Accuracy is reported per condition on a 0–1 scale.
See [evaluation instructions](docs/EVALUATION.md) for the input contract, prompt
format and reporting requirements.

`validate_eval_results.py` checks the project's detailed result schema. Its
`--formal-config` mode checks the historical deterministic local-inference
configuration, not arbitrary API responses. It checks conditions only for models
present in the input; callers must separately check the intended model roster,
sample IDs and expected number of cells. A record-schema check does not score
predictions or establish their scientific validity.

This package does not include an inference runner, model weights, original model
responses, paper-level analysis results, or private formula/generation implementations.
It therefore supports public data reuse and numeric scoring, not a one-command
rerun of the entire paper. It contains no hosted leaderboard or hidden-answer service.

## Answer-withheld questions

Public development/test/gold answers are provided. The 160 `hidden_public`
questions expose formulas, parameters and prompts but do not include reference
answers or solutions. This does not establish absence of training contamination.
See [the shared policy](release/cropmath-v1/HIDDEN_POLICY.md). Hidden-answer tests
are maintained separately and are not part of this public package.

## License, citation and maintenance

Code uses the MIT notice in `LICENSE`; data uses CC BY 4.0 as specified in the
dataset's `LICENSE`. `CITATION.cff` provides dataset attribution and the
repository link. No paper DOI is assigned here; cite via `CITATION.cff` and update
it when a paper reference becomes available. Environment metadata version `0.0.0`
tracks the validation environment for these tests; it is not a versioned software
release.

Keep public formula IDs, split names and condition names stable. After changes,
run the tests and both release validators above. Data-loading tests do not prove
formula provenance or human-audit completion.
