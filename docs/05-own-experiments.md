# 把你自己的实验接进来 / Import your own measurements

`import-results` 接受你已经算出的指标，不执行程序，也不替你决定实验设计。先用公开教学数据熟悉，再在自己的本地项目中导入有权限使用的数据。代码和记录可公开复现时再考虑贡献，私人数据不必上传。

## 先跑完整例子

在源码根目录运行；只需 Python 3.10+：

```bash
python scripts/course_example.py course-study
python -m papertrail check course-study
```

打开 `course-study/report/index.html`。脚本会创建新项目，把原始十行数据和独立实验程序复制到 `data/`，实际运行程序，保留逐条测试预测，导入结果并生成草稿与报告。已有目录会拒绝覆盖。

| 方法 | 如何决定模型 | 测试样本数 | 实际算出的 accuracy |
|---|---|---:|---:|
| majority | 只数训练标签，多数类相同则选 0 | 4 | 0.25 |
| threshold | 只用训练误差选择单个阈值，相同误差选较小阈值 | 4 | 0.75 |

阈值为 3.5。测试标签不参与选择；回归测试把测试标签全部翻转后，模型保持不变，得分随之改变。数据是手工写的 6 行训练 / 4 行测试样例，不支持泛化、统计显著性或方法优越性的结论。它与内置检索 demo 是两个独立练习；没有运行语言模型，也没有执行 RAG/BEIR。

你应看到 0 个错误、4 项提醒：两条 toy 数据、外部命令未重新执行、尚无证据卡。提醒不会因为脚本运行过就被隐藏；通用检查器没有重新执行该程序。

## 再换成你的结果

结果 CSV 必须是 UTF-8，可带 BOM，列名及顺序固定：

```csv
method,metric,value,n
my-baseline,accuracy,0.65,40
my-method,accuracy,0.70,40
```

上面只是**格式示意，数值没有被测量**，请使用你自己的实际输出。一个逻辑记录对应一个指标；同一方法有多个指标就写多行。支持正常 CSV 引号与 CRLF。指标值必须是有限十进制数，n 为正整数；已知的 MRR、Recall@1、Recall@3、accuracy、precision、recall 限定为 0–1，其他指标的含义和范围由你说明。

```bash
python -m papertrail import-results my-research results.csv --run-id trial1 --dataset "公开教学数据的具体版本与切分" --label toy --command "python my_experiment.py" --input data/evaluation.csv
python -m papertrail check my-research
python -m papertrail report my-research --out my-research/report-trial1
```

先把数据放到项目内的 `data/evaluation.csv`，再选择 `--input`。可以重复该参数，登记代码、数据或逐样本预测的指纹；不传时不核对额外输入。路径相对项目目录，不是相对当前终端目录。不能登记将被本次导入改写的 `experiments.csv`。复现命令只是一段记录，不会执行；示意命令需要改为真实可复现步骤。

`--label toy` 表示教学或模拟数据；确属真实研究结果时才自报 `--label real`。工具不能验证这一声明。`--run-id` 必须以 ASCII 字母开头，之后仅用字母、数字、`_`、`-`，最多 64 字符；Windows 设备名如 CON、LPT1 会拒绝。

## 会留下哪些记录

| 文件 | 保存的内容 |
|---|---|
| `artifacts/trial1.source.csv` | 导入时原始 CSV 字节，包括 BOM、引号和换行 |
| `artifacts/trial1.json` | `papertrail-results-v1` 元数据、源快照指纹、逐指标映射与可选输入指纹 |
| `experiments.csv` | 追加 `trial1-001`、`trial1-002` 等结果 ID，以及附件指纹、数据说明和命令 |
| `report-trial1/draft.md` | 将 `{{run:trial1-001}}` 展开为登记数值、样本数和数据性质 |

`check` 读取源快照、重新解析指标，比对 JSON 映射和实验表，再核对可选输入指纹。单独改表中的数值、样本数、方法、数据性质、数据说明或命令会报错；删除同组的一部分登记也会报错。源快照和 JSON 每组只解析一次。

外部的 `results.csv` 后来被修改时，保存的快照仍代表导入当时的历史；要登记新结果，请用新 ID。若想持续检查当前源文件，也可把它放入项目并显式列为 `--input`。已经登记的输入变动会使旧记录报错，所以真实课题要保留版本化数据与代码。

## 亲手制造一次错误

在课程例子的 `experiments.csv` 中，把第一条 `value` 从 `0.25` 改为 `0.99`，运行 `check`，应出现 `artifact_error` 并退出 2。恢复原值，再改 `data/course.csv` 任一数据，同样会报告输入变动。不要通过重新填写指纹来掩盖改动；另起项目或另存版本重跑，保留旧记录便于比较。

SHA-256 与数值比对用于发现记录不一致，不能阻止有人协调修改所有记录，也不是真实性签名。通用、不认识结构的附件只检查指纹，并提醒 `unverified_result_values`。外部命令始终提醒 `external_command_unverified`；独立复现、指标定义、泄漏检查和结论范围仍需人工判断。

所有输入验证在写入前完成；标识或目标附件冲突时不改旧文件。单文件上限 8 MiB，生成的 JSON/实验表超限也会在写入前拒绝。没有并发写锁或多文件事务；I/O 失败或中断可能留下未登记的新附件，需要检查后使用新 ID，不能宣称操作完全事务化。

## English quick path

Run `python scripts/course_example.py course-study` from the source root. It computes a majority baseline (accuracy 0.25) and a training-selected threshold (accuracy 0.75) on ten self-authored toy rows, saves predictions and code, imports the measured CSV, and generates the report. Four test cases do not establish generalization or superiority. The classifier is independent of the retrieval demo.

For your own output, use the exact CSV header `method,metric,value,n` and the `import-results` command above, replacing every example field. `--label` is an explicit self-declaration. `--input` may repeat and uses project-relative paths. The command string is recorded without execution. Imports preserve the original CSV bytes, assign `GROUP-001` IDs, and validate values against that snapshot during audit. The original external source can later change without changing saved history; optionally register a project-local source as an input to detect later changes.

Existing IDs/artifacts are refused. Validation happens before writes; interruption can still leave an orphan new file because this is not a multi-file transaction. The audit detects selected consistency errors, does not rerun your experiment, and cannot establish scientific validity or authenticity. Use new reports and versioned inputs for later runs.
