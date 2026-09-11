# math-modeling-paper 阶段指南

## 写作计划
使用 `scripts/paper.py --project <run> init` 建立paper-plan.json。按实际题目配置title、language、profile、questions、sections、evidence、claims、figures和references。profile的篇幅限制默认为未指定；格式来自当前要求。

## 完整章节
每个section指定id、path、questions、evidence及role。每问形成问题—选择依据—假设推导—求解结果—验证—回答的链条。先主体后摘要，明确公式含义和图文关系；不要把计算日志填进正文。

数值用 `[[value:ID]]` 从结果JSON装配；图用 `[[figure:ID]]`；引用用 `[[cite:ID]]`。引用元数据仍需实际查证。只允许受支持的Markdown子集，复杂排版需显式扩展适配器，不静默丢失内容。

## 校验与装配
运行 `audit` 修复缺失输出、错误数值、无来源图片、占位符和重复段落。运行 `build --formats docx latex` 装配并输出构建快照。通读装配稿，若需要修改回到章节源文件修改再构建，避免直接改成品导致下次覆盖。

## 原生公式与限制
Word的行内和块公式转换为OMML，失败阻断；不退化成公式截图冒充可编辑公式。LaTeX使用数学源码。跨格式行距倍率不代表相同基线距离，最终视觉和正式规范须单独核对。
