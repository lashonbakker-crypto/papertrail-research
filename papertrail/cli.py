"""Command-line entry point."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .audit import audit
from .experiment import run_experiment
from .project import initialize
from .references import add_doi, import_csl
from .report import export_report
from .results import import_results
from .storage import ProjectError, json_text


def build_parser():
    parser = argparse.ArgumentParser(prog="papertrail", description="论文前，先把证据和实验整理清楚。Local research provenance checks.")
    parser.add_argument("--version", action="version", version=f"papertrail {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "demo"):
        sub = commands.add_parser(command, help="创建空白项目" if command == "init" else "运行可复现教学演示并生成报告")
        sub.add_argument("project", type=Path, help="尚不存在的新目录")
    check = commands.add_parser("check", help="检查文献、证据、结果和附件的一致性")
    check.add_argument("project", type=Path)
    check.add_argument("--json", action="store_true")
    report = commands.add_parser("report", help="生成本地 HTML / JSON / Markdown 报告")
    report.add_argument("project", type=Path)
    report.add_argument("--out", type=Path)
    exp = commands.add_parser("experiment", help="运行英文教学语料的 overlap / TF-IDF 检索实验")
    exp.add_argument("project", type=Path)
    exp.add_argument("--run-id", default="demo")
    csl = commands.add_parser("import-csl", help="从 Zotero 等工具导入 CSL-JSON 文献元数据")
    csl.add_argument("project", type=Path)
    csl.add_argument("source", type=Path)
    results = commands.add_parser("import-results", help="登记你自己的实验 CSV，保存原始快照并核对数值")
    results.add_argument("project", type=Path)
    results.add_argument("source", type=Path)
    results.add_argument("--run-id", required=True)
    results.add_argument("--dataset", required=True)
    results.add_argument("--command", dest="reproduction_command", required=True, help="仅记录，不执行")
    results.add_argument("--label", choices=("toy", "real"), required=True)
    results.add_argument("--input", action="append", default=[], help="需要持续核对 SHA-256 的项目相对路径，可重复")
    doi = commands.add_parser("add-doi", help="显式联网从 Crossref 获取一条 DOI 元数据")
    doi.add_argument("project", type=Path)
    doi.add_argument("doi")
    doi.add_argument("--key", required=True)
    return parser


def summarize(result):
    status = "NEEDS FIXES" if result["errors"] else "STRUCTURE CHECK OK"
    print(f"{status}: {len(result['errors'])} error(s), {len(result['warnings'])} reminder(s)")
    for level, items in (("ERROR", result["errors"]), ("NOTE", result["warnings"])):
        for item in items:
            print(f"{level} [{item['code']}] {item['location']}: {item['message']}")
    print("Human review of sources and research design is still required.")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            initialize(args.project)
            print(f"Created: {args.project}")
            return 0
        if args.command == "demo":
            initialize(args.project, demo=True)
            run_experiment(args.project)
            result = audit(args.project)
            destination = export_report(result, args.project / "report")
            summarize(result)
            print(f"Open in your browser: {(destination / 'index.html').resolve()}")
            return 2 if result["errors"] else 0
        if args.command == "experiment":
            result = run_experiment(args.project, args.run_id)
            for key, row in result["metrics"].items():
                print(f"{key}: {row['metric']}={row['value']:.6f}, n={row['n']}, toy")
            return 0
        if args.command == "import-csl":
            added = import_csl(args.project, args.source)
            print(f"Imported {len(added)} reference(s). Read and verify the source papers.")
            return 0
        if args.command == "import-results":
            result = import_results(args.project, args.source, run_id=args.run_id, dataset=args.dataset,
                                    command=args.reproduction_command, label=args.label, inputs=args.input)
            print(f"Recorded {len(result['metrics'])} measurement(s); original CSV preserved. Command was not executed.")
            return 0
        if args.command == "add-doi":
            print(json_text(add_doi(args.project, args.doi, args.key)), end="")
            return 0
        result = audit(args.project)
        if args.command == "check" and args.json:
            print(json_text(result), end="")
        else:
            summarize(result)
        if args.command == "report":
            output = args.out if args.out is not None else args.project / "report"
            export_report(result, output)
            print(f"Report: {(output / 'index.html').resolve()}")
        return 2 if result["errors"] else 0
    except (OSError, ValueError, UnicodeError) as error:
        print(f"papertrail: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
