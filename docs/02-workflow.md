# 把论文写作拆成能检查的工作

## 1. 先写一个可以检验的问题

在 `project.json` 写清楚研究对象、输入、评价指标和范围。比如“课程 FAQ 中，加入标题的词法检索是否改善前 3 条结果的命中情况？”比“我要做一个很强的 Agent”更容易开始。

这个问题需要自己的数据、合适基线和未用于调参的评价集合。PaperTrail 的 demo 只是熟悉记录方式。

## 2. 先整理文献，再写论点

导入 CSL-JSON 或手工填写 `references.json`。每条记录至少有 `key`、`title`、`authors`、`year`、`url`；有 DOI 就记录 DOI。读过并核对来源后可补 `metadata_source`、`checked_at`。

在 `evidence.csv` 填：

| 字段 | 要填什么 |
|---|---|
| `claim_id` | 你自己给这张卡的标识，例如 C1 |
| `text` | 准备在论文中表达的一个具体论点 |
| `reference_key` | 支持这个论点的那篇文献的 key |
| `locator` | 读到的章节/页码/摘要定位 |
| `note` | 你自己的解释、条件和疑问 |
| `reviewed` | 读过对应原文并核对后填 yes，否则 no |

同一个论点需多篇来源时，本版本建立多个不同 ID 的证据卡。元数据匹配和原文支持是两回事，工具不能替你理解原文。

## 3. 实验先从基线开始

每次登记一条指标结果到 `experiments.csv`：实验 ID、方法、数据描述、样本数、指标、值、原始附件、SHA-256、数据性质和复现命令。`label=toy` 是教学数据；真实研究只能在确实使用真实研究数据时自报 `real`。

内置实验会自动填六条结果，同时记录输入数据和实现的 SHA-256、Python 版本及逐查询排名。查看 JSON 才能知道总分背后发生了什么。

自己的实验附件可以是 JSON、CSV 或文本。通用附件只校验文件指纹，本版本只有内置 `papertrail-retrieval-v1` schema 额外验证指标和输入数据。手工填真实实验表时，必须自己保证指标定义、计算、数据来源和切分正确。

修改输入数据会让旧实验的输入校验失败。要研究新数据，保存版本化文件并手工登记自己的实验，或在新项目目录复制/调整教学语料；不要用新的数据覆盖旧记录并继续引用旧分数。

## 4. 草稿使用显式引用和结果标记

```markdown
相关研究把检索与生成结合 [@lewis2020]。{{claim:C1}}
本次教学实验的 MRR 为 {{run:demo-overlap-mrr}}。
```

`check` 会连接引用键和标记；`report` 会在 `draft.md` 展开已登记结果和证据定位。未知标记会显示 MISSING 并返回退出码 2。
普通文字中任意数字和没有显式标记的论点不在自动核对范围内。不要把生成的 draft.md 当作已完成或可直接投稿的论文。

## 5. 使用 AI 辅助时提供已经核对的输入

[提示词](../prompts/README.md)帮助你读难段落、比较表述与证据、准备提纲、检查局限。把缺失的证据标为待补，把模型建议和原作者结论分开；论文中的事实最终由你回到来源确认。

## 6. 每次组会前导出一次新报告

```bash
python -m papertrail check my-research
python -m papertrail report my-research --out my-research/report-week1
```

先修复 errors，再解释 reminders。挑一张证据卡、一个结果、一个失败案例，写进[组会记录](../templates/advisor-update.md)。

若要 Word/LaTeX 格式化，在这一层结构整理后使用学校或期刊模板，或另外用 Pandoc 转换。当前版本没有投稿格式引擎。
