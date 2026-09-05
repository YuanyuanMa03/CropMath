#!/usr/bin/env python3
"""Prompt builders for clean knowledge ablation.

The dev split is used to choose one prompt style before running the frozen
test split. Keep every style versioned and reproducible.
"""

from __future__ import annotations

CONDITIONS = ("C", "K_name", "K_formula", "K_domain", "K_distractor", "K_wrong")

# Original GSM8K-style prompt, kept as the baseline for prompt-search reports.
BASELINE_COT_PROMPT = (
    "You are a scientific reasoning assistant. Solve the following problem "
    "step by step. Show your reasoning clearly, then end with exactly one line "
    "in this format: The answer is [number].\n"
    "Do not write multiple answers. Do not include units in the final line.\n"
    "Example:\n"
    "Step 1: ...\n"
    "Step 2: ...\n"
    "The answer is 42.5"
)

STRICT_NUMERIC_PROMPT = (
    "You solve crop-model numerical problems. Work carefully, but keep the "
    "solution concise. Use only the information provided in the question and "
    "knowledge block. End with exactly one final line:\n"
    "The answer is [number]\n"
    "The final line must contain no unit, no explanation, and no extra text."
)

FORMULA_AUDIT_PROMPT = (
    "You solve mechanistic crop-model formula problems. Before calculating, "
    "identify the target quantity and the formula that matches the problem. "
    "Then substitute the given values, compute the result, and round to the "
    "precision implied by the problem. If a knowledge block is wrong or does "
    "not match the target quantity, do not blindly follow it. End with exactly "
    "one final line:\n"
    "The answer is [number]"
)

CALCULATOR_PROMPT = (
    "You are a careful numerical calculator for crop physiology equations. "
    "Follow this order: target quantity, relevant variables, formula choice, "
    "substitution, arithmetic check. Avoid inventing missing variables. The "
    "last line must be exactly:\n"
    "The answer is [number]"
)

FINAL_ONLY_PROMPT = (
    "Solve the crop-model calculation internally. Do not show derivations. "
    "Return exactly one line and nothing else:\n"
    "The answer is [number]"
)

AGENTIC_SOLVER_PROMPT = (
    "You are a crop-model formula-solving agent. Your job is not just to "
    "calculate, but to guard against formula misuse and variable mismatch.\n"
    "\n"
    "Follow this internal workflow:\n"
    "1. Task parse: identify the requested target quantity and output unit.\n"
    "2. Formula check: use a provided formula only if its name, output unit, "
    "and physiological meaning match the requested target. If the provided "
    "formula is irrelevant or wrong, rely on the problem information instead "
    "of blindly following it.\n"
    "3. Variable binding: map every symbol in the formula to the exact value "
    "given in the problem. Treat similarly named variables as different unless "
    "the knowledge block explicitly maps them.\n"
    "4. Branch/min/max check: for piecewise formulas, select the active branch; "
    "for min/max formulas, explicitly choose the smaller/larger driver before "
    "multiplying.\n"
    "5. Arithmetic: substitute values into the calculation-friendly formula "
    "and compute the numeric result to a decimal number. Do not leave the "
    "answer as an unevaluated expression. Respect sensitivity questions by "
    "using the changed value requested in the question; the changed value "
    "overrides the original value for the final calculation.\n"
    "6. Final check: round to the precision implied by the dataset answer and "
    "ensure the final line contains only a decimal number.\n"
    "\n"
    "Write a concise solution with these labels: Target, Formula, Variables, "
    "Calculation, Check. End with exactly one line:\n"
    "The answer is 42.5\n"
    "Replace 42.5 with your computed decimal number. Never output [number], "
    "brackets, units, or an unevaluated expression in the final line."
)

EXPERT_CROPMATH_PROMPT = (
    "You are solving a verified crop-model formula problem as an agronomic "
    "modeling expert, not as a general chatbot. Treat the task as checking a "
    "small piece of model code by hand.\n"
    "\n"
    "Use the calculation-friendly plain-text formula when it is provided. "
    "The LaTeX formula is only a display version. Your main risks are variable "
    "mismatch, using an old value in a sensitivity question, choosing the wrong "
    "piecewise branch, and leaving arithmetic unfinished.\n"
    "\n"
    "Before calculating, make sure the requested output quantity and unit match "
    "the formula's output. If the retrieved formula is clearly for another "
    "quantity, do not force it onto the problem. When the question says a "
    "parameter 'changed to' a new value, use that new value for the final "
    "calculation and ignore the old value for that parameter. For min/max terms, "
    "first determine which numeric driver is selected; for piecewise terms, "
    "first determine which condition is active.\n"
    "\n"
    "Carry the arithmetic through to a decimal number. Do not give a symbolic "
    "expression such as '0.49*exp(...)' as the final answer. Keep scratch work "
    "short: at most four concise lines before the final answer. Prefer finishing "
    "the calculation over explaining background context.\n"
    "\n"
    "The final line must begin with 'The answer is ' followed by decimal digits, "
    "for example 'The answer is 0.982'. Never output placeholders such as "
    "'[number]' or '<decimal number>', never output brackets, and never include "
    "units or extra text after the final number."
)

EXPERT_LITE_PROMPT = (
    "Solve this as a crop-model formula execution task. Prefer the "
    "calculation-friendly plain-text formula over the LaTeX display formula.\n"
    "\n"
    "Rules for this benchmark:\n"
    "- Match the requested output quantity before using a formula.\n"
    "- If the problem says a parameter changed to a new value, use the new "
    "value in the final calculation.\n"
    "- For min/max, compute the selected numeric input first.\n"
    "- For piecewise formulas, choose the active branch before substituting.\n"
    "- Substitute values and finish the arithmetic; do not leave an expression "
    "as the answer.\n"
    "\n"
    "Keep the solution short. End with exactly one line in this form:\n"
    "The answer is 0.982\n"
    "Use your computed decimal number instead of 0.982. Do not include units."
)

PROMPT_STYLES = {
    "baseline_cot": BASELINE_COT_PROMPT,
    "strict_numeric": STRICT_NUMERIC_PROMPT,
    "formula_audit": FORMULA_AUDIT_PROMPT,
    "calculator": CALCULATOR_PROMPT,
    "final_only": FINAL_ONLY_PROMPT,
    "agentic_solver": AGENTIC_SOLVER_PROMPT,
    "expert_cropmath": EXPERT_CROPMATH_PROMPT,
    "expert_lite": EXPERT_LITE_PROMPT,
}


def build_user_block(sample: dict, condition: str) -> str:
    """Build the user message for one knowledge-ablation condition.

    Conditions:
    - C: formula expression only (no semantic context). The model has the
      computational tool but not the domain knowledge. This isolates the
      effect of understanding from the effect of computation availability.
    - K_name: C + formula name (English + Chinese).
    - K_formula: C + parameter meanings, units, and typical ranges.
    - K_domain: K_formula + category and applicability metadata.
    - K_distractor: problem plus the correct formula mixed with distractors.
    - K_wrong: problem plus an incorrect but plausible formula.
    """

    problem = sample["problem"]
    if condition == "C":
        user = f"{sample['knowledge_formula_expr']}\n\nQ: {problem}"
    elif condition == "K_name":
        user = f"{sample['knowledge_name']}\n\nQ: {problem}"
    elif condition == "K_formula":
        user = f"{sample['knowledge_formula']}\n\nQ: {problem}"
    elif condition == "K_domain":
        user = f"{sample['knowledge_domain']}\n\nQ: {problem}"
    elif condition == "K_distractor":
        user = f"{sample['knowledge_distractor']}\n\nQ: {problem}"
    elif condition == "K_wrong":
        user = f"{sample['knowledge_wrong']}\n\nQ: {problem}"
    else:
        raise ValueError(f"Unknown condition: {condition}")

    return user


def build_messages(sample: dict, condition: str, prompt_style: str = "baseline_cot") -> list[dict[str, str]]:
    """Build a chat-messages list (model-agnostic) for one sample and prompt style.

    Returns:
        [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
    """
    if prompt_style not in PROMPT_STYLES:
        known = ", ".join(sorted(PROMPT_STYLES))
        raise ValueError(f"Unknown prompt style: {prompt_style}. Known styles: {known}")

    user = build_user_block(sample, condition)
    system_prompt = PROMPT_STYLES[prompt_style]
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user},
    ]


def build_prompt(sample: dict, condition: str, prompt_style: str = "baseline_cot") -> str:
    """Build a ChatML-style prompt (backward compat).

    Prefer build_messages() + tokenizer.apply_chat_template() for multi-model support.
    """
    messages = build_messages(sample, condition, prompt_style)
    system_prompt = messages[0]["content"]
    user = messages[1]["content"]
    return (
        "<|im_start|>system\n"
        f"{system_prompt}<|im_end|>\n"
        "<|im_start|>user\n"
        f"{user}<|im_end|>\n"
        "<|im_start|>assistant\n"
        "A:"
    )


def assert_control_is_clean(sample: dict) -> None:
    """Verify C condition does not leak semantic knowledge.

    C includes the formula expression (computation tool) but must NOT include:
    - Parameter descriptions (domain knowledge)
    - Typical parameter ranges (domain knowledge)
    - Formula name (semantic identifier)
    - Category/applicability metadata (domain context)
    """
    prompt = build_prompt(sample, "C", "baseline_cot")
    forbidden = [
        "Parameters:",
        "typical range=",
        "Formula name:",
        "Physiological category:",
    ]
    leaked = [item for item in forbidden if item in prompt]
    if leaked:
        raise AssertionError(f"Control prompt leaks semantic knowledge: {leaked}")
