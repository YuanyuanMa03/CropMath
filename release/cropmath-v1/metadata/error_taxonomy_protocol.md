# CropMath Error Taxonomy Protocol

Annotate at least 200 incorrect core-model predictions sampled across model, condition, family, and mode.

Allowed primary/secondary error types:

- `formula_selection_error`
- `parameter_substitution_error`
- `arithmetic_computation_error`
- `branch_condition_error`
- `sensitivity_change_handling_error`
- `unit_precision_rounding_error`
- `final_answer_extraction_format_error`
- `hallucinated_or_ignored_formula`

Set `parser_extraction_correct` to `yes`, `no`, or `unclear` after comparing the raw response with the parsed prediction.
