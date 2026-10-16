"""Download a public release and verify bytes, tagged source and CLI outcomes.

Developer/release tooling only. PaperTrail itself remains standard-library only.
Use --downloads-dir for an offline check of already downloaded attachments.
"""

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MAIN = b"from papertrail.cli import main\nraise SystemExit(main())\n"
LIMIT = 16 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def blob_hash(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def source_hashes(source):
    if (source / ".git").exists():
        output = subprocess.check_output(["git", "-C", str(source), "ls-tree", "-rz", "HEAD"])
        result = {}
        for entry in output.split(b"\0"):
            if entry:
                metadata, name = entry.split(b"\t", 1)
                mode, kind, digest = metadata.decode().split()
                require(kind == "blob" and mode in ("100644", "100755"), "Expected only regular tracked source files")
                result[name.decode("utf-8")] = digest
        return result
    directories = ("papertrail", "scripts", "tests", "docs", "templates", "prompts", "assets", "examples", ".github")
    paths = [p for d in directories for p in (source / d).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    paths += [source / n for n in ("README.md", "README.en.md", "pyproject.toml", "LICENSE", "AGENTS.md", "CONTRIBUTING.md", "CHANGELOG.md", "ROADMAP.md", ".gitignore")]
    return {p.relative_to(source).as_posix(): blob_hash(p.read_bytes()) for p in paths}


def verify(downloads, tag, source):
    version = tag[1:]
    names = {"papertrail.pyz", f"papertrail-research-{tag}.zip"}
    lines = (downloads / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    manifest = {}
    for line in lines:
        digest, name = line.split()
        require(re.fullmatch(r"[0-9a-f]{64}", digest) and name in names and name not in manifest, "Invalid or repeated checksum entry")
        manifest[name] = digest
    require(set(manifest) == names, "Checksum file must cover both attachments")
    for name, expected in manifest.items():
        require(hashlib.sha256((downloads / name).read_bytes()).hexdigest() == expected, f"SHA-256 mismatch: {name}")
    expected = source_hashes(source)
    prefix = "papertrail-research/"
    with zipfile.ZipFile(downloads / f"papertrail-research-{tag}.zip") as archive:
        infos = archive.infolist()
        require(len(infos) == len(expected) and {i.filename for i in infos} == {prefix + p for p in expected}, "Source archive file set differs from tagged source")
        for info in infos:
            name = info.filename[len(prefix):]
            require(stat.S_IFMT(info.external_attr >> 16) != stat.S_IFLNK, "Unexpected symlink in source archive")
            require(blob_hash(archive.read(info)) == expected[name], f"Source bytes differ: {name}")
        with zipfile.ZipFile(downloads / "papertrail.pyz") as portable:
            package = {p: digest for p, digest in expected.items() if p.startswith("papertrail/")}
            files = [i.filename for i in portable.infolist() if not i.is_dir()]
            require(len(files) == len(package) + 1 and set(files) == set(package) | {"__main__.py"}, "Portable archive has unexpected files")
            for name, digest in package.items():
                require(blob_hash(portable.read(name)) == digest, f"Portable package differs: {name}")
            require(portable.read("__main__.py") == MAIN, "Portable entry point must propagate the command exit code")
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            archive.extractall(work)
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)

            def call(command, cwd=work):
                return subprocess.run([sys.executable, *command], cwd=cwd, env=environment, capture_output=True, text=True, encoding="utf-8")

            pyz = str((downloads / "papertrail.pyz").resolve())
            installed_version = call([pyz, "--version"])
            require(installed_version.returncode == 0 and installed_version.stdout.strip() == f"papertrail {version}", "Downloaded version mismatch")
            project = work / "portable study"
            created = call([pyz, "demo", str(project)])
            require(created.returncode == 0, created.stderr or created.stdout)
            checked = call([pyz, "check", str(project), "--json"])
            require(checked.returncode == 0 and json.loads(checked.stdout)["counts"]["runs"] == 6, "Portable demo audit failed")
            if "papertrail/results.py" in expected:
                csv_source = work / "external-results.csv"
                csv_source.write_text("method,metric,value,n\nfixture,accuracy,0.75,4\n", encoding="utf-8")
                imported = call([pyz, "import-results", str(project), str(csv_source), "--run-id", "downloaded",
                                 "--dataset", "teaching fixture", "--label", "toy", "--command", "NOT_EXECUTED"])
                require(imported.returncode == 0, imported.stderr or imported.stdout)
                snapshot = project / "artifacts/downloaded.source.csv"
                require(snapshot.read_bytes() == csv_source.read_bytes(), "Portable import did not preserve CSV bytes")
                checked = call([pyz, "check", str(project), "--json"])
                require(checked.returncode == 0 and json.loads(checked.stdout)["counts"]["runs"] == 7, "Portable imported-results audit failed")
                with snapshot.open("ab") as handle:
                    handle.write(b"tampered")
                changed = call([pyz, "check", str(project), "--json"])
                require(changed.returncode == 2 and "artifact_error" in {i["code"] for i in json.loads(changed.stdout)["errors"]}, "Changed snapshot must fail audit")
            absent = call([pyz, "check", str(work / "missing"), "--json"])
            require(absent.returncode == 2 and json.loads(absent.stdout)["errors"], "Invalid project must return 2")
            with (project / "manuscript.md").open("a", encoding="utf-8") as handle:
                handle.write("\n[@notExists2026]\n")
            bad = call([pyz, "check", str(project), "--json"])
            require(bad.returncode == 2 and "missing_reference" in {i["code"] for i in json.loads(bad.stdout)["errors"]}, "Missing citation must return 2")
            source_result = call(["-m", "papertrail", "demo", str(work / "source study")], work / "papertrail-research")
            require(source_result.returncode == 0, source_result.stderr or source_result.stdout)
            if "examples/data/course.csv" in expected:
                course = call(["scripts/course_example.py"], work / "papertrail-research")
                require(course.returncode == 0 and "accuracy=0.25" in course.stdout and "accuracy=0.75" in course.stdout, course.stderr or course.stdout)
    print(f"{tag}: published checksums, {len(expected)} source files, portable bytes, version, demo, error exit codes and extracted source: OK")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default=os.environ.get("PAPERTRAIL_RELEASE_TAG"), required=not bool(os.environ.get("PAPERTRAIL_RELEASE_TAG")))
    parser.add_argument("--source-dir", type=Path, default=ROOT / "released-source" if (ROOT / "released-source").exists() else ROOT)
    parser.add_argument("--downloads-dir", type=Path)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "lashonbakker-crypto/papertrail-research"))
    args = parser.parse_args()
    require(re.fullmatch(r"v\d+\.\d+\.\d+", args.tag), "Tag must be vMAJOR.MINOR.PATCH")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository), "Invalid owner/repository")
    destination = args.downloads_dir
    if destination is None:
        destination = ROOT / "dist" / f"released-{args.tag}"
        destination.mkdir(parents=True, exist_ok=False)
        base = f"https://github.com/{args.repository}/releases/download/{args.tag}/"
        for name in ("papertrail.pyz", f"papertrail-research-{args.tag}.zip", "SHA256SUMS.txt"):
            with urlopen(Request(base + name, headers={"User-Agent": "PaperTrail release verification"}), timeout=60) as response:
                data = response.read(LIMIT + 1)
            require(len(data) <= LIMIT, "Download exceeds verification size limit")
            with (destination / name).open("xb") as handle:
                handle.write(data)
    verify(destination, args.tag, args.source_dir)


if __name__ == "__main__":
    main()
