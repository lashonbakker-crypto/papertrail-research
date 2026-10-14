"""Produce a self-contained HTML report and a Markdown handoff."""

import html
import math
import re
from pathlib import Path
from urllib.parse import urlsplit

from .storage import ProjectError, json_text, write_new


def escape(value):
    return html.escape(str(value), quote=True)


def safe_link(url, label):
    if not isinstance(url, str):
        return escape(label)
    try:
        parsed = urlsplit(url)
    except ValueError:
        return escape(label)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        return escape(label)
    return f'<a href="{escape(url)}" rel="noreferrer">{escape(label)}</a>'


def _table(headers, rows):
    head = "".join(f"<th>{escape(title)}</th>" for title in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def render_html(result):
    counts = result["counts"]
    errors, warnings = result["errors"], result["warnings"]
    status = "需要修正" if errors else "结构检查通过"
    cards = "".join(f'<div class="stat"><span>{escape(name)}</span><strong>{counts.get(key, 0)}</strong></div>' for name, key in (("文献", "references"), ("已引用", "citations"), ("证据卡", "claims"), ("结果记录", "runs")))
    issues = "".join(f'<div class="issue {level}"><b>{escape(item["code"])}</b><span>{escape(item["message"])}</span><code>{escape(item["location"])}</code></div>' for level, items in (("error", errors), ("warning", warnings)) for item in items)
    if not issues:
        issues = "<p>没有发现结构问题。仍请人工核对文献原文、实验设计和论证。</p>"
    refs = _table(("引用键", "文献", "来源核对记录"), [(f'<code>{escape(r.get("key", ""))}</code>', safe_link(r.get("url", ""), r.get("title", "")), escape(r.get("metadata_source", "未记录"))) for r in result["references"]])
    evidence = _table(("论点", "自己的表述", "证据定位", "人工阅读"), [(escape(r["claim_id"]), escape(r["text"]), f'{escape(r["reference_key"])} · {escape(r["locator"])}', "已登记复核" if r["reviewed"] == "yes" else "待阅读") for r in result["evidence"]])
    runs = _table(("结果 ID", "方法 / 指标", "数值", "样本数", "数据性质"), [(f'<code>{escape(r["run_id"])}</code>', f'{escape(r["method"])} / {escape(r["metric"])}', escape(r["value"]), escape(r["n"]), "教学数据" if r["label"] == "toy" else "自报真实数据") for r in result["runs"]])
    charts = []
    for row in result["runs"]:
        if row["metric"] not in ("MRR", "Recall@1", "Recall@3"):
            continue
        try:
            value = float(row["value"])
        except ValueError:
            continue
        if not math.isfinite(value) or not 0 <= value <= 1:
            continue
        width = f"{value * 100:.3f}%"
        charts.append(f'<div class="chart-row"><div><b>{escape(row["method"])} · {escape(row["metric"])}</b><span>{value:.4f} / 1.0000</span></div><div class="track"><div class="bar" style="width:{width}"></div></div><small>{escape(row["run_id"])} · n={escape(row["n"])} · {escape(row["label"])}</small></div>')
    chart = "".join(charts) or "<p>尚无可展示的 MRR / Recall 结果。</p>"
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{escape(result["title"])} · PaperTrail</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f5f8;color:#15233a;font-family:system-ui,-apple-system,"Microsoft YaHei",sans-serif;line-height:1.65}}main{{max-width:1140px;margin:auto;padding:36px 24px 70px}}header{{background:#102239;border-radius:26px;padding:38px;color:#f4f8ff;position:relative;overflow:hidden}}.brand{{letter-spacing:3px;font-size:12px;font-weight:700;color:#80dec2}}h1{{font-size:clamp(25px,4vw,38px);line-height:1.3;margin:16px 0}}header p{{max-width:730px;color:#c0cce0;margin:0}}.status{{display:inline-block;background:#d6f5e8;color:#135d43;padding:5px 14px;border-radius:20px;font-weight:700;margin-top:24px}}.status.fail{{background:#ffdbd7;color:#84291e}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:24px 0}}.stat{{background:white;border:1px solid #e2e7ef;padding:20px;border-radius:16px}}.stat span{{display:block;font-size:13px;color:#617086}}.stat strong{{font-size:32px}}section{{background:white;border:1px solid #e2e7ef;padding:26px;border-radius:18px;margin:20px 0}}h2{{font-size:21px;margin:0 0 16px}}.section-note{{color:#647187;font-size:14px}}.issue{{display:grid;grid-template-columns:190px 1fr;gap:8px;border-left:4px solid #dda33e;background:#fff9eb;padding:12px 16px;margin:9px 0;font-size:13px}}.issue.error{{border-color:#cf5544;background:#fff0ee}}.issue code{{grid-column:2;color:#69758a}}.issue b{{font-family:ui-monospace,monospace;font-size:12px;overflow-wrap:anywhere}}table{{border-collapse:collapse;width:100%;font-size:13px}}th{{text-align:left;background:#f1f5fa;color:#66758b;font-weight:600}}th,td{{padding:12px;vertical-align:top;border-bottom:1px solid #e8edf4;overflow-wrap:anywhere}}.scroll{{overflow:auto}}a{{color:#176f8c;text-decoration:none}}code{{font-family:ui-monospace,monospace;font-size:12px}}.chart-row{{margin:19px 0}}.chart-row>div:first-child{{display:flex;justify-content:space-between;gap:15px;font-size:14px}}.chart-row span{{font-variant-numeric:tabular-nums;color:#69768b}}.track{{background:#eaf0f6;height:14px;border-radius:20px;margin:7px 0;overflow:hidden}}.bar{{height:100%;background:linear-gradient(90deg,#15977d,#64c7ac);border-radius:20px}}small{{color:#6c7a90}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}footer{{color:#647187;font-size:12px;text-align:center;margin-top:25px}}@media(max-width:700px){{main{{padding:18px 14px 40px}}header{{padding:26px}}.stats{{grid-template-columns:repeat(2,1fr)}}section{{padding:18px}}.issue{{grid-template-columns:1fr}}.issue code{{grid-column:1}}.two{{grid-template-columns:1fr}}}}
</style></head><body><main><header><div class="brand">PAPERTRAIL / RESEARCH WITH A RECORD</div><h1>{escape(result["title"])}</h1><p>{escape(result.get("question", "文献 → 证据 → 实验 → 草稿"))}</p><span class="status {"fail" if errors else ""}">{status} · {len(errors)} 个错误 / {len(warnings)} 项提醒</span></header>
<div class="stats">{cards}</div><section><h2>01 / 提交给导师前，先看这里</h2><p class="section-note">结构检查记录引用和附件是否对得上。元数据核对、人工阅读登记、研究有效性是不同的事情。</p>{issues}</section>
<section><h2>02 / 结果可追溯</h2><p class="section-note">MRR 与 Recall 坐标固定为 0–1；教学数据与真实研究必须区分。图表只展示登记值，不能证明方法优越性。</p>{chart}{runs}</section>
<section><h2>03 / 论点背后的证据</h2>{evidence}</section><section><h2>04 / 文献来源</h2>{refs}</section>
<footer>PaperTrail 0.1.0 · 本地生成，零外部资源 · SHA-256 检查内容一致性，不能证明数据真实性或发布者身份</footer></main></body></html>'''


def render_markdown(result):
    lines = [f"# {result['title']} — 科研交接记录", "", f"问题：{result.get('question', '')}", "", f"结构检查：{len(result['errors'])} 个错误，{len(result['warnings'])} 项提醒。", "", "## 需要处理", ""]
    for item in result["errors"] + result["warnings"]:
        lines.append(f"- `{item['code']}` · {item['location']} · {item['message']}")
    lines += ["", "## 文献与证据", ""]
    for row in result["evidence"]:
        lines.append(f"- {row['claim_id']}：{row['text']}；来源 {row['reference_key']}，定位 {row['locator']}。人工阅读登记：{row['reviewed']}。")
    lines += ["", "## 已登记实验", ""]
    for row in result["runs"]:
        lines += [f"- {row['run_id']}：{row['method']} / {row['metric']}={row['value']}，n={row['n']}，label={row['label']}。", f"  - 附件 `{row['artifact']}`；SHA-256 `{row['sha256']}`。", f"  - 复现命令（将 PROJECT 替换为项目目录）：`{row['command']}`。"]
    lines += ["", "## 下一次组会", "", "1. 展示自己读懂的一张证据卡。", "2. 在新目录重跑实验，核对逐条结果。", "3. 解释一个失败案例和当前结论的范围。", "", "本记录帮助整理过程。科研贡献和申请材料只写自己实际完成、能解释并可复核的工作。", ""]
    return "\n".join(lines)


def export_report(result, destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ProjectError("Report destination already exists; use a new --out folder")
    destination.mkdir(parents=True, exist_ok=False)
    write_new(destination / "index.html", render_html(result))
    write_new(destination / "audit.json", json_text(result))
    write_new(destination / "handoff.md", render_markdown(result))
    run_map = {row["run_id"]: row for row in result["runs"]}
    claim_map = {row["claim_id"]: row for row in result["evidence"]}

    def expand(match):
        kind, key = match.groups()
        if kind == "run" and key in run_map:
            row = run_map[key]
            return f"{row['value']}（n={row['n']}，{row['label']}；结果 ID：{key}）"
        if kind == "claim" and key in claim_map:
            row = claim_map[key]
            return f"（证据卡 {key}：{row['reference_key']}，{row['locator']}）"
        return f"[MISSING {kind}:{key}]"

    draft = re.sub(r"\{\{(run|claim):([A-Za-z][A-Za-z0-9_.:-]*)\}\}", expand, result.get("manuscript", ""))
    write_new(destination / "draft.md", draft)
    return destination
