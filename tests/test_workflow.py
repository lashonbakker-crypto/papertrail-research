import copy
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from papertrail.audit import audit, prose_only
from papertrail.experiment import evaluate, rank_documents, run_experiment
from papertrail.project import EVIDENCE_FIELDS, RUN_FIELDS, initialize
from papertrail.report import export_report, render_html, safe_link
from papertrail.storage import ProjectError, csv_text, json_text, project_path, read_csv, read_json, replace_text


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = initialize(Path(self.temporary.name) / "study", demo=True)
        run_experiment(self.root)

    def codes(self):
        result = audit(self.root)
        return {item["code"] for item in result["errors"]}, {item["code"] for item in result["warnings"]}

    def change_rows(self, name, fields, edit):
        path = self.root / name
        rows = read_csv(path, fields)
        edit(rows)
        replace_text(path, csv_text(rows, fields))

    def test_complete_demo_has_no_errors_and_clear_toy_label(self):
        result = audit(self.root)
        self.assertEqual([], result["errors"])
        self.assertEqual({"references": 2, "citations": 2, "claims": 2, "runs": 6}, result["counts"])
        self.assertIn("toy_data", self.codes()[1])

    def test_missing_citation_key(self):
        with (self.root / "manuscript.md").open("a", encoding="utf-8") as f:
            f.write("\n参考 [@invented2026]。\n")
        self.assertIn("missing_reference", self.codes()[0])

    def test_multiple_citations_in_one_group(self):
        (self.root / "manuscript.md").write_text("[@lewis2020; @thakur2021]", encoding="utf-8")
        self.assertEqual(2, audit(self.root)["counts"]["citations"])

    def test_code_and_comments_are_not_citations(self):
        (self.root / "manuscript.md").write_text("[@lewis2020]\n```md\n[@fakeCode]\n```\n`[@fakeInline]`\n<!-- [@fakeComment] -->", encoding="utf-8")
        self.assertNotIn("missing_reference", self.codes()[0])

    def test_fence_with_inner_shorter_marker(self):
        self.assertEqual("[@real]", prose_only("````\n```\n[@notReal]\n````\n[@real]"))

    def test_reference_id_duplicates(self):
        path = self.root / "references.json"
        refs = read_json(path)
        refs.append(copy.deepcopy(refs[0]))
        replace_text(path, json_text(refs))
        self.assertIn("duplicate_id", self.codes()[0])
        self.assertIn("duplicate_doi", self.codes()[0])

    def test_doi_case_normalization_detects_duplicates(self):
        path = self.root / "references.json"
        refs = read_json(path)
        refs[1]["doi"] = "HTTPS://doi.org/" + refs[0]["doi"].upper()
        replace_text(path, json_text(refs))
        self.assertIn("duplicate_doi", self.codes()[0])

    def test_metadata_record_does_not_mean_human_review(self):
        self.change_rows("evidence.csv", EVIDENCE_FIELDS, lambda rows: rows[0].update(reviewed="no"))
        self.assertIn("human_review_pending", self.codes()[1])
        self.assertEqual(set(), self.codes()[0])

    def test_evidence_missing_source_and_location(self):
        self.change_rows("evidence.csv", EVIDENCE_FIELDS, lambda rows: rows[0].update(reference_key="missing", locator="", note=""))
        self.assertIn("missing_evidence_source", self.codes()[0])
        self.assertIn("evidence_location_missing", self.codes()[1])

    def test_missing_structured_claim(self):
        (self.root / "manuscript.md").write_text("{{claim:C404}}", encoding="utf-8")
        self.assertIn("missing_claim", self.codes()[0])

    def test_invalid_review_state(self):
        self.change_rows("evidence.csv", EVIDENCE_FIELDS, lambda rows: rows[0].update(reviewed="true"))
        self.assertIn("invalid_review_state", self.codes()[0])

    def test_missing_result(self):
        (self.root / "manuscript.md").write_text("{{run:ghost}}", encoding="utf-8")
        self.assertIn("missing_run", self.codes()[0])

    def test_mutated_artifact_is_detected(self):
        path = self.root / "artifacts/demo.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertIn("artifact_error", self.codes()[0])

    def test_deleted_artifact_is_detected(self):
        (self.root / "artifacts/demo.json").unlink()
        self.assertIn("artifact_error", self.codes()[0])

    def test_input_data_change_is_detected(self):
        path = self.root / "data/queries.json"
        queries = read_json(path)
        queries[0]["text"] = "Changed after experiment"
        replace_text(path, json_text(queries))
        self.assertIn("artifact_error", self.codes()[0])

    def test_table_value_must_match_original_result(self):
        self.change_rows("experiments.csv", RUN_FIELDS, lambda rows: rows[0].update(value="0.123456"))
        self.assertIn("artifact_error", self.codes()[0])

    def test_table_label_must_match_original_result(self):
        self.change_rows("experiments.csv", RUN_FIELDS, lambda rows: rows[0].update(label="real"))
        self.assertIn("artifact_error", self.codes()[0])

    def test_artifact_path_traversal_rejected(self):
        self.change_rows("experiments.csv", RUN_FIELDS, lambda rows: rows[0].update(artifact="../outside.json"))
        self.assertIn("artifact_error", self.codes()[0])

    def test_metrics_invalid_values(self):
        original = (self.root / "experiments.csv").read_text(encoding="utf-8")
        for value in ("NaN", "Infinity", "-0.1", "1.1", "not-a-number"):
            with self.subTest(value=value):
                replace_text(self.root / "experiments.csv", original)
                self.change_rows("experiments.csv", RUN_FIELDS, lambda rows: rows[0].update(value=value))
                self.assertIn("invalid_metric", self.codes()[0])

    def test_sample_size_requires_positive_integer(self):
        for value in ("0", "-1", "1.5", "", "NaN"):
            with self.subTest(value=value):
                self.change_rows("experiments.csv", RUN_FIELDS, lambda rows: rows[0].update(n=value))
                self.assertIn("invalid_metric", self.codes()[0])

    def test_missing_file_and_invalid_csv_are_errors(self):
        path = self.root / "evidence.csv"
        path.write_text("wrong,header\n", encoding="utf-8")
        self.assertIn("input_error", self.codes()[0])
        path.unlink()
        self.assertIn("input_error", self.codes()[0])

    def test_json_duplicate_keys_are_errors(self):
        (self.root / "project.json").write_text('{"schema_version":1,"title":"a","title":"b"}', encoding="utf-8")
        self.assertIn("input_error", self.codes()[0])

    def test_json_non_finite_number_is_error(self):
        (self.root / "project.json").write_text('{"schema_version":1,"title":"a","x":NaN}', encoding="utf-8")
        self.assertIn("input_error", self.codes()[0])
        (self.root / "project.json").write_text('{"schema_version":1,"title":"a","x":1e999}', encoding="utf-8")
        self.assertIn("input_error", self.codes()[0])

    def test_json_invalid_shape_is_error(self):
        (self.root / "references.json").write_text('null', encoding="utf-8")
        self.assertIn("input_error", self.codes()[0])

    def test_non_string_reference_key_reports_error(self):
        path = self.root / "references.json"
        refs = read_json(path)
        refs[0]["key"] = ["invalid"]
        replace_text(path, json_text(refs))
        self.assertIn("invalid_key", self.codes()[0])

    def test_report_escapes_untrusted_text(self):
        result = audit(self.root)
        result["title"] = '<script>alert("bad")</script>'
        result["references"][0]["title"] = '<img src=x onerror="bad()">'
        result["references"][0]["url"] = "javascript:alert(1)"
        rendered = render_html(result)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img", rendered)
        self.assertNotIn('href="javascript:', rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("Content-Security-Policy", rendered)

    def test_report_contains_real_values_and_expands_draft(self):
        output = Path(self.temporary.name) / "report"
        export_report(audit(self.root), output)
        self.assertEqual({"index.html", "audit.json", "handoff.md", "draft.md"}, {p.name for p in output.iterdir()})
        draft = (output / "draft.md").read_text(encoding="utf-8")
        self.assertNotIn("{{run:", draft)
        self.assertIn("n=12，toy", draft)
        self.assertIn("[@lewis2020]", draft)

    def test_report_refuses_overwrite(self):
        output = Path(self.temporary.name) / "report"
        output.mkdir()
        with self.assertRaises(ProjectError):
            export_report(audit(self.root), output)

    def test_initialization_refuses_existing_target(self):
        before = (self.root / "project.json").read_bytes()
        with self.assertRaises(ProjectError):
            initialize(self.root)
        self.assertEqual(before, (self.root / "project.json").read_bytes())

    def test_experiment_refuses_duplicate_run(self):
        before = (self.root / "experiments.csv").read_bytes()
        with self.assertRaises(ProjectError):
            run_experiment(self.root)
        self.assertEqual(before, (self.root / "experiments.csv").read_bytes())

    def test_new_experiment_preserves_previous_results(self):
        previous = read_json(self.root / "artifacts/demo.json")
        result = run_experiment(self.root, "replication")
        self.assertEqual(previous["per_query"], result["per_query"])
        self.assertEqual(12, len(read_csv(self.root / "experiments.csv", RUN_FIELDS)))
        self.assertEqual([], audit(self.root)["errors"])

    def test_symlink_artifact_is_rejected(self):
        artifact = self.root / "artifacts/demo.json"
        target = Path(self.temporary.name) / "outside.json"
        artifact.rename(target)
        try:
            artifact.symlink_to(target)
        except OSError as error:
            self.skipTest(f"Symlink creation unavailable on this environment: {error}")
        self.assertIn("artifact_error", self.codes()[0])


class RankingTests(unittest.TestCase):
    def test_known_ranking_and_metric(self):
        documents = [{"id": "a", "text": "apple"}, {"id": "b", "text": "banana"}]
        queries = [{"id": "q", "text": "banana", "relevant": "b"}]
        for method in ("overlap", "tfidf"):
            metrics, rows = evaluate(documents, queries, method)
            self.assertEqual(1.0, metrics["MRR"])
            self.assertEqual(1, rows[0]["rank"])

    def test_ties_sort_by_id_even_when_input_reversed(self):
        documents = [{"id": "b", "text": "same"}, {"id": "a", "text": "same"}]
        for method in ("overlap", "tfidf"):
            self.assertEqual(["a", "b"], rank_documents("unknown", documents, method))

    def test_reciprocal_rank_is_calculated_not_invented(self):
        documents = [{"id": "a", "text": "same"}, {"id": "b", "text": "same"}]
        metrics, _ = evaluate(documents, [{"id": "q", "text": "same", "relevant": "b"}], "overlap")
        self.assertEqual({"MRR": 0.5, "Recall@1": 0.0, "Recall@3": 1.0}, metrics)

    def test_empty_or_invalid_ground_truth_rejected(self):
        with self.assertRaises(ProjectError):
            evaluate([], [], "overlap")
        with self.assertRaises(ProjectError):
            evaluate([{"id": "a", "text": "valid"}], [{"id": "q", "text": "valid", "relevant": "missing"}], "overlap")

    def test_duplicate_document_and_query_ids_rejected(self):
        with self.assertRaises(ProjectError):
            evaluate([{"id": "a", "text": "one"}, {"id": "a", "text": "two"}], [{"id": "q", "text": "one", "relevant": "a"}], "tfidf")
        with self.assertRaises(ProjectError):
            evaluate([{"id": "a", "text": "one"}], [{"id": "q", "text": "one", "relevant": "a"}] * 2, "tfidf")

    def test_non_english_empty_token_query_rejected(self):
        with self.assertRaises(ProjectError):
            evaluate([{"id": "a", "text": "hello"}], [{"id": "q", "text": "你好", "relevant": "a"}], "tfidf")


if __name__ == "__main__":
    unittest.main()
