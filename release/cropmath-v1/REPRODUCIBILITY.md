# Reproducibility and release scope

CropMath provides frozen questions, stored reference answers and controlled
prompts for evaluating agricultural formula execution. Development and test
contain 1,003 unique questions; the 95 gold questions are a subset of test.
The six conditions are repeated measurements on the same questions.

| Research component | Distributed artifact | Supported use |
|---|---|---|
| Questions and labels | `data/default/` | Reuse dev/test/gold questions and stored references |
| Knowledge conditions | `data/eval_prompts/` | Use all six prompts with stable sample/condition IDs |
| Numeric scoring | GitHub parser and `scripts/score_predictions.py` | Score complete model-output files with the documented tolerance |
| Formula coverage | `metadata/formula_catalog.csv` | Inspect 62 formula IDs and grouping metadata |
| Audit records | `metadata/gold_audit.csv` and protocols | Inspect supplied records; automated tests do not certify human review |
| Auxiliary questions | `hidden_public/` and `HIDDEN_POLICY.md` | Inspect 160 questions without reference labels |

The code package does not distribute an inference runner, private calculators,
data generators, original model responses or the paper's full statistical
analysis pipeline. Formula acquisition and answer regeneration therefore cannot
be reproduced solely from this package. The formula catalog is not a complete
per-formula literature provenance table. These limits must not be replaced by a
claim of end-to-end paper reproduction.

For experiments, record the data and code revision, model and tokenizer revision,
runtime/dependency versions, chat template, decoding parameters, thinking mode,
seed and sample coverage. Keep public labels out of model inputs. Score against
the original task reference even under the incorrect-formula condition K_wrong.

The batch scorer reports descriptive accuracy, not confidence intervals,
McNemar tests, BH-FDR corrections or behavioral judgments. Comparisons require
the same sample IDs across conditions; uncertainty analysis must account for
formula clustering. The original experiment settings in `eval.yaml` describe a
protocol, not proof that a new run matches the paper.

Dataset loading, parser tests and fixture scoring establish software/data
compatibility. They do not measure a model, validate agricultural field use,
independently audit references or establish absence of training contamination.

Data licensing is recorded in `LICENSE` (CC BY 4.0); code licensing is in the
GitHub `LICENSE` and the dataset's `CODE_LICENSE` (MIT). Cite the dataset metadata
in `CITATION.cff`. Paper bibliographic details will be added after they exist.
