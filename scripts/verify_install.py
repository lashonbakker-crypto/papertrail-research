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
    print("Installed module, command, templates, benchmark and report: OK")


if __name__ == "__main__":
    main()
