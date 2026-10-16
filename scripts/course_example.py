"""Build the complete, locally computed results-import teaching example."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from papertrail.audit import audit
from papertrail.project import initialize
from papertrail.report import export_report
from papertrail.results import import_results
from papertrail.storage import ProjectError, json_text, replace_text


def run(project):
    initialize(project)
    data = project / "data"
    data.mkdir()
    shutil.copyfile(ROOT / "examples/data/course.csv", data / "course.csv")
    shutil.copyfile(ROOT / "scripts/course_experiment.py", data / "course_experiment.py")
    subprocess.run([sys.executable, str(data / "course_experiment.py"), str(data / "course.csv"),
                    str(data / "results.csv"), "--predictions", str(data / "predictions.csv")], check=True)
    import_results(project, data / "results.csv", run_id="course", label="toy",
                   dataset="Self-authored teaching data: 6 train / 4 test rows; not a research benchmark",
                   command="python PROJECT/data/course_experiment.py PROJECT/data/course.csv NEW_RESULTS.csv --predictions NEW_PREDICTIONS.csv",
                   inputs=("data/course.csv", "data/course_experiment.py", "data/predictions.csv"))
    replace_text(project / "project.json", json_text({"schema_version": 1, "title": "课程实验：把自己的结果接入 PaperTrail",
                 "question": "如何保留预测、指标和生成代码，并在草稿中引用可复核的结果？", "stage": "toy exercise"}))
    replace_text(project / "manuscript.md", """# 课程实验：结果记录练习

## 方法

只用六行训练数据决定多数类和单个分类阈值；训练误差相同时选较小阈值。
四行测试数据仅用于计分。逐条预测在 data/predictions.csv 中。

## 结果

多数类基线 accuracy 为 {{run:course-001}}；训练得到的阈值分类器为 {{run:course-002}}。

## 局限与下一步

这是手工编写的十行教学数据，只演示导入与一致性检查。四条测试记录不支持泛化或方法优越性结论。
没有引用文献或人工证据卡；实际课题需补充来源、真实数据授权、合理评估和独立复现。
更改结果源文件不会改写已保存的历史 CSV；更改登记值、快照或登记输入会被 check 检出。
""")
    result = audit(project)
    if result["errors"]:
        raise ProjectError(json_text(result["errors"]))
    export_report(result, project / "report")
    for row in result["runs"]:
        print(f"{row['run_id']}: {row['method']} accuracy={row['value']}, n={row['n']}, {row['label']}")
    print(f"0 errors; {len(result['warnings'])} reminders (including unverified external command and no evidence cards)")
    print(f"Report: {(project / 'report/index.html').resolve()}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, help="new directory; omit for a self-cleaning verification")
    args = parser.parse_args()
    try:
        if args.project is None:
            with tempfile.TemporaryDirectory() as temporary:
                run(Path(temporary) / "course-study")
        else:
            run(args.project)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"course example: {error}\n")


if __name__ == "__main__":
    main()
