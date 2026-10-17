# 命令、文件格式和下载校验

## 命令表

| 命令 | 实际作用 | 是否联网/写入 |
|---|---|---|
| `init PROJECT` | 创建空白工作目录 | 本地写新目录；目录已存在就拒绝 |
| `demo PROJECT` | 创建教学输入，运行实验，生成报告 | 本地写新目录 |
| `check PROJECT [--json]` | 校验选定结构和文件一致性 | 本地只读 |
| `coverage PROJECT [--json]` | 只读统计文献引用、证据卡人工核对及草稿连接情况，列出下一步提醒；[详细说明](07-coverage.md) | 本地只读 |
| `report PROJECT [--out NEW_DIR]` | 先检查，再导出 HTML/JSON/两份 Markdown | 本地只读输入、写新报告目录 |
| `experiment PROJECT [--run-id NEW_ID]` | 运行自编英文语料的两种词法检索 | 本地写新附件并更新 experiments.csv |
| `import-csl PROJECT EXPORT.json` | 导入 CSL-JSON 文献 | 本地读取导出，原子替换 references.json；碰撞不保存 |
| `import-results PROJECT RESULTS.csv --run-id ID --dataset TEXT --command TEXT --label toy/real [--input PATH ...]` | 保存自算指标 CSV 原始快照、映射和可选输入指纹，不执行命令 | 本地写新附件、原子替换 experiments.csv；[完整教程](05-own-experiments.md) |
| `add-doi PROJECT DOI --key KEY` | 从 Crossref 查询并加入单条元数据 | 显式 HTTPS 网络请求；成功才更新文献表 |

退出码 `0` 表示本命令的结构检查或操作完成；存在提醒仍可为 `0`。退出码 `2` 表示输入错误、发现结构问题、网络失败或拒绝覆盖。`report` 即使检查有错也会导出问题报告，再返回 `2`。

包方式也可 `python -m pip install .` 后直接运行 `papertrail`。运行时无需第三方包，安装构建需要 setuptools；无法联网安装时优先源码或 pyz 方式。

## 文件约定

UTF-8 JSON、CSV、Markdown；读取可接受一个 UTF-8 BOM。JSON 拒绝重复键和非有限数；CSV 列名和顺序必须与模板一致，行列数不对会报错。
CSV 畸形引号、字段超出解析器限制或列数错误会返回受控错误。
引用键/claim ID/run ID：ASCII 字母开头，后续允许字母、数字、`_ . : -`。

新的 import-results 分组 ID 为跨平台文件名：ASCII 字母开头，后续只允许字母、数字、`_ -`，最多 64 字符，拒绝设备名；生成的结果 ID 为 GROUP-001 等。自带 CSL 练习见[Zotero 导入](06-zotero-import.md)。

正文引用支持方括号中的 `[@key]` 和 `[@one; @two]`；不完整模拟全部 Pandoc Markdown 语法。跳过代码围栏、行内代码和 HTML 注释。单条实验记录对应一个指标。

## 保留旧结果

现有项目、报告目录、实验附件和 ID 不覆盖。重新导出用 `--out report-v2`，重跑同一份教学数据用 `--run-id replication`。
命令不会执行 experiments.csv 的 command 字段。SHA-256 只是对内容的一致性检查，不保证真实性。

拒绝项目内部符号链接和 `../` /绝对附件路径。单个输入文件限制 8 MiB。该保护不是针对恶意并发替换路径的完整隔离沙箱，也不提供多文件事务或快照。操作时不要同时编辑输入。

## Crossref 的边界

只有 `add-doi` 联网，向 `api.crossref.org` 发送你选择的 DOI 和工具标识 User-Agent，不发送草稿、证据卡或账户凭据。默认 15 秒超时，不自动批量抓取或后台重试。
Crossref 元数据可能缺字段或有录入错误，需人工对照出版页面。404 也可能表示 DOI 归其他注册机构。演示 arXiv DOI 归 DataCite，因此不调用 Crossref 检验这两篇。
本地测试使用成功、404、超时/断网和畸形响应夹具；CI 不依赖在线服务。当前运行环境未完成 CLI 的真实 Crossref 网络实测。

## 校验单文件下载

从 Release 下载 `papertrail.pyz` 与 `SHA256SUMS.txt`，放在同一文件夹。跨平台使用 Python 校验：

```bash
python -c "import hashlib; from pathlib import Path; entries=[line.split() for line in Path('SHA256SUMS.txt').read_text(encoding='utf-8').splitlines() if line.strip()]; matches=[digest for digest,name in entries if name=='papertrail.pyz']; ok=len(matches)==1 and hashlib.sha256(Path('papertrail.pyz').read_bytes()).hexdigest()==matches[0]; print('SHA-256 OK' if ok else 'SHA-256 MISMATCH'); raise SystemExit(0 if ok else 2)"
python papertrail.pyz --version
python papertrail.pyz demo my-first-study
```

应看到 `SHA-256 OK` 与 `papertrail 0.3.0`。校验文件同时列出单文件版和源码包，上述命令只核对 `papertrail.pyz`，不要求你下载源码包。校验失败时重新获取同一 Release 的两份附件，校验通过后再运行。它检查下载内容，不是作者身份签名。pyz 仍需要 Python 3.10+。

`v0.1.0` 的单文件入口曾忽略命令返回码，发现错误时仍可能返回 `0`。使用 `v0.1.1` 或以上：正常检查为 `0`，未知引用或不存在的项目应返回 `2`；终端输出和进程状态都要检查。
