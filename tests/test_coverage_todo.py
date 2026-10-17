"""Regression tests for unfinished draft detection."""
import unittest
from papertrail.coverage import coverage

class DraftTodoTests(unittest.TestCase):
    def test_case_insensitive_todo_and_chinese_marker(self):
        base = {"title": "test", "errors": [], "counts": {"references": 0},
                "references": [], "evidence": [], "runs": [], "manuscript": ""}
        for marker in ("todo: verify", "ToDo check", "待补证据"):
            with self.subTest(marker=marker):
                result = coverage({**base, "manuscript": marker})
                self.assertIn("unfinished_draft", [gap["kind"] for gap in result["gaps"]])

    def test_word_inside_other_word_does_not_trigger(self):
        base = {"title": "test", "errors": [], "counts": {"references": 0},
                "references": [], "evidence": [], "runs": [], "manuscript": "METHODOTOMY"}
        self.assertNotIn("unfinished_draft", [gap["kind"] for gap in coverage(base)["gaps"]])
