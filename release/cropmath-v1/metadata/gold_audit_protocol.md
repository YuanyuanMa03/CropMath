# CropMath v1 Gold Audit Protocol

The gold file is a 95-row audit worksheet copied from the frozen test split. It
is not an independent evaluation split.

For each row, verify that the problem is clear, the formula matches the intended
quantity and mode, and the serialized answer recomputes from the effective
parameters within the formula precision. Use `yes`, `no`, or `unclear` in the
human audit columns and record issues in `human_notes`.

If any row fails, fix the generator/calculator and rebuild the release. Do not
patch individual JSONL rows by hand.
