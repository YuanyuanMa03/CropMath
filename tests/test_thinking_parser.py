"""Tests for answer extraction under thinking-mode (chain-of-thought) output.

The main paper runs with thinking_mode=off. A control experiment runs
reasoning models with thinking_mode=on, which emits <think>...</think>
(or <thinking>...</thinking>) blocks before the final answer. These tests
guarantee the answer parser:

  1. Strips properly-closed thinking blocks and finds the answer after them.
  2. Handles truncated (unclosed) thinking blocks — generation cut at the
     token limit mid-thought — by NOT returning a spurious last number
     scraped from the reasoning trace.

Case (2) is the load-bearing one: if a reasoning model is truncated inside
its <think> block, the parser must return None (unparseable) rather than
hallucinate a number from the reasoning text, otherwise the scoring would
be corrupted by truncation artifacts.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from cropmath.answer_parser import extract_answer


class TestThinkingBlockStripping:
    """Properly-closed thinking blocks are removed; the answer survives."""

    def test_think_block_then_boxed(self):
        text = "<think>Let me compute 2+2. Wait that's not right.\n</think>\nThe answer is \\boxed{4}"
        assert extract_answer(text) == 4.0

    def test_thinking_block_then_boxed(self):
        text = "<thinking>Working through the formula...\n</thinking>\\boxed{0.613}"
        assert extract_answer(text) == 0.613

    def test_think_with_attributes(self):
        # Qwen-style <think> and some templates emit attributes
        text = "<think type=\"reasoning\">ignore this 99 number</think>\n#### 42"
        assert extract_answer(text) == 42.0

    def test_answer_inside_think_ignored_answer_after_used(self):
        # A number inside the thinking block (99) must NOT leak into the result
        # when a real answer follows the block.
        text = "<think>I first guessed 99 but that's wrong.</think>\nTherefore, the answer is 7.5"
        assert extract_answer(text) == 7.5

    def test_multiple_think_blocks(self):
        text = "<think>step1</think>middle<think>step2 with 123</think>\n\\boxed{8}"
        assert extract_answer(text) == 8.0


class TestTruncatedThinkingBlock:
    """Truncated (unclosed) thinking blocks must NOT yield a spurious number.

    When generation is cut at the token limit mid-thought, there is no final
    answer. The parser must return None so the row is scored honestly as
    unparseable, rather than scraping a random number from the reasoning.
    """

    def test_truncated_think_no_close_returns_none(self):
        # Generation stopped at token limit inside <think>; no answer emitted.
        text = "<think>Let me work through this. First I compute the leaf area index"
        assert extract_answer(text) is None

    def test_truncated_thinking_no_close_returns_none(self):
        text = "<thinking>So if Tmean is 19.4 and Topt is 26.6, then we need"
        assert extract_answer(text) is None

    def test_truncated_think_with_distractor_number_returns_none(self):
        # The reasoning contains numbers, but no real answer — must be None.
        text = "<think>I'll multiply 3.5 by 2.1 to get 7.35, but wait the formula says"
        assert extract_answer(text) is None

    def test_truncated_deepseek_placeholder_returns_none(self):
        text = "<｜place▁holder▁no1｜>Reasoning about methane emission factor"
        assert extract_answer(text) is None


class TestNonThinkingFallback:
    """Normal (non-thinking) output still parses as before — no regression."""

    def test_plain_boxed(self):
        assert extract_answer("\\boxed{123.45}") == 123.45

    def test_plain_gsm8k(self):
        assert extract_answer("Some work.\n#### 1000") == 1000.0

    def test_last_number_fallback(self):
        assert extract_answer("The result we computed is 0.42") == 0.42

    def test_empty_text(self):
        assert extract_answer("") is None
        assert extract_answer("no numbers here at all") is None


class TestEdgeCases:
    """Mixed and adversarial cases."""

    def test_think_closed_but_no_answer(self):
        # Thinking block closed, but no parseable answer follows -> None
        text = "<think>done thinking</think>"
        assert extract_answer(text) is None

    def test_answer_before_think_block(self):
        # Unusual but possible: answer emitted before a trailing think block.
        # The parser should still find a number somewhere valid.
        text = "\\boxed{5.5}<think>let me verify</think>"
        assert extract_answer(text) == 5.5

    def test_think_block_with_math_content(self):
        # Thinking contains a calculation; real answer is different and after.
        text = "<think>3 * 4 = 12, but that's intermediate</think>\n#### 12.0"
        assert extract_answer(text) == 12.0
