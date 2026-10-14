"""Build tested portable and source downloads; exclude personal workspaces."""

import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from papertrail import __version__


def main():
    subprocess.run([sys.executable, str(ROOT / "scripts/build_zipapp.py")], check=True)
    dist = ROOT / "dist"
    archive = dist / f"papertrail-research-v{__version__}.zip"
    included = ("papertrail", "scripts", "tests", "docs", "templates", "prompts", "assets", ".github")
    paths = [p for directory in included for p in (ROOT / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    paths += [ROOT / name for name in ("README.md", "README.en.md", "pyproject.toml", "LICENSE", "AGENTS.md", "CONTRIBUTING.md", "CHANGELOG.md", "ROADMAP.md", ".gitignore")]
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(paths):
            info = zipfile.ZipInfo(f"papertrail-research/{path.relative_to(ROOT).as_posix()}", date_time=(2026, 10, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            handle.writestr(info, path.read_bytes())
    with tempfile.TemporaryDirectory() as directory:
        command = [sys.executable, str(dist / "papertrail.pyz"), "demo", str(Path(directory) / "portable-study")]
        subprocess.run(command, cwd=directory, check=True, stdout=subprocess.DEVNULL)
    files = [dist / "papertrail.pyz", archive]
    checksum = "".join(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name + "\n" for path in files)
    (dist / "SHA256SUMS.txt").write_text(checksum, encoding="utf-8", newline="\n")
    for path in files:
        print(f"{path.name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
