# 🐦 数学建模工作流 × Meta-Prompt

**把一个问题，认真走成一篇论文。**

![戴眼镜的小鸟在研究工作台旁，沿着数据、模型与图像走向完成的报告](docs/assets/readme-hero.png)

**v0.3.0 · Python 3.10+ · 9 个 skills · Word / LaTeX · MIT**

[🚀 快速开始](docs/quickstart.md) · [📄 接手已有论文](docs/existing-project.md) · [🧭 工作流全貌](docs/workflow.md) · [🎨 ImageGen 制图](docs/imagegen.md)

欢迎来到这个小小的建模工作台。这里把读题、推导、计算、制图、写作和终审串起来，让助手知道下一步该做什么，也让你看得清每个结论从哪里来。

带上自己的材料就能开始；中途换个对话，或者已经有了论文初稿，也有对应入口。仓库只分享通用方法和合成示例，保留你对题目、篇幅和风格的选择。

## 先选一个入口

| 你现在想做什么？ | 从这里出发 |
|---|---|
| 🌱 还没开始，想让助手带着推进 | 复制 [启动 prompt](prompts/start.md)，附上你的材料 |
| 🧵 上个对话没做完，想接着来 | 使用 [续接 prompt](prompts/continue.md)，保留已有证据 |
| 🔎 已有初稿，想认真过一遍 | 使用 [审阅 prompt](prompts/review.md)；TeX 工程看 [接入指南](docs/existing-project.md) |
| 🧪 想先看看工具能不能跑通 | 运行 [纯合成示例](docs/quickstart.md) |
| 🧰 想让客户端自动发现 skills | 阅读 [安装说明](docs/install.md) |

**只读文档、复制 prompt，不需要安装任何依赖。**

## 一路上，我们做些什么？

![同一只小鸟依次观察笔记、开展实验、检查完成的报告；三联装饰插画](docs/assets/readme-journey.png)

| ① 想清楚 | ② 算明白 | ③ 交得稳 |
|---|---|---|
| 拆问题，理条件，辨认假设 | 建模型，做计算，用对照检验 | 画图，写作，查看实际成品 |
| 留下需求、符号和推导关系 | 留下数据、代码、误差和限制 | 留下图源、引用和逐页检查 |

展开以后，是这条可以回退、也可以续接的路线：

**问题分析 → 数据证据 → 模型推导 → 实际求解 → 验证 → ImageGen 制图 → 写作 → 成品检查**

发现问题就回到对应步骤修正。上游数据或代码变化，下游图表和结论也要重新核对。

> 插画让这份介绍轻松一点；论文里的定量图仍然来自真实计算。上面两张图由 ImageGen 生成，仅作项目介绍。

## 这套工具会帮你记住什么？

### 🧭 每一步为什么要做

[Meta-Prompt](workflow/META_PROMPT_INTEGRATION.md) 把目标、上下文、执行与验收组织起来。[9 个 skills](skills/README.md) 分担读题、证据、求解、验证、制图、论文、终审与复盘。

### 🔗 每个结论从哪里来

将数值绑定到结果文件，让章节、公式、图片与证据相互对应。文件变化时，旧的通过记录会失效；“看起来没变”需要比较来支持。

### 🎨 图在解释什么

先写图卡，再实际调用 ImageGen，检查对象、方向、符号和标注。定量曲线、坐标与误差范围保留可复算的数据层。详见 [图形工作流](docs/imagegen.md)。

### 📄 最后交出去的是什么

支持生成 Word 原生公式、构建 LaTeX 并渲染 PDF；已有 TeX 工程可在独立目录重建，保留原稿。摘要、正文和附录可分别计页，实际页面逐页检查。

### 🔍 到底验证到了哪一步

把“历史哈希吻合”“本次重算”“独立解包重建”“完整冷启动”“异机验证”分别记录。数学合理性与文件完整性也分别看，限制不会被一个 PASS 藏起来。

## 动手跑一个小例子

下载或克隆仓库后，在仓库根目录运行。示例只包含简单算术，目标目录必须是新目录：

```sh
# 生成合成材料，不覆盖已有项目
python3 examples/create_demo.py --destination ../mm-demo

# 检查章节、结果和证据
python3 scripts/paper.py --project ../mm-demo audit

# 生成 LaTeX 源文件
python3 scripts/paper.py --project ../mm-demo build --formats latex
```

想看到 PDF？先检查环境：

```sh
python3 scripts/paper.py doctor
```

按 [交付说明](docs/authoring.md) 准备可选文档依赖和 XeLaTeX，然后：

```sh
python3 scripts/paper.py --project ../mm-demo render --format latex
python3 scripts/paper.py --project ../mm-demo verify
```

**首次 `verify` 因缺少视觉审核而失败，是预期行为。** 打开真正生成的 PDF，查看每一页，再按 [审核合同](docs/review-contracts.md) 填写记录。

Word 使用 `docx` 格式与 LibreOffice；完整命令见 [快速开始](docs/quickstart.md)。ImageGen 由助手所在环境提供，本仓库不会替你登录图像服务或自动购买调用。

## 桌面上的工具，放在哪里？

| 目录 / 文件 | 装着什么 |
|---|---|
| [prompts/](prompts/) | 启动、续接和审阅提示词 |
| [skills/](skills/) | 总控与分阶段技能 |
| [workflow/](workflow/) | Meta-Prompt、阶段内核和空模板 |
| [scripts/](scripts/) | 安装、论文构建、验收及发布检查 |
| [examples/](examples/) | 不含真实题目的合成示例生成器 |
| [docs/](docs/) | 使用说明、审核合同、排障与发布准备 |
| [tests/](tests/) | 交付和发布回归测试 |

[2026-10-06 代码复核](docs/code-review.md)

## 我们已经检查了什么？

当前核心、交付与发布测试共 **58 项，本地全部通过**；Word、生成式 LaTeX 与既有 TeX 的合成样张均实际构建并查看。README 插画与发布扫描的后续验证见 [验证记录](docs/validation.md)。

```sh
python3 -B -m unittest discover -s workflow/tests -v
python3 -B -m unittest discover -s tests -v
```

CI 配置覆盖 Windows / Linux、Python 3.10–3.12，以及 Word、LaTeX 和发布检查。远端运行状态以 GitHub Actions 的实际结果为准。

<details>
<summary><strong>展开：使用前值得知道的边界</strong></summary>

- 软件检查不证明模型正确、文献真实或竞赛成绩；关键结论仍需审阅。
- 文档适配器支持明确的 Markdown/公式子集；复杂 TeX 可走已有工程模式。
- Word 与 TeX 的相同行距倍率，不保证相同物理行高。
- ImageGen 不可用时，保存图卡和待办，不假称图片已经生成。
- 新任务的输入、输出和私人记录应留在独立运行目录；分享前检查实际 ZIP 与 Git 索引。

遇到问题先看 [排障与已知限制](docs/troubleshooting.md)。

</details>

## 分享、修改与致谢

原创代码与文档采用 [MIT License](LICENSE)，欢迎按许可使用、修改和分享。

公式转换模块复用自 [MathModel-Skill](https://github.com/yushui2022/MathModel-Skill)，已保留固定提交、原始许可与来源说明，详见 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)。README 插画由 ImageGen 生成，素材说明见 [图片记录](docs/assets/README.md)。

[版本变化](CHANGELOG.md) · [发布前检查](docs/release-readiness.md) · [公开范围](docs/publication.md)

**准备好了，就从你的第一个问题开始。** 🐦
