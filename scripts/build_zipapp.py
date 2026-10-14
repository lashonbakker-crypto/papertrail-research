"""Build a portable archive including the demonstration corpus."""

import shutil
import sys
import tempfile
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from papertrail import __version__


def main():
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        staging = Path(directory)
        shutil.copytree(ROOT / "papertrail", staging / "papertrail", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        zipapp.create_archive(staging, destination / "papertrail.pyz", main="papertrail.cli:main", compressed=True)
    print(f"Built papertrail {__version__}: {destination / 'papertrail.pyz'}")


if __name__ == "__main__":
    main()
