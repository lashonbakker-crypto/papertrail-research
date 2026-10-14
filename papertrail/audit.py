"""Check structured provenance. A passing audit is not a scientific review."""

import re
from collections import Counter
from decimal import Decimal, InvalidOperation

from .project import EVIDENCE_FIELDS, RUN_FIELDS
from .references import KEY_PATTERN, normalize_doi
from .storage import ProjectError, project_path, read_csv, read_json, read_text, sha256


def prose_only(text):
    """Ignore fenced code, inline code, and HTML comments in citation scans."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines, fence, result = text.splitlines(), None, []
    for line in lines:
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
                fence = None
            continue
        if match:
            fence = match[1]
            continue
        result.append(re.sub(r"(`+).*?\1", "", line))
    return "\n".join(result)


def audit(root):
    errors, warnings = [], []

    def issue(level, code, location, message):
        (errors if level == "error" else warnings).append({"code": code, "location": location, "message": message})

    def duplicate(rows, key, location):
        counts = Counter(str(row.get(key, "")) for row in rows)
        for value, count in counts.items():
            if count > 1:
                issue("error", "duplicate_id", location, f"重复标识 {value!r} ({count} 次)")

    try:
        project = read_json(project_path(root, "project.json"))
        refs = read_json(project_path(root, "references.json"))
        evidence = read_csv(project_path(root, "evidence.csv"), EVIDENCE_FIELDS)
        runs = read_csv(project_path(root, "experiments.csv"), RUN_FIELDS)
        raw_manuscript = read_text(project_path(root, "manuscript.md"))
        manuscript = prose_only(raw_manuscript)
        if not isinstance(project, dict) or type(project.get("schema_version")) is not int or project["schema_version"] != 1 or not isinstance(project.get("title"), str):
            raise ProjectError("project.json requires schema_version=1 and a string title")
        if not isinstance(refs, list) or any(not isinstance(ref, dict) for ref in refs):
            raise ProjectError("references.json must be an array of objects")
    except (OSError, ValueError, UnicodeError) as error:
        issue("error", "input_error", "project", str(error))
        return {"title": "PaperTrail 项目检查", "errors": errors, "warnings": warnings, "counts": {}, "references": [], "evidence": [], "runs": []}

    duplicate(refs, "key", "references.json")
    duplicate(evidence, "claim_id", "evidence.csv")
    duplicate(runs, "run_id", "experiments.csv")
    ref_map, canonical_dois = {}, {}
    for index, ref in enumerate(refs, 1):
        where = f"references.json[{index}]"
        key = ref.get("key")
        if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
            issue("error", "invalid_key", where, "文献 key 格式错误")
            continue
        ref_map[key] = ref
        if not isinstance(ref.get("title"), str) or not ref["title"].strip():
            issue("error", "missing_title", where, f"{key} 缺少标题")
        if type(ref.get("year")) is not int or not 1000 <= ref["year"] <= 2200:
            issue("warning", "missing_year", where, f"{key} 缺少年份或年份格式错误")
        if not isinstance(ref.get("authors"), list) or not ref["authors"] or any(not isinstance(a, str) or not a.strip() for a in ref["authors"]):
            issue("warning", "missing_authors", where, f"{key} 缺少有效作者信息")
        source = ref.get("metadata_source", "")
        if not isinstance(source, str) or not source.startswith("https://") or not ref.get("checked_at"):
            issue("warning", "metadata_unchecked", where, f"{key} 元数据尚未独立核对")
        doi = ref.get("doi", "")
        if doi:
            try:
                if not isinstance(doi, str):
                    raise ProjectError("DOI must be text")
                doi = normalize_doi(doi)
                if doi in canonical_dois:
                    issue("error", "duplicate_doi", where, f"DOI 与 {canonical_dois[doi]} 重复")
                canonical_dois[doi] = key
            except ProjectError as error:
                issue("error", "invalid_doi", where, str(error))

    citations = sorted(set(re.findall(r"\[([^\]\n]+)\]", manuscript)))
    cited_keys = sorted({key for group in citations for key in re.findall(r"(?<![\w@])@([A-Za-z][A-Za-z0-9_.:-]*)", group)})
    for key in cited_keys:
        if key not in ref_map:
            issue("error", "missing_reference", "manuscript.md", f"引用 [@{key}] 不在文献表中")
    for key in ref_map:
        if key not in cited_keys:
            issue("warning", "unused_reference", "references.json", f"{key} 尚未在正文引用")

    claim_ids = set()
    for index, row in enumerate(evidence, 2):
        where = f"evidence.csv:{index}"
        claim_ids.add(row["claim_id"])
        if not KEY_PATTERN.fullmatch(row["claim_id"]) or not row["text"].strip():
            issue("error", "invalid_claim", where, "证据卡需要有效 claim_id 和论点文字")
        if row["reference_key"] not in ref_map:
            issue("error", "missing_evidence_source", where, f"证据来源 {row['reference_key']!r} 不存在")
        if row["reviewed"] not in ("yes", "no"):
            issue("error", "invalid_review_state", where, "reviewed 只能填写 yes 或 no")
        if row["reviewed"] != "yes":
            issue("warning", "human_review_pending", where, f"{row['claim_id']} 尚未由人阅读原文核对")
        if not row["locator"].strip() or not row["note"].strip():
            issue("warning", "evidence_location_missing", where, f"{row['claim_id']} 需要章节/页码定位和自己的阅读笔记")
    used_claims = set(re.findall(r"\{\{claim:([A-Za-z][A-Za-z0-9_.:-]*)\}\}", manuscript))
    for key in sorted(used_claims - claim_ids):
        issue("error", "missing_claim", "manuscript.md", f"论点 {key} 不在证据表中")

    run_ids, artifact_cache = set(), {}
    for index, row in enumerate(runs, 2):
        where = f"experiments.csv:{index}"
        run_ids.add(row["run_id"])
        if not KEY_PATTERN.fullmatch(row["run_id"]) or not row["method"].strip() or not row["metric"].strip():
            issue("error", "invalid_run", where, "实验需要有效 run_id、method、metric")
        try:
            if not re.fullmatch(r"[1-9]\d*", row["n"]):
                raise ValueError("n must be a positive integer")
            value = Decimal(row["value"])
            if not value.is_finite():
                raise ValueError("metric value must be finite")
            if row["metric"] in ("MRR", "Recall@1", "Recall@3", "accuracy", "precision", "recall") and not 0 <= value <= 1:
                raise ValueError("ratio metric must lie between 0 and 1")
        except (ValueError, InvalidOperation) as error:
            issue("error", "invalid_metric", where, str(error))
        if row["label"] not in ("toy", "real"):
            issue("error", "invalid_data_label", where, "label 只能填写 toy（教学）或 real（真实研究）")
        if row["label"] == "toy":
            issue("warning", "toy_data", where, f"{row['run_id']} 是教学小数据结果，不能当作真实科研结论")
        if not row["dataset"].strip() or not row["command"].strip():
            issue("error", "missing_run_provenance", where, "缺少数据描述或复现命令")
        try:
            artifact = project_path(root, row["artifact"])
            if not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
                raise ProjectError("缺少有效的 SHA-256")
            if row["artifact"] not in artifact_cache:
                actual = sha256(artifact)
                details = read_json(artifact) if artifact.suffix == ".json" else None
                artifact_cache[row["artifact"]] = actual, details
            actual, details = artifact_cache[row["artifact"]]
            if actual != row["sha256"]:
                raise ProjectError("附件内容已改变，与实验登记的 SHA-256 不一致")
            if isinstance(details, dict) and details.get("schema") == "papertrail-retrieval-v1":
                measurement = details.get("metrics", {}).get(row["run_id"])
                if not measurement or any(str(measurement.get(k)) != row[k] for k in ("method", "metric", "n", "label")) or Decimal(str(measurement.get("value"))) != Decimal(row["value"]):
                    raise ProjectError("实验表数值与原始结果附件不一致")
                for item in details.get("inputs", []):
                    if sha256(project_path(root, item["path"])) != item["sha256"]:
                        raise ProjectError(f"实验输入数据已改变: {item['path']}")
        except (OSError, ValueError, UnicodeError, KeyError, TypeError, InvalidOperation) as error:
            issue("error", "artifact_error", where, str(error))
    used_runs = set(re.findall(r"\{\{run:([A-Za-z][A-Za-z0-9_.:-]*)\}\}", manuscript))
    for key in sorted(used_runs - run_ids):
        issue("error", "missing_run", "manuscript.md", f"结果 {key} 不在实验表中")
    if "TODO" in manuscript or "待补" in manuscript:
        issue("warning", "unfinished_draft", "manuscript.md", "草稿包含 TODO / 待补内容")
    if not evidence:
        issue("warning", "no_evidence", "evidence.csv", "还没有证据卡")
    if not runs:
        issue("warning", "no_experiments", "experiments.csv", "还没有登记实验")
    return {"title": project["title"], "question": project.get("question", ""), "errors": errors, "warnings": warnings, "counts": {"references": len(refs), "citations": len(cited_keys), "claims": len(evidence), "runs": len(runs)}, "references": refs, "evidence": evidence, "runs": runs, "manuscript": raw_manuscript}
