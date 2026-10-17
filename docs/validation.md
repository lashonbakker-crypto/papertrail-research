# Validation record

## 0.3.0 local validation — 2026-10-17

- Linux / Python 3.12.14: **84 behavior tests passed**. Audit and coverage agree on mixed-case TODO, Chinese notes and ignored code/comments in a real workspace. HTML connections include optional unused metrics, pending cards and escaped untrusted IDs; unreadable inputs produce no inferred counts.
- The four exported report files remain compatible. Coverage does not execute commands, upload records or establish scientific validity. HTML structure and escaping are tested; browser rendering inspection of local report files is still unavailable in this environment.
- A fresh installed 0.3.0 package passed module/command, resource, imported CSV, coverage and HTML checklist checks away from the source tree. Locally built portable/source downloads passed the verification script, including coverage counts and checklist content, imported snapshot tampering and extracted-source examples. These were local builds; public-download and remote CI evidence is recorded separately. Historical evidence below applies only to its exact source.


## 0.2.0 本地验证 — 2026-10-16

- Linux / Python 3.12.14：**73 项行为测试通过**。新增覆盖 CSV 原字节快照（BOM/CRLF/引号）、非法数值/样本数/列/引号、超限写入预检、重复 ID/附件保留、表值/元数据/输入变动、同组记录缺失、未知附件提醒、CLI 退出码、安装版与单文件导入。
- `python scripts/course_example.py` 实际运行课程实验：6 行训练 / 4 行测试；majority accuracy=0.25，threshold accuracy=0.75，阈值 3.5。保留代码、数据、逐样本预测、CSV 快照、登记表和报告；0 错误、4 提醒。测试标签翻转不改变训练模型，只改变测试得分。所有数据明确为 toy，不支持研究优越性结论。
- 0.2.0 在独立虚拟环境构建并安装，源码目录外的模块、命令、资源、检索实验、自定义 CSV 导入与检查通过；未下载运行时依赖。
- 本地构建 0.2.0 源码包和 pyz，并运行发布验证器：核对校验文件、源码文件集合与字节、单文件包、版本、正常/错误命令、导入后的快照篡改失败，以及解压源码后的课程例子。这里检查的是本地构建物；正式下载验证另列。
- 自带 CSL-JSON 的两条公开元数据导入通过，保持未独立核对状态，不伪填人工阅读完成。空白项目的引用语法说明改为代码文本，避免假缺失引用。
- HTML 报告的内容、图表数值和转义由测试检查；当前浏览器禁止打开本地 file URL，未完成报告渲染目检。

## 0.2.0 远端 CI 与正式下载 — 2026-10-16

- 功能提交 `f60de440b2f92343174ebc697627ce7d7b8f07a7` 的 [矩阵 CI 38844789070](https://github.com/lashonbakker-crypto/papertrail-research/actions/runs/38844789070) 全部通过：Linux / Python 3.10、3.12、3.14；Windows / 3.12；Intel macOS / 3.12。每组包含 73 项行为测试、安装后源码目录外的入口/导入验证、单文件构建与课程例子。
- [发布工作流 38844919565](https://github.com/lashonbakker-crypto/papertrail-research/actions/runs/38844919565) 确认精确提交的 CI 通过后构建并发布 [v0.2.0](https://github.com/lashonbakker-crypto/papertrail-research/releases/tag/v0.2.0)，包含源码包、pyz 和 SHA256SUMS.txt。
- [公开附件下载复验 38845066135](https://github.com/lashonbakker-crypto/papertrail-research/actions/runs/38845066135) 在 Linux、Windows、Intel macOS 三组 Python 3.12 环境全部通过。逐组检查了实际 job 与日志。
- 下载复验实际从公开 Release 获取三份附件，核对两个程序附件的 SHA-256、源码归档的 **63 个文件**与精确标签的 Git blob、pyz 包内字节和入口、版本、源码目录外正常/错误退出码。另验证 CSV 导入与快照原字节、篡改快照后退出 2，以及解压源码课程例子计算出的 0.25 / 0.75。
- 下载检查使用发布附件，不使用本地重建替代品；不宣称 Apple Silicon、生产规模、Crossref 实际请求或研究结论有效性。下面 0.1.1 的执行记录仅代表历史版本。

## 0.1.1 历史记录 — 2026-10-14

## 本地验证

- Linux / Python 3.12：54 项行为测试通过。测试涵盖引用缺失、证据未复核、结果/输入变动、结构化数值不一致、导入冲突、路径越界和 HTML 转义。
- 源码 demo：2 篇文献、2 张证据卡、6 条结果；0 错误、7 提醒。
- 0.1.1 构建并安装到虚拟环境，源码目录外的模块、命令入口、模板、实验与报告验证通过。本地构建复用已安装的 setuptools，没有下载运行时依赖。
- 多附件校验文件的文档命令已实测：只下载 pyz 的场景通过，内容被改动时返回失败。
- 0.1.1 附件构建、解压源码 demo、单文件独立运行和本地发布验证脚本通过；修改下载文件后，验证脚本拒绝 SHA-256 不一致的文件。
- 演示动图摘取实际命令输出，只缩短路径；数据图读取真实 audit.json，经过视觉检查。数据预览是概览图，未冒充 HTML 浏览器截图。

## 已发布源码的矩阵 CI

0.1.1 功能版本提交为 `8cd2cd35d73eeb809e4c09fabe8388bc2a43ff8d`；[run 38523789446](https://github.com/lashonbakker-crypto/papertrail-research/actions/runs/38523789446) 的五组环境全部成功。

| 环境 | 行为测试 | 安装与源码目录外入口 | 单文件构建和 demo |
|---|---|---|---|
| Linux / Python 3.10 | 通过 | 通过 | 通过 |
| Linux / Python 3.12 | 通过 | 通过 | 通过 |
| Linux / Python 3.14 | 通过 | 通过 | 通过 |
| Windows / Python 3.12 | 通过 | 通过 | 通过 |
| Intel macOS / Python 3.12 | 通过 | 通过 | 通过 |

## 正式发布与真实下载

[v0.1.1](https://github.com/lashonbakker-crypto/papertrail-research/releases/tag/v0.1.1) 已发布，目标为上述提交；[发布工作流](https://github.com/lashonbakker-crypto/papertrail-research/actions/runs/38524113991) 成功，包含单文件版、源码归档和校验文件。

[下载复验 run 38524427034](https://github.com/lashonbakker-crypto/papertrail-research/actions/runs/38524427034) 在 Linux、Windows 和 Intel macOS 三组环境中全部成功，每组使用 Python 3.12。

每组实际从公开 Release 下载三份附件，而非重新构建本地替代品，然后执行：

1. 核对两个程序附件的 SHA-256。
2. 将源码归档的 54 个文件逐一比对精确发布标签的 Git blob 哈希；单文件内的包源码也逐一比对。
3. 核对单文件入口、版本号和源码目录外的 demo。
4. 检查不存在的项目与未知引用，进程必须返回 2。
5. 解压正式源码归档，独立运行源码 demo。

macOS 使用 Intel 运行器，本轮不宣称 Apple Silicon 验证。浏览器直接下载曾被取消；以上下载结果来自 GitHub Actions，不声称在当前浏览器完成下载。

## 修复记录

v0.1.0 的单文件入口曾忽略 CLI 返回码，出现终端显示错误、进程仍返回 0 的问题。扩充原有单文件行为测试后，修复前复现 `2 != 0`；改为 `raise SystemExit(main())` 后，正常 demo、无效项目和未知引用分别返回 0、2、2。旧版保留历史记录，单文件使用者应升级到 v0.1.1。

## 待核实与范围

- CLI 的真实 Crossref 元数据请求尚未实际运行；成功、404、网络失败、响应不匹配和畸形输入由夹具验证。发布下载联网验证不等于 Crossref 实测。
- HTML 报告有内容与转义检查，但本轮未完成浏览器渲染检查。
- 元数据核对、人工阅读登记、文件一致性和研究正确性是不同层次的证据。

## 教学实验结果

| Method | n | MRR | Recall@1 | Recall@3 |
|---|---:|---:|---:|---:|
| overlap | 12 | 1.0 | 1.0 | 1.0 |
| tfidf | 12 | 1.0 | 1.0 | 1.0 |

每条查询只有一个相关文档。语料为自编英文教学数据，没有独立留出集、模型训练或 LLM。结果由代码运行得到，不支持方法优越性或泛化能力的结论。
