"""Coverage should be useful without claiming scientific validity."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from papertrail.audit import audit
from papertrail.coverage import coverage
from papertrail.experiment import run_experiment
from papertrail.project import EVIDENCE_FIELDS, initialize
from papertrail.report import render_html
from papertrail.storage import csv_text, read_csv, replace_text

ROOT = Path(__file__).resolve().parents[1]


class CoverageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = initialize(Path(temporary.name) / "demo", demo=True)
        run_experiment(self.root)

    def test_computed_demo_links_and_honest_gaps(self):
        result = coverage(audit(self.root))
        self.assertEqual([], result["errors"])
        self.assertEqual({
            "references": 2,
            "references_cited": 2,
            "references_with_evidence_cards": 2,
            "evidence_cards": 2,
            "cards_marked_reviewed": 2,
            "cards_with_locator_and_note": 2,
            "cards_used_in_draft": 2,
            "results": 6,
            "results_used_in_draft": 2,
        }, result["counts"])
        kinds = [gap["kind"] for gap in result["gaps"]]
        self.assertEqual(4, kinds.count("result_not_in_draft"))
        self.assertIn("unfinished_draft", kinds)
        self.assertNotIn("review_pending", kinds)

    def test_gaps_change_after_manual_record_edits(self):
        rows = read_csv(self.root / "evidence.csv", EVIDENCE_FIELDS)
        rows[0]["reviewed"] = "no"
        rows[0]["locator"] = ""
        rows[0]["note"] = ""
        replace_text(self.root / "evidence.csv", csv_text(rows, EVIDENCE_FIELDS))
        result = coverage(audit(self.root))
        self.assertEqual(1, result["counts"]["cards_marked_reviewed"])
        self.assertEqual(1, result["counts"]["cards_with_locator_and_note"])
        self.assertIn(("review_pending", "C1"), {(g["kind"], g["item"]) for g in result["gaps"]})
        self.assertIn(("locator_or_note_missing", "C1"), {(g["kind"], g["item"]) for g in result["gaps"]})

    def test_unknown_reference_is_error_not_false_coverage(self):
        (self.root / "manuscript.md").write_text("[@lewis2020] [@missing2026]", encoding="utf-8")
        result = coverage(audit(self.root))
        self.assertEqual(1, result["counts"]["references_cited"])
        self.assertIn("missing_reference", {e["code"] for e in result["errors"]})

    def test_fenced_citations_and_claims_are_not_counted(self):
        (self.root / "manuscript.md").write_text("~~~md\n[@lewis2020] {{claim:C1}} {{run:demo-overlap-mrr}}\n~~~\n", encoding="utf-8")
        result = coverage(audit(self.root))
        self.assertEqual(0, result["counts"]["references_cited"])
        self.assertEqual(0, result["counts"]["cards_used_in_draft"])
        self.assertEqual(0, result["counts"]["results_used_in_draft"])

    def test_invalid_workspace_has_no_coverage(self):
        (self.root / "evidence.csv").write_text("broken,header\n", encoding="utf-8")
        result = coverage(audit(self.root))
        self.assertEqual({}, result["counts"])
        self.assertEqual([], result["gaps"])
        self.assertEqual("input_error", result["errors"][0]["code"])

    def test_cli_json_and_exit_status_and_read_only(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        cmd = [sys.executable, "-m", "papertrail", "coverage", str(self.root), "--json"]
        ok = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, ok.returncode, ok.stderr)
        self.assertEqual(2, json.loads(ok.stdout)["counts"]["cards_marked_reviewed"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()})
        with (self.root / "manuscript.md").open("a", encoding="utf-8") as f:
            f.write("\n[@missing2026]\n")
        broken = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(2, broken.returncode, broken.stderr)
        self.assertIn("missing_reference", {e["code"] for e in json.loads(broken.stdout)["errors"]})

    def test_html_report_includes_optional_connections_and_escaped_pending_cards(self):
        result = audit(self.root)
        result["evidence"][0].update(claim_id='<img src=x onerror="bad()">', reviewed="no", locator="")
        rendered = render_html(result)
        self.assertIn("写作前的连接检查", rendered)
        self.assertIn("可选连接", rendered)
        self.assertIn("待复核", rendered)
        self.assertIn("demo-overlap-r1", rendered)
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;img", rendered)

    def test_invalid_project_report_does_not_infer_coverage(self):
        (self.root / "evidence.csv").write_text("broken,header\n", encoding="utf-8")
        rendered = render_html(audit(self.root))
        self.assertIn("无法统计", rendered)
        self.assertNotIn("对应记录总数", rendered)


if __name__ == "__main__":
    unittest.main()
