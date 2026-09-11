# 数学建模工作流与 Meta-Prompt

一套可阅读、可复用的数学建模到论文交付流程：问题分析 → 数据证据 → 模型推导 → 实际求解 → 验证 → ImageGen 制图 → 写作 → 成品检查。

这里分享通用方法、提示词、skill 和轻量运行内核，不包含任何具体题目、真实数据、论文、计算结果或私人技能库快照。软件测试只使用明确标记的合成材料。

当前版本：**0.2.0**。已补充项目安装器、章节证据检查、Word原生公式、LaTeX构建及PDF验收。

## 从这里开始

1. 阅读 [工作流说明](docs/workflow.md)，理解各阶段如何交接。
2. 把 [启动提示词](prompts/start.md) 发给你使用的助手，并提供自己的材料。
3. 持续推进时使用 [续接提示词](prompts/continue.md)；只需修订时用 [审阅提示词](prompts/review.md)。
4. 需要客户端自动发现技能时，按 [安装说明](docs/install.md) 安装完整包。
5. 需要完整论文生成与核验时，按 [论文交付说明](docs/authoring.md) 执行。
6. 需要文件证据和阶段记录时，按 [内核用法](workflow/README.md) 创建独立运行。

## 内容导航

| 内容 | 用途 |
|---|---|
| [Meta-Prompt](workflow/META_PROMPT_INTEGRATION.md) | 把目标、上下文、执行和验收组织成明确任务 |
| [9个建模 skill](skills/README.md) | 总控及读题、证据、求解、验证、制图、论文、终审、复盘 |
| [ImageGen 工作流](docs/imagegen.md) | 图卡、实际生成、精确标注、语义与版面核验 |
| [模板](workflow/templates/) | 需求、公式、证据、图形、主张和交付记录 |
| [运行内核](workflow/workflow.py) | 阶段状态、哈希检查、依赖失效和任务提示 |
| [发布范围](docs/publication.md) | 文件来源、公开边界和检查方法 |

## 使用环境

纯阅读与复制提示词不需要安装依赖。运行内核需要 Python 3.10+；执行建模还需按具体任务准备计算、文档渲染和 ImageGen 工具。此仓库不内置模型API，不含密钥，不会自动调用或购买图像服务。

Skill 可以作为普通 Markdown 读取；若助手支持技能目录，可把 `skills/` 中所需目录放入其约定位置。不同客户端安装约定不同，以客户端文档为准。不需要复制作者的个人配置。

## 基本约定

- 先分析和实际计算，再写有证据支持的结论。
- 图与推导相互解释，图像美观不能代替数学证明或真实数据。
- 论文格式、篇幅和视觉风格来自当前任务，不继承任何旧论文设置。
- 保存失败、近似与限制，不伪造人工检查。
- 新运行内容默认由 `.gitignore` 排除；分享前仍需检查实际提交文件。

验证内核：

```sh
python3 -B -m unittest discover -s workflow/tests -v
python3 -B -m unittest discover -s tests -v
```

测试通过仅表示所覆盖的工作流行为通过检查，不保证任一论文正确或取得竞赛成绩。

公式转换复用自 MathModel-Skill 的 MIT 模块，详见 [来源与许可](THIRD_PARTY_NOTICES.md)。实际验收记录见 [验证说明](docs/validation.md)。
