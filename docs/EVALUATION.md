# Scoring model outputs

Run one model/configuration at a time. Read `data/eval_prompts/<split>.jsonl`
inside the bundled dataset and preserve the full row `id` (including its condition
suffix) in your output. Required output fields are `id` and `response`, both
strings. Extra fields are ignored by the scorer; do not mix runs in one file.

The dataset's `prompt` is serialized system/user text with chat delimiters. It is
not a universally portable API messages object. For a chat API, use the public
`build_messages(sample, condition)` function on the matching `default` sample
and the model's chat template; record this choice. Never render a chat template
twice. No inference/backend compatibility is claimed by these scoring tests.

Create each output record from the source ID and the actual response:

```python
record = {"id": source_row["id"], "response": model_response_text}
```

An empty string represents a failed generation and is scored incorrect. Do not
drop it. Missing IDs abort scoring. Unknown IDs (including an unselected condition
or split), duplicate IDs and non-string responses also abort scoring. Reference
conditions must have matching sample sets. Report file creation is exclusive;
choose a new filename for each run.

```bash
uv run --locked python scripts/score_predictions.py --predictions predictions.jsonl --split test --output scores.json
```

By default, test requires 4,506 responses: 751 per condition. Use `--conditions C`
for a complete single-condition run or list multiple conditions. Use dev for
development and gold for the overlapping audit subset; gold is not a second
independent test set. The auxiliary answer-withheld set cannot be scored here.

Each condition reports `total`, `parsed`, `unparseable`, `correct` and `accuracy`
(fraction between 0 and 1). Parsing uses the distributed parser without changing
the historical extraction order. Nonfinite predictions are treated as unparseable.
The correctness threshold is:

```text
abs(prediction - answer_float) <= max(0.5 * 10**(-precision), abs(answer_float) * 0.01)
```

K_wrong retains the original task's reference answer. Matching the injected
incorrect formula does not count as correct. The score file contains descriptive
results for the supplied responses; it cannot certify where they came from.
Do not report reference-fixture tests as measured model performance.
