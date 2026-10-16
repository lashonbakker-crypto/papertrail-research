"""A tiny, self-authored classification exercise. Standard library only.

Choose a majority class and one threshold using TRAIN rows only. Test rows are
used once for scoring. This demonstrates the record flow, not generalization.
"""

import argparse
import csv
import io
import json
import math
from pathlib import Path


def calculate(source):
    with Path(source).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != ["id", "split", "feature", "label"]:
            raise ValueError("Expected id,split,feature,label")
        data = list(reader)
    seen = set()
    for row in data:
        if None in row or any(value is None for value in row.values()) or not row["id"] or row["id"] in seen:
            raise ValueError("Rows need distinct ids and exactly four fields")
        seen.add(row["id"])
        if row["split"] not in ("train", "test") or row["label"] not in ("0", "1"):
            raise ValueError("Expected train/test split and binary labels")
        row["feature"] = float(row["feature"])
        row["label"] = int(row["label"])
        if not math.isfinite(row["feature"]):
            raise ValueError("Feature must be finite")
    train = [row for row in data if row["split"] == "train"]
    test = [row for row in data if row["split"] == "test"]
    if not train or not test:
        raise ValueError("Both train and test rows are required")
    majority = int(sum(row["label"] for row in train) > len(train) / 2)  # ties choose 0
    values = sorted({row["feature"] for row in train})
    candidates = [values[0] - 1] + [(a + b) / 2 for a, b in zip(values, values[1:])] + [values[-1] + 1]
    threshold = min(candidates, key=lambda t: (sum(int(row["feature"] >= t) != row["label"] for row in train), t))
    predictions = [{"id": row["id"], "truth": row["label"], "majority": majority,
                    "threshold": int(row["feature"] >= threshold)} for row in test]
    results = [{"method": method, "metric": "accuracy",
                "value": str(sum(row[method] == row["truth"] for row in predictions) / len(predictions)),
                "n": len(predictions)} for method in ("majority", "threshold")]
    return results, predictions, {"train_n": len(train), "test_n": len(test),
                                  "majority": majority, "threshold": threshold, "label": "toy"}


def write_csv(path, rows, fields):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(buffer.getvalue())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("results", type=Path)
    parser.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args()
    try:
        outputs = [args.results, args.predictions]
        if len({p.resolve() for p in outputs}) != 2 or any(p.exists() or p.is_symlink() for p in outputs):
            raise ValueError("Choose two distinct, nonexistent output files")
        results, predictions, model = calculate(args.source)
        write_csv(args.predictions, predictions, ("id", "truth", "majority", "threshold"))
        write_csv(args.results, results, ("method", "metric", "value", "n"))
        print(json.dumps(model, indent=2))
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(2, f"course experiment: {error}\n")


if __name__ == "__main__":
    main()
