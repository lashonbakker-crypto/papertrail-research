# Contributing

先跑 demo 和行为测试，再选择一个你确实能复现的问题。

```bash
python -m unittest discover -s tests -v
python -m papertrail demo my-first-study
```

欢迎：修复真实检查漏洞、改进不清楚的中文步骤、提供有许可的公开实验示例、提升跨平台初次运行体验。

PR 请写问题触发条件、修改后的行为、实际验证、剩余限制。行为改变添加能复现旧问题的回归测试，不为测试数量拆分同义测试。

报告中引用外部材料要保留来源；原创数据说明创建方式与许可。不要提交全文版权受限论文、个人成绩、申请文件、凭据、私有数据或模型生成的假结果。

一个适合新贡献者的任务：给自己的课程小实验写一份去标识化的结果登记案例，并说明数据来源、指标准则、复现命令和局限。在开 Issue 时先讨论范围。

README 图像由真实 demo 输出构建。若修改示例，再运行 `python scripts/build_visuals.py` 更新图像；这个开发步骤需要 Pillow 和 DejaVu 字体，不属于运行时依赖。可通过 `PAPERTRAIL_VISUAL_FONT` 指定字体文件。报告数据概览不冒充浏览器截图，CLI 动图只缩短路径、摘取输出。
