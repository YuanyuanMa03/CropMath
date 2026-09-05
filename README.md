# CropMath toolkit for private review

This repository contains the CropMath dataset, prompt builders, numeric answer
parser and local validation tests. It is deposited for private review at
[YuanyuanMa03/CropMath](https://github.com/YuanyuanMa03/CropMath), alongside the
private [Hugging Face dataset](https://huggingface.co/datasets/myy555/CropMath).
Access is restricted; this is not a public release and no DOI is assigned.

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
| `release/cropmath-v1/` | The same dataset payload as the standalone Hugging Face candidate |
| `scripts/` | Dataset, formula catalog and result-record validators |
| `tests/` | Public parser, validation and actual dataset-loading tests |
| `examples/quickstart.py` | Local data and public-API smoke example |
| `pyproject.toml`, `uv.lock` | Reproducible local test and dataset-loading environment |

The dataset has 252 development questions and 751 test questions. Gold is a
95-question test subset. Six knowledge conditions produce 4,506 test prompts.
There are 62 formula identifiers and 160 additional answer-withheld questions.
See the [dataset card](release/cropmath-v1/README.md) for schema, license,
split relationships and scientific limitations.

## Evaluate your own model outputs

Load `eval_prompts` from the bundled dataset, send only each row's `prompt` to
your model, and retain its `id`, `sample_id` and `condition` with the response.
Use `cropmath.answer_parser.extract_answer(response)` followed by
`is_correct(prediction, row["answer_float"], row["precision"])` to score it.
Treat parsing failures as incorrect and report complete expected-sample coverage;
do not silently drop failed or missing predictions. The executable quickstart
demonstrates these APIs. Use the same items for paired condition comparisons.

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

Code uses the existing MIT notice in `LICENSE`; data uses CC BY 4.0 as specified
in the dataset's `LICENSE`. `CITATION.cff` provides attribution metadata and the private repository address;
no DOI is assigned. Environment metadata version `0.0.0`
identifies this local validation project; it is not a published software release.

Keep public formula IDs, split names and condition names stable. After changes,
run the tests and both release validators above. Data-loading tests do not prove
formula provenance or human-audit completion. Any future public release must update
the visibility notice only after access settings have actually been changed
with the maintainer's authorization and online access has been checked.
