import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from papertrail.project import initialize
from papertrail.references import add_doi, fetch_doi, import_csl, normalize_doi
from papertrail.storage import ProjectError, json_text, read_json

ROOT = Path(__file__).resolve().parents[1]


class ReferencesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = initialize(Path(self.temporary.name) / "new-study")
        self.csl = Path(self.temporary.name) / "csl.json"
        self.items = [{"id": "smith2020", "title": "A test metadata fixture", "author": [{"given": "A", "family": "Smith"}], "issued": {"date-parts": [[2020]]}, "DOI": "https://doi.org/10.1234/test", "URL": "https://example.org/paper"}]

    def save(self):
        self.csl.write_text(json_text(self.items), encoding="utf-8")

    def test_csl_import_metadata_not_claimed_verified(self):
        self.save()
        refs = import_csl(self.root, self.csl)
        self.assertEqual("smith2020", refs[0]["key"])
        self.assertEqual("10.1234/test", refs[0]["doi"])
        self.assertNotIn("checked_at", refs[0])
        self.assertIn("not independently verified", refs[0]["metadata_source"])

    def test_second_import_collision_preserves_previous_file(self):
        self.save()
        import_csl(self.root, self.csl)
        before = (self.root / "references.json").read_bytes()
        with self.assertRaises(ProjectError):
            import_csl(self.root, self.csl)
        self.assertEqual(before, (self.root / "references.json").read_bytes())

    def test_bad_second_item_is_all_or_nothing(self):
        self.items.append({"id": "bad", "title": ""})
        self.save()
        with self.assertRaises(ProjectError):
            import_csl(self.root, self.csl)
        self.assertEqual([], read_json(self.root / "references.json"))

    def test_duplicate_doi_with_different_key_rejected(self):
        self.items.append({**self.items[0], "id": "different"})
        self.save()
        with self.assertRaises(ProjectError):
            import_csl(self.root, self.csl)

    def test_unusable_csl_id_gets_documented_fallback(self):
        self.items[0]["id"] = "https://zotero.org/items/item1"
        self.save()
        self.assertEqual("ref1", import_csl(self.root, self.csl)[0]["key"])

    def test_normalize_doi_accepts_prefix_rejects_bad_syntax(self):
        self.assertEqual("10.1234/abc", normalize_doi("DOI:10.1234/ABC"))
        for value in ("", "not-a-doi", "10.1234/a b", "https://example.org/10.1234/abc"):
            with self.subTest(value=value), self.assertRaises(ProjectError):
                normalize_doi(value)

    def test_crossref_failure_does_not_change_project(self):
        with patch("papertrail.references.urlopen", side_effect=URLError("offline")):
            with self.assertRaises(ProjectError):
                add_doi(self.root, "10.1234/test", "smith2020")
        self.assertEqual([], read_json(self.root / "references.json"))

    def test_crossref_not_found_not_called_fake_paper(self):
        error = HTTPError("https://api.crossref.org", 404, "not found", {}, None)
        with patch("papertrail.references.urlopen", side_effect=error):
            with self.assertRaisesRegex(ProjectError, "DataCite"):
                fetch_doi("10.48550/arxiv.2005.11401")

    def test_crossref_success_records_metadata_only(self):
        payload = {"message": {"DOI": "10.1234/test", "title": ["Fixture title"], "author": [{"given": "A", "family": "Smith"}], "issued": {"date-parts": [[2020]]}}}
        with patch("papertrail.references.urlopen") as request:
            request.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            result = add_doi(self.root, "10.1234/test", "smith2020")
        self.assertEqual("Fixture title", result["title"])
        self.assertIn("checked_at", result)
        self.assertNotIn("reviewed", result)

    def test_crossref_response_identity_mismatch_rejected(self):
        with patch("papertrail.references.urlopen") as request:
            request.return_value.__enter__.return_value.read.return_value = b'{"message":{"DOI":"10.1234/other","title":["Fixture"]}}'
            with self.assertRaises(ProjectError):
                fetch_doi("10.1234/test")

    def test_malformed_date_and_author_shapes_are_controlled_errors(self):
        for change in ({"issued": "2020"}, {"issued": {"date-parts": [2020]}}, {"author": [{"family": ["Smith"]}]}):
            with self.subTest(change=change):
                self.items = [{"id": "fixture", "title": "Fixture", **change}]
                self.save()
                with self.assertRaises(ProjectError):
                    import_csl(self.root, self.csl)
                self.assertEqual([], read_json(self.root / "references.json"))

    def test_crossref_invalid_payload_shape_is_controlled_error(self):
        for payload in (b'null', b'{"message":null}', b'{"message":{"DOI":"10.1234/test","title":"wrong-shape"}}'):
            with self.subTest(payload=payload), patch("papertrail.references.urlopen") as request:
                request.return_value.__enter__.return_value.read.return_value = payload
                with self.assertRaises(ProjectError):
                    fetch_doi("10.1234/test")


class CommandTests(unittest.TestCase):
    def call(self, *args):
        return subprocess.run([sys.executable, "-m", "papertrail", *map(str, args)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")

    def test_real_cli_demo_check_report(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "研究 项目"
            created = self.call("demo", project)
            self.assertEqual(0, created.returncode, created.stderr)
            checked = self.call("check", project, "--json")
            self.assertEqual(0, checked.returncode, checked.stderr)
            self.assertEqual([], json.loads(checked.stdout)["errors"])
            self.assertTrue((project / "report/index.html").is_file())
            self.assertEqual(2, self.call("demo", project).returncode)
            self.assertEqual(2, self.call("report", project).returncode)
            self.assertEqual(0, self.call("report", project, "--out", Path(directory) / "report2").returncode)

    def test_cli_invalid_project_returns_json_error_and_status_two(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.call("check", Path(directory) / "missing", "--json")
            self.assertEqual(2, result.returncode)
            self.assertTrue(json.loads(result.stdout)["errors"])

    def test_documented_download_check_handles_multi_asset_manifest(self):
        document = (ROOT / "docs/03-cli.md").read_text(encoding="utf-8")
        command = re.search(r'^python -c "(import hashlib;[^\n]+)"$', document, re.M).group(1)
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "papertrail.pyz"
            original = b"public download fixture"
            archive.write_bytes(original)
            manifest = Path(directory) / "SHA256SUMS.txt"
            manifest.write_text(hashlib.sha256(original).hexdigest() + "  papertrail.pyz\n" + "0" * 64 + "  source-not-downloaded.zip\n", encoding="utf-8")
            valid = subprocess.run([sys.executable, "-c", command], cwd=directory, capture_output=True, text=True)
            self.assertEqual(0, valid.returncode, valid.stderr)
            self.assertEqual("SHA-256 OK", valid.stdout.strip())
            archive.write_bytes(original + b"changed")
            invalid = subprocess.run([sys.executable, "-c", command], cwd=directory, capture_output=True, text=True)
            self.assertEqual(2, invalid.returncode, invalid.stderr)
            self.assertEqual("SHA-256 MISMATCH", invalid.stdout.strip())

    def test_portable_archive_runs_outside_source(self):
        built = subprocess.run([sys.executable, str(ROOT / "scripts/build_zipapp.py")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, built.returncode, built.stderr)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "portable-study"
            result = subprocess.run([sys.executable, str(ROOT / "dist/papertrail.pyz"), "demo", str(target)], cwd=directory, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((target / "data/queries.json").is_file())
            self.assertTrue((target / "report/draft.md").is_file())
            source = Path(directory) / "results.csv"
            source.write_text("method,metric,value,n\nfixture,accuracy,0.75,4\n", encoding="utf-8")
            command = [sys.executable, str(ROOT / "dist/papertrail.pyz"), "import-results", str(target), str(source),
                       "--run-id", "portable", "--dataset", "fixture", "--label", "toy", "--command", "NOT_EXECUTED"]
            imported = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, imported.returncode, imported.stderr)
            self.assertEqual(source.read_bytes(), (target / "artifacts/portable.source.csv").read_bytes())
            invalid = subprocess.run([sys.executable, str(ROOT / "dist/papertrail.pyz"), "check", str(Path(directory) / "missing"), "--json"], cwd=directory, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(2, invalid.returncode, invalid.stdout)
            self.assertTrue(json.loads(invalid.stdout)["errors"])
            with (target / "manuscript.md").open("a", encoding="utf-8") as handle:
                handle.write("\n[@notExists2026]\n")
            broken = subprocess.run([sys.executable, str(ROOT / "dist/papertrail.pyz"), "check", str(target), "--json"], cwd=directory, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(2, broken.returncode, broken.stdout)
            self.assertIn("missing_reference", {item["code"] for item in json.loads(broken.stdout)["errors"]})


if __name__ == "__main__":
    unittest.main()
