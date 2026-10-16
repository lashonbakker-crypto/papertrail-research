"""Record external measurements without executing their reproduction command."""

import hashlib
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .project import RUN_FIELDS
from .storage import LIMIT, ProjectError, csv_rows, csv_text, json_text, project_path, read_bytes, read_csv, replace_text, sha256, write_new

SCHEMA = "papertrail-results-v1"
RESULT_FIELDS = ("method", "metric", "value", "n")
RATIO_METRICS = ("MRR", "Recall@1", "Recall@3", "accuracy", "precision", "recall")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
GROUP = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
RESERVED = {"CON", "PRN", "AUX", "NUL"} | {f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)}


def validate_group(group):
    if not isinstance(group, str) or not GROUP.fullmatch(group) or group.upper() in RESERVED:
        raise ProjectError("run-id must be a portable ASCII name: letter first, then letters/digits/_/-, at most 64 characters; no reserved device names")


def validate_metric(metric, value, n):
    if not re.fullmatch(r"[1-9][0-9]*", n):
        raise ProjectError("n must be a positive ASCII integer")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ProjectError("metric value must be a finite decimal number") from error
    if not number.is_finite():
        raise ProjectError("metric value must be finite")
    if metric in RATIO_METRICS and not 0 <= number <= 1:
        raise ProjectError("ratio metric must lie between 0 and 1")
    return number


def measurements(data, group, label):
    rows = csv_rows(data, RESULT_FIELDS)
    if not rows:
        raise ProjectError("Results CSV must contain at least one measurement")
    result = {}
    for record, raw in enumerate(rows, 2):
        row = {key: value.strip() for key, value in raw.items()}
        if not row["method"] or not row["metric"] or not row["value"]:
            raise ProjectError(f"Results record {record} needs method, metric and value")
        validate_metric(row["metric"], row["value"], row["n"])
        result[f"{group}-{record - 1:03d}"] = {**row, "label": label, "source_record": record}
    return result


def _description(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ProjectError(f"{name} must be nonempty text")
    return value.strip()


def import_results(root, source, *, run_id, dataset, command, label, inputs=()):
    """Validate before writes, snapshot original bytes, then append registrations.

    The CSV replacement is atomic; the three-file operation is not a transaction.
    An interrupted I/O operation can leave a new orphan artifact for inspection.
    """
    validate_group(run_id)
    dataset, command = _description(dataset, "dataset"), _description(command, "command")
    if label not in ("toy", "real"):
        raise ProjectError("label must be explicitly set to toy or real")
    source = Path(source)
    if source.is_symlink():
        raise ProjectError("Refusing symlink results source")
    original = read_bytes(source)
    metrics = measurements(original, run_id, label)
    table = project_path(root, "experiments.csv")
    existing = read_csv(table, RUN_FIELDS)
    identifiers = [row["run_id"] for row in existing]
    if len(set(identifiers)) != len(identifiers) or set(identifiers) & metrics.keys():
        raise ProjectError("Experiment id collision; existing registrations were not changed")
    relative = f"artifacts/{run_id}.json"
    snapshot_relative = f"artifacts/{run_id}.source.csv"
    artifact, snapshot = project_path(root, relative), project_path(root, snapshot_relative)
    if artifact.exists() or snapshot.exists():
        raise ProjectError("Experiment artifact exists; use a new --run-id")
    input_records, seen = [], set()
    for item in inputs:
        path = project_path(root, item)
        name = path.relative_to(Path(root)).as_posix()
        if name == "experiments.csv" or name in seen:
            raise ProjectError("Inputs must be distinct files that this import does not modify")
        seen.add(name)
        input_records.append({"path": name, "sha256": sha256(path)})
    payload = {"schema": SCHEMA, "run_id": run_id, "label": label,
               "dataset": dataset, "command": command,
               "source_csv": {"path": snapshot_relative, "sha256": hashlib.sha256(original).hexdigest()},
               "inputs": input_records, "metrics": metrics,
               "limitations": "External measurements recorded, not rerun. Data nature is self-declared; consistency is not scientific validity."}
    content = json_text(payload)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    rows = [{"run_id": key, **{field: item[field] for field in RESULT_FIELDS},
             "dataset": dataset, "label": label, "command": command,
             "artifact": relative, "sha256": digest} for key, item in metrics.items()]
    updated = csv_text(existing + rows, RUN_FIELDS)
    for name, text in ((relative, content), ("experiments.csv", updated)):
        if len(text.encode("utf-8")) > LIMIT:
            raise ProjectError(f"Generated {name} would exceed {LIMIT} bytes; split the import")
    with snapshot.open("xb") as handle:
        handle.write(original)
    write_new(artifact, content)
    replace_text(table, updated)
    return payload


def verified_measurements(root, details):
    """Rebuild canonical measurements from the saved CSV, and check input bytes."""
    group, label = details.get("run_id"), details.get("label")
    validate_group(group)
    if label not in ("toy", "real"):
        raise ProjectError("Invalid imported-results label")
    _description(details.get("dataset"), "dataset")
    _description(details.get("command"), "command")
    snapshot = details.get("source_csv")
    if not isinstance(snapshot, dict) or snapshot.get("path") != f"artifacts/{group}.source.csv" or not DIGEST.fullmatch(str(snapshot.get("sha256", ""))):
        raise ProjectError("Invalid imported-results CSV snapshot record")
    data = read_bytes(project_path(root, snapshot["path"]))
    if hashlib.sha256(data).hexdigest() != snapshot["sha256"]:
        raise ProjectError("Original results CSV snapshot has changed")
    expected = measurements(data, group, label)
    if details.get("metrics") != expected:
        raise ProjectError("Results metadata disagrees with the original CSV snapshot")
    inputs = details.get("inputs")
    if not isinstance(inputs, list):
        raise ProjectError("Imported-results inputs must be an array")
    seen = set()
    for item in inputs:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not DIGEST.fullmatch(str(item.get("sha256", ""))):
            raise ProjectError("Invalid imported-results input record")
        path = project_path(root, item["path"])
        canonical = path.relative_to(Path(root)).as_posix()
        if canonical in seen:
            raise ProjectError("Repeated imported-results input")
        seen.add(canonical)
        if sha256(path) != item["sha256"]:
            raise ProjectError(f"Experiment input has changed: {item['path']}")
    return expected
