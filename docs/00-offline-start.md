# 先下载跑通，再逐步开始自己的课题

你可以把 PaperTrail 理解为一个科研资料检查员：一条论点对应哪篇文献、一个数值对应哪次实验，都有记录能查。

## 从本次交付包运行

需要 Python 3.10 或以上，不需要安装第三方包，也不需要 API key。

解压 `PaperTrail_v0.1.0_bundle.zip`，打开解压后的文件夹终端：

```bash
cd papertrail-research
python -m papertrail demo my-first-study
```

打开新生成的 `my-first-study/report/index.html`。应有 2 篇文献、2 张证据卡、6 条结果记录，0 个错误和 7 项提醒。提醒说明这个例子使用教学数据，而且草稿还有 TODO。

也可在交付包根目录直接运行 `python papertrail.pyz demo my-first-study`。这与源码 demo 使用同一套实现，仍需要 Python。

## 十分钟理解它

1. 先打开报告，找到“论点背后的证据”，再打开项目中的 `evidence.csv`。一张证据卡记录你准备写什么、依据哪篇文章、原文在哪里，以及你是否已经人工阅读复核。
2. 在 `manuscript.md` 最后添加一行 `参考 [@notExists2026]`。运行 `python -m papertrail check my-first-study`，应看到 `missing_reference` 和退出码 2。删掉这一行，再检查应恢复为 0。
3. 打开 `experiments.csv`，找到 `artifact` 与 `sha256` 两列，再看 `artifacts/demo.json`。表中的数值、原始结果和输入文件指纹应该对得上。
4. 修改 JSON 附件里的任意字符，再运行检查。它应报告 `artifact_error`。用一个全新的项目目录重跑 demo，保留旧文件方便对比。

## 哪些内容适合你现在学

按这个顺序读：[7 天入门](01-first-week.md) → [工作流](02-workflow.md) → [命令说明](03-cli.md) → `papertrail/cli.py` → `papertrail/audit.py`。

准备大创、进课题组或整理保研科研材料时，先用它记录自己实际读过、做过、能解释的内容。代码会核对选定结构和文件的一致性；研究问题是否有价值、文献是否支持论点、实验是否公平，仍要你和导师判断。

也可以从 GitHub 克隆源码，或从 Release 下载 `papertrail.pyz`，按[命令说明](03-cli.md)校验后运行。若下载源码归档 `papertrail-research-v0.1.0.zip`，解压后进入其中的 `papertrail-research` 目录，运行同一条 demo 命令。实际验证状态见[验证记录](validation.md)。
