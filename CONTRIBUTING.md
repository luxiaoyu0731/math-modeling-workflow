# Contributing

## 从一个小任务开始 / Starter tasks

先在 Issue 中说明选择的任务和复现方法，再提交最小修改。测试只使用合成资料；不把外部模型收费作为贡献前提。

- **合成示例覆盖带空格的目标路径** — `tests/test_release_review.py`。验收：创建、audit 与 build 在含空格目录工作；重跑不覆盖已有目录。
- **改善缺少 LaTeX 引擎时的提示** — `scripts/paper.py`。验收：输出可执行排障建议；失败时不能复用旧 PDF；补失败反例测试。

[报告问题 / Report a bug](https://github.com/luxiaoyu0731/math-modeling-workflow/issues/new?template=bug_report.yml) · [首次使用反馈 / First-use feedback](https://github.com/luxiaoyu0731/math-modeling-workflow/issues/new?template=first_use.yml)
