"""Bounded reads, strict JSON, and project-contained paths."""

import csv
import hashlib
import io
import json
import math
import os
import tempfile
from pathlib import Path

LIMIT = 8 * 1024 * 1024


class ProjectError(ValueError):
    pass


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProjectError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ProjectError(f"Non-finite JSON number: {value}")


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ProjectError(f"JSON number exceeds finite float range: {value}")
    return result


def read_bytes(path):
    path = Path(path)
    if path.is_symlink():
        raise ProjectError(f"Refusing symlink: {path}")
    with path.open("rb") as handle:
        data = handle.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ProjectError(f"File exceeds {LIMIT} bytes: {path}")
    return data


def read_text(path):
    return read_bytes(path).decode("utf-8-sig")


def read_json(path):
    return json.loads(read_text(path), object_pairs_hook=_pairs, parse_constant=_constant, parse_float=_float)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n"


def read_csv(path, fields):
    reader = csv.DictReader(io.StringIO(read_text(path), newline=""))
    if reader.fieldnames != list(fields):
        raise ProjectError(f"CSV header must be {','.join(fields)}: {path}")
    rows = list(reader)
    for number, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            raise ProjectError(f"Invalid CSV column count at row {number}: {path}")
    return rows


def csv_text(rows, fields):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def project_path(root, relative):
    root = Path(root)
    relative = Path(relative)
    if root.is_symlink() or not root.is_dir():
        raise ProjectError(f"Project must be an existing directory, not a symlink: {root}")
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ProjectError(f"Path must stay inside the project: {relative}")
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ProjectError(f"Refusing symlink in project path: {relative}")
    return candidate


def sha256(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()


def write_new(path, content):
    path = Path(path)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def replace_text(path, content):
    """Replace one explicit project data file; not a multi-file transaction."""
    path = Path(path)
    if path.is_symlink():
        raise ProjectError(f"Refusing symlink: {path}")
    fd, temporary = tempfile.mkstemp(prefix=".papertrail-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()
