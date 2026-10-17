"""Regression tests for unfinished draft detection."""
import unittest
import tempfile
from pathlib import Path
from papertrail.audit import audit
from papertrail.project import initialize
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

    def test_check_and_coverage_agree_on_real_workspace_prose(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = initialize(Path(temporary) / "study")
            for text, expected in (("todo: verify", True), ("ToDo note", True), ("待补证据", True),
                                   ("METHODOTOMY", False), ("`todo`", False),
                                   ("<!-- ToDo -->", False), ("~~~\nTODO\n~~~", False)):
                with self.subTest(text=text):
                    (root / "manuscript.md").write_text(text, encoding="utf-8")
                    result = audit(root)
                    self.assertEqual(expected, "unfinished_draft" in {w["code"] for w in result["warnings"]})
                    self.assertEqual(expected, "unfinished_draft" in {g["kind"] for g in coverage(result)["gaps"]})
