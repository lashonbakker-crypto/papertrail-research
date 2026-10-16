# 从 Zotero 导入第一份文献表 / First CSL-JSON import

这是 [Issue #1](https://github.com/lashonbakker-crypto/papertrail-research/issues/1) 对应的可运行示例。仓库根目录中的 [examples/references.csl.json](../examples/references.csl.json) 只包含两篇公开论文的元数据，没有 PDF、私人条目或阅读完成声明。

在源码根目录依次运行，选一个尚不存在的项目目录：

```bash
python -m papertrail init zotero-study
python -m papertrail import-csl zotero-study examples/references.csl.json
python -m papertrail check zotero-study
```

应导入 2 条文献，key 分别为 `lewis2020`、`thakur2021`。`check` 无结构错误，但会提醒元数据未独立核对、正文未引用、尚无证据卡/实验以及草稿未完成。这些提醒是待做的工作，不需要为了消除提醒而虚填核对记录。

你可在自己的 `manuscript.md` 正文中写 `[@lewis2020]`，或并列写 `[@lewis2020; @thakur2021]`。阅读原文并确认与论点有关后，才填写 evidence.csv 的定位、笔记与 `reviewed=yes`。导入程序不会填写 `checked_at`，也不会把文献标成已经阅读。

## 换成你自己的 Zotero 条目

在 Zotero 中选中需要的条目，右键导出，选择 **CSL JSON** 格式。把导出文件路径换到上面的 `import-csl` 命令中。这一步只在本地读元数据，不连接 Zotero 账户，不上传文献，也不调用 DOI 查询。

| 选中的 CSL 字段 | PaperTrail 使用的 key |
|---|---|
| 有 `citation-key` | 优先使用其值 |
| 没有 `citation-key`，有合法 `id` | 使用 id，如示例中的 `lewis2020` |
| 选中的值不存在或不合法，如 Zotero 条目 URL | 生成 `refN`；N 为已有文献数加本次条目序号 |

key 须以 ASCII 字母开头，之后允许字母、数字、`_ . : -`。如果 `citation-key` 存在但不合法，会生成 refN，不再尝试 id；请查看实际导入的 `references.json`，不要凭导出工具界面猜 key。

重新运行同一个导入命令应退出 2，提示 key 冲突，原文件保持不变。即使用不同 key，同一 DOI 仍会拒绝；本次导入中后面的条目无效时，也不会只保存前半部分。遇到需要重新命名的条目，先在导出副本中修改 id/citation-key，或选择全新项目，不要删除旧文献来强行通过。

来源：[RAG arXiv 元数据](https://arxiv.org/abs/2005.11401)、[BEIR arXiv 元数据](https://arxiv.org/abs/2104.08663)。它们是内置检索练习的背景资料，示例未运行对应研究。arXiv DOI 由 DataCite 注册；不要用 Crossref 的 404 判断这些论文不存在。

## English

Run the three commands above from the repository root. The supplied CSL-JSON contains two public metadata records and imports keys `lewis2020` and `thakur2021`. The audit reports reminders for unchecked metadata, unused references, missing evidence/experiments and the unfinished draft. Importing does not establish that you read or verified either paper.

Export selected Zotero items as **CSL JSON**, then replace the source path. A present `citation-key` takes precedence; otherwise `id` is selected. An invalid selected value becomes `refN`, where N is the existing reference count plus the incoming item's one-based position. Inspect the saved keys. A repeated key or normalized DOI rejects the entire import and preserves the old table. Repeating the supplied import should therefore fail with exit code 2. This workflow is local and does not access a Zotero account or upload research.
