# 🐦 数学建模工作流

[English](README.en.md)

给使用 AI 辅助建模与写作的参赛者：组织推导、计算和论文证据，生成 Word / LaTeX，并检查结论与成品是否一致。

![数学建模工作台概念插画](docs/assets/readme-hero.png)

Python 3.10+ · 9 个 skills · Word / LaTeX · MIT

[直接查看生成的示例 PDF](docs/assets/sample-paper.pdf)

<img src="docs/assets/sample-paper.png" alt="Synthetic sample PDF; arithmetic fixture only" width="500" />

![Recorded walkthrough](docs/assets/walkthrough.gif)

演示说明：真实合成示例创建、audit 和 LaTeX 构建命令输出；不使用真实比赛数据或论文。

## 从这里开始

| 当前任务 | 入口 |
|---|---|
| 开始一个新题目 | [启动提示词](prompts/start.md) |
| 继续上次任务 | [续接提示词](prompts/continue.md) |
| 审阅已有论文 | [审阅提示词](prompts/review.md) · [已有工程接入](docs/existing-project.md) |
| 安装 skills | [安装说明](docs/install.md) |

只阅读文档、使用提示词不需要安装依赖。题目、数据和私人论文留在仓库外的独立目录。

## 工作流

问题分析 → 数据证据 → 模型推导 → 实际求解 → 验证 → 制图 → 写作 → 成品检查

- 用阶段合同组织任务，保存需求、符号、推导与执行证据。
- 将章节、公式、图表绑定到结果文件；上游变化后重新核验相关结论。
- 支持 Word 原生公式、生成 LaTeX，以及接入已有 TeX 工程。
- 区分数学验证、文件检查与逐页视觉审阅，不把软件通过当作结论正确。

[工作流全貌](docs/workflow.md) · [ImageGen 制图](docs/imagegen.md)

## 跑一个合成示例

```sh
python3 examples/create_showcase.py --destination ../mm-demo
python3 scripts/paper.py --project ../mm-demo audit
python3 scripts/paper.py --project ../mm-demo build --formats latex
```

目标目录必须是新目录。示例只有合成算术数据，不包含真实比赛论文。

生成 PDF、Word 和填写视觉审核记录见 [快速开始](docs/quickstart.md)。首次 `verify` 缺少视觉审核而失败是预期行为；模型与文献真实性仍需人工核验。

<details>
<summary>开发、测试与许可</summary>

`prompts/` 提示词 · `skills/` 阶段技能 · `workflow/` 内核与模板 · `scripts/` 构建与检查。

```sh
python3 -B -m unittest discover -s workflow/tests -v
python3 -B -m unittest discover -s tests -v
```

[排障](docs/troubleshooting.md) · [审核合同](docs/review-contracts.md) · [代码审查](docs/code-review.md)

公式转换模块来自 MathModel-Skill，许可及固定版本见 [第三方声明](THIRD_PARTY_NOTICES.md)。ImageGen 由助手所在环境提供，本仓库不购买调用；首页插画仅作展示，来源见 [素材说明](docs/assets/README.md)。

</details>

[MIT License](LICENSE)

[遇到问题](https://github.com/luxiaoyu0731/math-modeling-workflow/issues/new?template=bug_report.yml) · [告诉我们哪一步不清楚](https://github.com/luxiaoyu0731/math-modeling-workflow/issues/new?template=first_use.yml) · [从小任务参与](.github/CONTRIBUTING.md)

[Versioned releases and artifact verification](docs/releasing.md)
