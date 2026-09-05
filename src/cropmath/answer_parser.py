"""Pure-Python answer extraction and scoring utilities.

Separated from evaluate_pytorch.py so tests can run without PyTorch/CUDA.
"""

from __future__ import annotations

import ast
import re


def parse_number_like(raw: str) -> float | None:
    """Parse a plain number, fraction, or simple arithmetic expression."""
    raw = raw.strip().rstrip(".,;")
    raw = raw.replace("−", "-").replace("^", "**")

    try:
        return float(raw)
    except ValueError:
        pass

    if re.fullmatch(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?\s*/\s*[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?", raw):
        try:
            num, den = raw.split("/", 1)
            return float(num.strip()) / float(den.strip())
        except (ValueError, ZeroDivisionError):
            return None

    if not re.fullmatch(r"[\d\s+\-*/().eE]+", raw):
        return None

    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.USub,
        ast.UAdd,
    )
    try:
        tree = ast.parse(raw, mode="eval")
    except SyntaxError:
        return None
    if not all(isinstance(node, allowed_nodes) for node in ast.walk(tree)):
        return None
    try:
        # Safe: tree was parsed by ast.parse and all nodes are whitelisted numeric ops only
        value = eval(compile(tree, "<answer>", "eval"), {"__builtins__": {}}, {})
    except Exception:
        return None
    if isinstance(value, (int, float)) and abs(float(value)) < 1e12:
        return float(value)
    return None


def extract_answer(text: str) -> float | None:
    """Extract the final numeric answer from model output.

    Pattern priority:
    1. \\boxed{X} (MATH format)
    2. #### X (GSM8K format)
    3. "Therefore, the answer is X"
    4. "The answer is X" (with contradiction detection)
    5. Last number fallback
    """
    # Strip think/reasoning blocks.
    # Each block type handles TWO cases:
    #   (a) properly closed  <tag>...</tag>  -> remove the whole block
    #   (b) truncated/unclosed <tag>...      -> generation was cut before the
    #       closing tag; drop everything from the opening tag to the end so
    #       the reasoning text does not pollute the last-number fallback.
    #       (Returns None downstream when no real answer remains.)
    if "<｜place▁holder▁no" in text and "</｜place▁holder▁no" in text:
        text = re.sub(r"<｜place▁holder▁no\d+｜>.*?</｜place▁holder▁no\d+｜>", " ", text, flags=re.DOTALL)
    elif "<｜place▁holder▁no" in text:
        text = re.sub(r"<｜place▁holder▁no\d+｜>.*$", " ", text, flags=re.DOTALL)

    if "<think" in text and "</think" in text:
        text = re.sub(r"<think[^>]*>.*?</think[^>]*>", " ", text, flags=re.DOTALL)
    elif "<think" in text:
        # Unclosed <think ...> (truncated mid-thought): drop to end of text.
        text = re.sub(r"<think[^>]*>.*$", " ", text, flags=re.DOTALL)

    if "<thinking>" in text and "</thinking>" in text:
        text = re.sub(r"<thinking>.*?</thinking>", " ", text, flags=re.DOTALL)
    elif "<thinking>" in text:
        # Unclosed <thinking> (truncated mid-thought): drop to end of text.
        text = re.sub(r"<thinking>.*$", " ", text, flags=re.DOTALL)

    # 1. \\boxed{X} (MATH format)
    m = re.search(r"\\boxed\{([^}]+)\}", text)
    if m:
        parsed = parse_number_like(m.group(1))
        if parsed is not None:
            return parsed

    # 2. #### X (GSM8K format)
    matches = re.findall(r"####\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?(?:\s*/\s*[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)?)", text)
    if matches:
        parsed = parse_number_like(matches[-1])
        if parsed is not None:
            return parsed

    # 3. "Therefore, the answer is X"
    matches = re.findall(r"[Tt]herefore, the answer is\s+([^\n]+)", text)
    if matches:
        parsed = parse_number_like(matches[0])
        if parsed is not None:
            return parsed

    # 4. "The answer is X" with contradiction detection
    pattern = re.compile(
        r"[Tt]he answer (?:is|should be|would be|equals?)\s+"
        r"((?:[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?(?:\s*/\s*[-+]?\d+\.?\d*)?)|"
        r"(?:\d+\s*[\+\-\*/]\s*\d+))"
        r"(?:\s|\.|,|!|\?|$)"
    )
    matches = [m.group(1) for m in pattern.finditer(text)]

    if matches:
        values = []
        for raw in matches:
            parsed = parse_number_like(raw)
            if parsed is not None:
                values.append((parsed, raw))

        if len(values) >= 2:
            first_val, _ = values[0]
            last_val, _ = values[-1]
            if abs(last_val) > 1e-9:
                ratio = abs(first_val - last_val) / max(abs(first_val), abs(last_val))
                if ratio > 0.1:
                    return first_val
            return last_val

        for raw in reversed(matches):
            parsed = parse_number_like(raw)
            if parsed is not None:
                return parsed

    # 5. Last number fallback
    numbers = re.findall(r"([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)", text)
    if numbers:
        for n in reversed(numbers):
            try:
                v = float(n)
                if v == 0 or abs(v) >= 1e8:
                    continue
                if v in (10.0, 15.0, 20.0, 25.0, 30.0):
                    idx = text.rfind(n)
                    if idx >= 0 and idx + len(n) < len(text) and text[idx + len(n)] == '%':
                        continue
                return v
            except ValueError:
                continue

    return None


def is_correct(prediction: float | None, ground_truth: float, precision: int = 2,
                rel_tol: float = 0.01) -> bool:
    """Check if prediction matches ground truth within tolerance.

    Uses max(precision_tol, |GT| × rel_tol) as threshold.
    Precision tolerance = 0.5 × 10^(-precision).
    """
    if prediction is None:
        return False
    precision_tol = 0.5 * 10 ** (-precision)
    threshold = max(precision_tol, abs(ground_truth) * rel_tol)
    return abs(prediction - ground_truth) <= threshold
