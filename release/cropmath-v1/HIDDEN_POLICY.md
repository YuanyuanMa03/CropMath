# Answer-withheld auxiliary set

The `default` and `eval_prompts` configurations contain reference answers. The
`gold` split is a 95-row subset of `test`, not an independent evaluation set.

The `hidden_public` configuration contains 160 additional questions, including
formula expressions, input parameters and prompts. It does not distribute
reference answers, solutions or effective-parameter fields. Its sample IDs are
disjoint from the public development and test splits.

This is a question-public, answer-withheld auxiliary set. Withholding reference
labels and using disjoint IDs do not establish absence of training contamination:
the public questions can still be solved and may become part of training data.
The existing answer commitment fields are retained as metadata; this release
does not claim that the corresponding private answer files have been located
and independently checked as part of public-package validation.

No hosted hidden-set scoring service or submission endpoint is included or
currently offered by this candidate. Public-split scoring can be reproduced
locally. Hidden-set scoring requires separately verified reference answers and
a defined evaluation procedure. Any later service must document submission
format, complete-sample coverage, duplicate and unknown-ID handling, scoring
rules, access conditions and limits before accepting benchmark submissions.

Private reference answers, private calculators and generation implementations
are excluded from both publication candidates. This policy does not promise
future access to those materials.
