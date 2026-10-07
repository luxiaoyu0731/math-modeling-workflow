# 论文计划与实际交付

运行内核和内容审计仅依赖Python标准库。Word/PDF适配器使用已同意的可选依赖，用户按需安装：

```sh
python3 -m pip install -r docs/requirements.txt
python3 scripts/paper.py doctor
```

文字核验优先使用pypdfium2以兼容部分中文PDF编码。还需实际可用的LibreOffice（Word转PDF）或XeLaTeX（TeX转PDF）。工具检查不会安装任何软件。ImageGen由助手所在环境提供，本仓库不内置服务或密钥。

## 创建计划

```sh
python3 scripts/paper.py --project <run-directory> init
```

填写生成的paper-plan.json。所有文件路径相对于该运行目录，不能逃逸到外部目录。

| 字段 | 内容 |
|---|---|
| title / language | 实际标题及zh或en |
| profile | 字体、字号、行距倍率、页边距、可选正文字符数及整份PDF页数约束 |
| questions | 本次需回答的问题ID |
| sections | 有序章节：id、path、questions、evidence、role |
| evidence | 证据ID到path、sha256、source |
| claims | 数值ID到evidence、pointer、value、format与可选unit |
| figures | 图ID到文件、哈希、来源、图注、生成及审核记录 |
| references | 引用ID到实际核验过的text和source |

claims的pointer使用JSON pointer，例如 `/summary/metric`。数值来源目前仅支持有限的JSON数值，CSV或工作簿需要先保存实际计算的JSON结果；格式化后再显示。

## 写作与构建

章节支持标题、段落、简单加粗、代码块、Markdown表格、单独成行的图引用、`$...$`行内公式与`$$...$$`块公式。

- `[[value:ID]]`：从绑定结果格式化数值。
- `[[figure:ID]]`：插入已核验图片及图注；需独占一行。
- `[[cite:ID]]`：生成参考文献编号。

每个section的role默认为body；abstract、references、appendix不计入可选正文字符数。页数检查是整份PDF口径，不等于特定比赛的正文页数。零上下限表示不设统一配额。

```sh
python3 scripts/paper.py --project <run-directory> audit
python3 scripts/paper.py --project <run-directory> build --formats docx latex
python3 scripts/paper.py --project <run-directory> render --format docx
python3 scripts/paper.py --project <run-directory> render --format latex
```

成品写入运行目录delivery/，并保存输入、输出和构建代码哈希。装配稿由章节确定性生成；全文修订回写章节，再重建。Word使用原生OMML公式；转换不支持的公式会失败，不默默改成图片。LaTeX默认中文ctexart或英文article，不声称其行距倍率和Word具有相同物理行高。

## 视觉验收

渲染成功后仍是REVIEW_REQUIRED。查看所有页面，实际填写delivery/visual-review.json，其字段为status=PASS、reviewer（角色）、notes、pdfs（相对路径到哈希）和pages（docx/latex到页数）。不提供自动填写PASS的命令。

```sh
python3 scripts/paper.py --project <run-directory> verify
```

verify重读数据、计划、章节、代码、输出及PDF，检查视觉记录是否匹配最新文件。G7登记authoring_plan后执行内容检查，G8/G9执行完整交付检查。旧v7运行不自动迁移；新建v8运行默认启用。

## 能力边界

这是一套明确支持子集的文档适配器，不是完整Markdown或LaTeX编译前端。未通过引用标记写出的普通数字仍需人工追踪；reference.source不是文献真实性证明；图形审核记录不能证明ImageGen真的调用过，需保留实际工具证据。输出不能替代数学审阅。

无界面LibreOffice可能看不到桌面字体。指定实际可用的中文字体并检查渲染页面；若本机依赖Fontconfig，按环境配置FONTCONFIG_FILE，而不是只改字号或忽略缺字。标题文本核对失败时不会通过最终验收。

已有 TeX 工程使用 [existing_tex](existing-project.md)；分层证据、分区页数及逐页验收见 [审核合同](review-contracts.md)。原 v1 接口兼容，新示例默认开启逐页审核。
