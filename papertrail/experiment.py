"""An intentionally small lexical retrieval benchmark, not an LLM experiment."""

import math
import hashlib
import platform
import re
from collections import Counter
from importlib.resources import files

from .project import RUN_FIELDS
from .references import KEY_PATTERN
from .storage import ProjectError, csv_text, json_text, project_path, read_csv, read_json, replace_text, sha256, write_new


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def rank_documents(query, documents, method):
    query_terms = Counter(tokens(query))
    document_terms = [Counter(tokens(doc["text"])) for doc in documents]
    if method == "overlap":
        scores = [len(query_terms.keys() & terms.keys()) for terms in document_terms]
    elif method == "tfidf":
        frequency = Counter(term for terms in document_terms for term in terms)
        idf = {term: math.log((1 + len(documents)) / (1 + count)) + 1 for term, count in frequency.items()}
        q = {term: count * idf[term] for term, count in query_terms.items() if term in idf}
        qnorm = math.sqrt(sum(v * v for v in q.values()))
        scores = []
        for terms in document_terms:
            vector = {term: count * idf[term] for term, count in terms.items()}
            norm = math.sqrt(sum(v * v for v in vector.values()))
            dot = sum(value * vector.get(term, 0) for term, value in q.items())
            scores.append(dot / (norm * qnorm) if norm and qnorm else 0.0)
    else:
        raise ProjectError(f"Unknown method: {method}")
    return [documents[i]["id"] for i in sorted(range(len(documents)), key=lambda i: (-scores[i], documents[i]["id"]))]


def evaluate(documents, queries, method):
    if not isinstance(documents, list) or not documents or not isinstance(queries, list) or not queries:
        raise ProjectError("Benchmark needs nonempty document and query arrays")
    if any(not isinstance(d, dict) or not isinstance(d.get("id"), str) or not isinstance(d.get("text"), str) or not tokens(d["text"]) for d in documents):
        raise ProjectError("Each document needs an id and English alphanumeric text")
    identifiers = {doc["id"] for doc in documents}
    if len(identifiers) != len(documents):
        raise ProjectError("Duplicate document ids")
    query_ids, observations = set(), []
    for query in queries:
        if not isinstance(query, dict) or not isinstance(query.get("id"), str) or not isinstance(query.get("text"), str) or not tokens(query["text"]) or query.get("relevant") not in identifiers:
            raise ProjectError("Query needs id, English text, and one existing relevant document")
        if query["id"] in query_ids:
            raise ProjectError("Duplicate query ids")
        query_ids.add(query["id"])
        ranked = rank_documents(query["text"], documents, method)
        rank = ranked.index(query["relevant"]) + 1
        observations.append({"query_id": query["id"], "relevant": query["relevant"], "rank": rank, "top3": ranked[:3]})
    n = len(observations)
    metrics = {"MRR": round(sum(1 / item["rank"] for item in observations) / n, 6), "Recall@1": round(sum(item["rank"] <= 1 for item in observations) / n, 6), "Recall@3": round(sum(item["rank"] <= 3 for item in observations) / n, 6)}
    return metrics, observations


def run_experiment(root, run_id="demo"):
    if not KEY_PATTERN.fullmatch(run_id):
        raise ProjectError("run-id must start with an ASCII letter")
    docs_path = project_path(root, "data/documents.json")
    queries_path = project_path(root, "data/queries.json")
    documents, queries = read_json(docs_path), read_json(queries_path)
    table_path = project_path(root, "experiments.csv")
    existing = read_csv(table_path, RUN_FIELDS)
    relative = f"artifacts/{run_id}.json"
    artifact = project_path(root, relative)
    if artifact.exists():
        raise ProjectError("Experiment artifact exists; use a new --run-id")
    results, rows, measurements = {}, [], {}
    for method in ("overlap", "tfidf"):
        metrics, observations = evaluate(documents, queries, method)
        results[method] = observations
        for metric, value in metrics.items():
            suffix = {"MRR": "mrr", "Recall@1": "r1", "Recall@3": "r3"}[metric]
            identifier = f"{run_id}-{method}-{suffix}"
            if any(row["run_id"] == identifier for row in existing):
                raise ProjectError(f"Experiment id exists: {identifier}")
            record = {"method": method, "metric": metric, "value": value, "n": len(queries), "label": "toy"}
            measurements[identifier] = record
            rows.append({"run_id": identifier, **record, "dataset": f"Self-authored English toy corpus; {len(documents)} documents / {len(queries)} queries", "artifact": relative, "sha256": "", "command": f"python -m papertrail experiment PROJECT --run-id {run_id}"})
    payload = {"schema": "papertrail-retrieval-v1", "label": "toy", "python": platform.python_version(), "implementation_sha256": hashlib.sha256(files("papertrail").joinpath("experiment.py").read_bytes()).hexdigest(), "inputs": [{"path": "data/documents.json", "sha256": sha256(docs_path)}, {"path": "data/queries.json", "sha256": sha256(queries_path)}], "metrics": measurements, "per_query": results, "limitations": "Handwritten English microbenchmark, no language model, no held-out research claims. Deterministic lexical scoring; ties sort by document id."}
    write_new(artifact, json_text(payload))
    digest = sha256(artifact)
    for row in rows:
        row["sha256"] = digest
    replace_text(table_path, csv_text(existing + rows, RUN_FIELDS))
    return payload
