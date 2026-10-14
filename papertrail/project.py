"""Create a research workspace without overwriting another project."""

from importlib.resources import files
from pathlib import Path

from .storage import ProjectError, csv_text, json_text, write_new

EVIDENCE_FIELDS = ("claim_id", "text", "reference_key", "locator", "note", "reviewed")
RUN_FIELDS = ("run_id", "method", "dataset", "n", "metric", "value", "artifact", "sha256", "label", "command")


def initialize(target, demo=False):
    target = Path(target)
    if target.exists() or target.is_symlink():
        raise ProjectError(f"Destination already exists; choose a new folder: {target}")
    target.mkdir(parents=True, exist_ok=False)
    (target / "artifacts").mkdir()
    if demo:
        source = files("papertrail").joinpath("templates", "demo")
        for item in source.iterdir():
            if item.is_dir():
                (target / item.name).mkdir()
                for child in item.iterdir():
                    write_new(target / item.name / child.name, child.read_text(encoding="utf-8"))
            else:
                write_new(target / item.name, item.read_text(encoding="utf-8"))
    else:
        write_new(target / "project.json", json_text({"schema_version": 1, "title": "我的第一个科研项目", "question": "请写下一个能用数据检验的具体问题", "stage": "planning"}))
        write_new(target / "references.json", "[]\n")
        write_new(target / "evidence.csv", csv_text([], EVIDENCE_FIELDS))
        write_new(target / "experiments.csv", csv_text([], RUN_FIELDS))
        write_new(target / "manuscript.md", "# 我的第一个科研项目\n\n## 问题\n\nTODO：我想检验什么？\n\n## 相关工作\n\nTODO：阅读原文，在 evidence.csv 记下证据，再写引用 [@citation-key]。\n\n## 方法与结果\n\nTODO：记录实验命令、数据版本和结果。\n\n## 局限\n\nTODO：结论适用于什么条件？\n")
    write_new(target / ".gitignore", "report*/\n.papertrail-*\n*.pdf\n.env*\n__pycache__/\n")
    return target
