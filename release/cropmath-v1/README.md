---
license: cc-by-4.0
pretty_name: CropMath
language:
  - en
  - zh
task_categories:
  - question-answering
tags:
  - agriculture
  - numerical-reasoning
size_categories:
  - 1K<n<10K
configs:
  - config_name: default
    default: true
    data_files:
      - split: dev
        path: data/default/dev.jsonl
      - split: test
        path: data/default/test.jsonl
      - split: gold
        path: data/default/gold.jsonl
  - config_name: eval_prompts
    data_files:
      - split: dev
        path: data/eval_prompts/dev.jsonl
      - split: test
        path: data/eval_prompts/test.jsonl
      - split: gold
        path: data/eval_prompts/gold.jsonl
  - config_name: hidden_public
    data_files:
      - split: hidden_public
        path: hidden_public/hidden_public.jsonl
---

# CropMath

CropMath contains agricultural mechanistic formula questions with numeric
reference answers and controlled knowledge conditions. The `cropmath-v1`
snapshot is publicly available at
[myy555/CropMath](https://huggingface.co/datasets/myy555/CropMath); the
accompanying prompt builders, scorer and validators are in the code repository
[YuanyuanMa03/CropMath](https://github.com/YuanyuanMa03/CropMath).

## Contents and split relationships

| Configuration | dev | test | gold | hidden_public |
|---|---:|---:|---:|---:|
| default | 252 | 751 | 95 | — |
| eval_prompts | 1,512 | 4,506 | 570 | — |
| hidden_public | — | — | — | 160 |

The 95 gold questions are copied from test for auditing; do not add them to the
test count or treat them as an independent split. There are 1,003 unique
development/test questions. The six-condition expansion repeats the same
questions with different knowledge blocks; it does not create independent
questions. The formula catalog contains 62 public identifiers, CMF001–CMF062.

The public process categories are `growth_yield`, `carbon_nitrogen_cycle`,
`methane_emission`, and `environmental_response`. Reasoning modes are `direct`,
`sensitivity`, `branch`, and `chain_2`.

## Loading from the Hub

```python
from datasets import load_dataset

questions = load_dataset("myy555/CropMath", "default")
prompts = load_dataset("myy555/CropMath", "eval_prompts")
auxiliary = load_dataset("myy555/CropMath", "hidden_public")
assert len(questions["test"]) == 751
assert len(prompts["test"]) == 4506
assert len(auxiliary["hidden_public"]) == 160
```

Pin the released dataset revision in experiment records. Do not put access
tokens in code or prediction files.

To work offline or to run the bundled validators, download this repository and
use it as a local path. The standalone dataset directory also contains
`pyproject.toml`, `uv.lock`, validation scripts and dataset tests. From its root:

```bash
uv sync --locked
uv run --locked pytest -q tests
uv run --locked python scripts/validate_cropmath_release.py --release-dir . --no-scan-repo-root
uv run --locked python scripts/validate_formula_catalog.py --path metadata/formula_catalog.csv
```

For the copy inside the GitHub repository, use that repository's root README
commands instead. Validation success means the specified local checks passed;
it does not establish scientific validity or online Viewer behavior.

## Fields and use

`default` rows include `id`, `problem`, `formula`, `parameters`, reasoning mode,
knowledge blocks, per-condition prompts, `answer` and `solution`.
`eval_prompts` rows include a condition-specific `id`, the original `sample_id`,
`condition`, `prompt`, `answer_float`, `precision` and grouping metadata.
Only send the selected `prompt` to a model. Do not include the answer, solution,
other conditions' knowledge blocks or scoring metadata in the model input.

The six conditions are C (formula and inputs), K_name (name), K_formula
(parameter semantics), K_domain (domain context), K_distractor (distractors),
and K_wrong (an incorrect formula). The target remains the reference answer
to the original task even when K_wrong supplies an incorrect formula.

Numeric scoring uses:

```text
abs(prediction - answer) <= max(0.5 * 10**(-precision), abs(answer) * 0.01)
```

Unparseable predictions count as incorrect. Preserve sample pairing across
conditions and account for formula-level clustering in statistical inference.
See `eval.yaml` for the serialized protocol and `HIDDEN_POLICY.md` for auxiliary-set access.

## Provenance and limitations

The snapshot contains standardized expressions, reference labels, a public
formula catalog and audit metadata. It does not distribute private calculator
implementations, generation code or a complete per-formula bibliographic mapping.
Consequently, this package supports reusing questions and checking numeric
predictions against stored labels, but does not independently reproduce the
entire formula acquisition and reference-answer generation process.

The audit CSV and protocols are supplied records, not a new independent human
audit performed by the package validator. Automated parser tests check the
serialized solutions; they do not certify the human-audit provenance.
Inputs are synthetic, and this benchmark does not establish reliability on
field observations, complete crop simulations or real agricultural decisions.

The 160 auxiliary questions are public while their answers are withheld. No
hosted scoring service is supplied. ID disjointness and withheld labels are not
proof of absence of training contamination. See `HIDDEN_POLICY.md`.

## Licensing and attribution

Dataset contents are provided under CC BY 4.0; see `LICENSE`. Validation code
included in this dataset repository uses the MIT terms in `CODE_LICENSE`.
The GitHub repository carries a separate MIT license for its code.
Attribution metadata is provided in `CITATION.cff`, including the code
repository link. No paper DOI is claimed. Existing notices are preserved. See
[reproducibility scope](REPRODUCIBILITY.md) for what these artifacts support.
