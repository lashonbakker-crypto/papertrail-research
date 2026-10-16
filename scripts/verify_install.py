"""Validate installed package resources and entry points away from the source tree."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory) / "installed-study"
        for command in ([sys.executable, "-m", "papertrail", "demo", str(project)], ["papertrail", "check", str(project), "--json"]):
            result = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding="utf-8")
            if result.returncode:
                raise SystemExit(result.stderr or result.stdout)
        report = json.loads(result.stdout)
        assert report["errors"] == []
        assert report["counts"]["runs"] == 6
        assert (project / "report/draft.md").is_file()
        source = Path(directory) / "own-results.csv"
        source.write_text("method,metric,value,n\nfixture,accuracy,0.75,4\n", encoding="utf-8")
        command = [sys.executable, "-m", "papertrail", "import-results", str(project), str(source),
                   "--run-id", "installed", "--dataset", "teaching fixture", "--label", "toy", "--command", "NOT_EXECUTED"]
        imported = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding="utf-8")
        assert imported.returncode == 0, imported.stderr
        checked = subprocess.run(["papertrail", "check", str(project), "--json"], cwd=directory, capture_output=True, text=True, encoding="utf-8")
        assert checked.returncode == 0, checked.stderr or checked.stdout
        assert json.loads(checked.stdout)["counts"]["runs"] == 7
        assert (project / "artifacts/installed.source.csv").read_bytes() == source.read_bytes()
    print("Installed module, command, templates, benchmark, external import and report: OK")


if __name__ == "__main__":
    main()
