import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from papertrail.audit import audit
from papertrail.project import RUN_FIELDS, initialize
from papertrail.references import import_csl
from papertrail.report import export_report
from papertrail.results import import_results
from papertrail.storage import ProjectError, csv_text, json_text, read_bytes, read_csv, read_json, replace_text

ROOT = Path(__file__).resolve().parents[1]


class ResultsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = initialize(Path(self.temporary.name) / "my study")
        self.source = Path(self.temporary.name) / "results.csv"
        self.original = b'\xef\xbb\xbfmethod,metric,value,n\r\n"baseline, first",accuracy,0.2500,4\r\nthreshold,accuracy,7.5e-1,4\r\n'
        self.source.write_bytes(self.original)

    def load(self, **changes):
        arguments = {"run_id": "course", "dataset": "Public teaching fixture", "command": "DO_NOT_EXECUTE --fixture", "label": "toy"}
        arguments.update(changes)
        return import_results(self.root, self.source, **arguments)

    def state(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def assert_artifact_error(self):
        self.assertIn("artifact_error", {e["code"] for e in audit(self.root)["errors"]})

    def test_empty_workspace_guidance_is_not_a_missing_citation(self):
        result = audit(self.root)
        self.assertEqual([], result["errors"])
        self.assertIn("unfinished_draft", {w["code"] for w in result["warnings"]})

    def test_original_bytes_round_trip_and_report_values(self):
        self.load()
        self.assertEqual(self.original, (self.root / "artifacts/course.source.csv").read_bytes())
        result = audit(self.root)
        self.assertEqual([], result["errors"])
        self.assertEqual(["course-001", "course-002"], [r["run_id"] for r in result["runs"]])
        self.assertEqual("0.2500", result["runs"][0]["value"])
        self.assertIn("external_command_unverified", {w["code"] for w in result["warnings"]})
        replace_text(self.root / "manuscript.md", "{{run:course-001}} / {{run:course-002}}")
        export_report(audit(self.root), self.root / "report")
        self.assertIn("0.2500（n=4，toy", (self.root / "report/draft.md").read_text(encoding="utf-8"))
        self.assertIn("25.000%", (self.root / "report/index.html").read_text(encoding="utf-8"))

    def test_repeated_group_or_existing_snapshot_preserves_files(self):
        self.load()
        before = self.state()
        with self.assertRaises(ProjectError):
            self.load()
        self.assertEqual(before, self.state())
        (self.root / "artifacts/other.source.csv").write_bytes(b"existing work")
        before = self.state()
        with self.assertRaises(ProjectError):
            self.load(run_id="other")
        self.assertEqual(before, self.state())

    def test_invalid_csv_has_no_partial_writes(self):
        examples = [b"method,metric,value,n\n", b"wrong,header\na,b\n",
                    b"method,metric,value,n\na,accuracy,0.5\n", b'method,metric,value,n\n"unfinished,accuracy,0.5,4\n',
                    b"method,metric,value,n\na,accuracy," + b"1" * 131073 + b",4\n"]
        for value in ("NaN", "Infinity", "-0.1", "1.1", "oops"):
            examples.append(f"method,metric,value,n\na,accuracy,{value},4\n".encode())
        for n in ("0", "-1", "1.5", "NaN", "４"):
            examples.append(f"method,metric,value,n\na,accuracy,0.5,{n}\n".encode())
        before = self.state()
        for content in examples:
            with self.subTest(content=content[:80]):
                self.source.write_bytes(content)
                with self.assertRaises(ProjectError):
                    self.load()
                self.assertEqual(before, self.state())

    def test_invalid_ids_and_required_provenance_preserve_project(self):
        before = self.state()
        for change in [{"run_id": name} for name in ("../bad", "a/b", "CON", "Lpt1", "a:b", "a" * 65)] + [{"label": ""}, {"dataset": " "}, {"command": " "}]:
            with self.subTest(change=change), self.assertRaises(ProjectError):
                self.load(**change)
            self.assertEqual(before, self.state())

    def test_generated_size_limit_checked_before_writes(self):
        before = self.state()
        with patch("papertrail.results.LIMIT", 100), self.assertRaises(ProjectError):
            self.load()
        self.assertEqual(before, self.state())

    def test_source_change_keeps_history_but_snapshot_change_is_detected(self):
        self.load()
        self.source.write_bytes(b"external source later replaced")
        self.assertEqual([], audit(self.root)["errors"])
        with (self.root / "artifacts/course.source.csv").open("ab") as handle:
            handle.write(b"changed")
        self.assert_artifact_error()

    def test_registered_input_change_is_detected(self):
        (self.root / "data.csv").write_bytes(b"original dataset")
        self.load(inputs=["data.csv"])
        self.assertEqual([], audit(self.root)["errors"])
        (self.root / "data.csv").write_bytes(b"changed dataset")
        self.assert_artifact_error()

    def test_unsafe_or_self_modified_input_is_refused_before_writes(self):
        before = self.state()
        for name in ("../results.csv", "experiments.csv", "missing.csv"):
            with self.subTest(name=name), self.assertRaises((ProjectError, OSError)):
                self.load(inputs=[name])
            self.assertEqual(before, self.state())

    def test_table_values_and_provenance_must_match_snapshot(self):
        self.load()
        original = read_csv(self.root / "experiments.csv", RUN_FIELDS)
        for field, value in (("value", "0.4"), ("n", "5"), ("method", "invented"), ("label", "real"), ("dataset", "other dataset"), ("command", "other command")):
            rows = [dict(row) for row in original]
            rows[0][field] = value
            replace_text(self.root / "experiments.csv", csv_text(rows, RUN_FIELDS))
            with self.subTest(field=field):
                self.assert_artifact_error()

    def test_changed_metadata_still_checked_against_original_csv(self):
        self.load()
        artifact = self.root / "artifacts/course.json"
        details = read_json(artifact)
        details["metrics"]["course-001"]["value"] = "0.9"
        replace_text(artifact, json_text(details))
        rows = read_csv(self.root / "experiments.csv", RUN_FIELDS)
        for row in rows:
            row["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
        replace_text(self.root / "experiments.csv", csv_text(rows, RUN_FIELDS))
        self.assert_artifact_error()

    def test_missing_member_of_imported_group_is_detected(self):
        self.load()
        rows = read_csv(self.root / "experiments.csv", RUN_FIELDS)
        replace_text(self.root / "experiments.csv", csv_text(rows[:1], RUN_FIELDS))
        self.assert_artifact_error()

    def test_snapshot_is_parsed_once_per_group(self):
        self.load()
        with patch("papertrail.results.read_bytes", wraps=read_bytes) as reader:
            self.assertEqual([], audit(self.root)["errors"])
        self.assertEqual(1, reader.call_count)

    def test_opaque_artifact_has_explicit_unverified_value_reminder(self):
        self.load()
        path = self.root / "artifacts/opaque.txt"
        path.write_bytes(b"external attachment")
        rows = read_csv(self.root / "experiments.csv", RUN_FIELDS)
        for row in rows:
            row.update(artifact="artifacts/opaque.txt", sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        replace_text(self.root / "experiments.csv", csv_text(rows, RUN_FIELDS))
        result = audit(self.root)
        self.assertEqual([], result["errors"])
        self.assertEqual(1, sum(w["code"] == "unverified_result_values" for w in result["warnings"]))

    def test_malformed_csv_in_project_is_a_controlled_audit_error(self):
        (self.root / "evidence.csv").write_text('claim_id,text,reference_key,locator,note,reviewed\n"unterminated', encoding="utf-8")
        self.assertEqual("input_error", audit(self.root)["errors"][0]["code"])

    def test_symlink_snapshot_is_refused(self):
        target = self.root / "artifacts/course.source.csv"
        try:
            target.symlink_to(self.source)
        except OSError as error:
            self.skipTest(str(error))
        before = (self.root / "experiments.csv").read_bytes()
        with self.assertRaises(ProjectError):
            self.load()
        self.assertEqual(before, (self.root / "experiments.csv").read_bytes())

    def test_cli_import_and_invalid_metric_exit_codes(self):
        command = [sys.executable, "-m", "papertrail", "import-results", str(self.root), str(self.source),
                   "--run-id", "course", "--label", "toy", "--dataset", "fixture", "--command", "DO_NOT_EXECUTE"]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, result.returncode, result.stderr)
        self.source.write_text("method,metric,value,n\na,accuracy,oops,4\n", encoding="utf-8")
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(2, result.returncode)
        self.assertNotIn("Traceback", result.stderr)

    def test_supplied_csl_example_does_not_mark_metadata_or_reading_reviewed(self):
        added = import_csl(self.root, ROOT / "examples/references.csl.json")
        self.assertEqual(["lewis2020", "thakur2021"], [r["key"] for r in added])
        self.assertTrue(all("checked_at" not in r and "reviewed" not in r for r in added))
        self.assertIn("metadata_unchecked", {w["code"] for w in audit(self.root)["warnings"]})


class CourseTests(unittest.TestCase):
    def test_classification_uses_training_labels_and_computes_test_scores(self):
        spec = importlib.util.spec_from_file_location("course_experiment", ROOT / "scripts/course_experiment.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        scores, predictions, model = module.calculate(ROOT / "examples/data/course.csv")
        self.assertEqual(["0.25", "0.75"], [r["value"] for r in scores])
        self.assertEqual(3.5, model["threshold"])
        self.assertEqual(4, len(predictions))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "flipped.csv"
            with (ROOT / "examples/data/course.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            for row in rows:
                if row["split"] == "test":
                    row["label"] = str(1 - int(row["label"]))
            source.write_text(csv_text(rows, ("id", "split", "feature", "label")), encoding="utf-8")
            changed, _, other_model = module.calculate(source)
        self.assertEqual(model, other_model)
        self.assertEqual(["0.75", "0.25"], [r["value"] for r in changed])


if __name__ == "__main__":
    unittest.main()
