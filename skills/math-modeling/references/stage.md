# math-modeling 阶段指南

## 输入与范围
读取任务、原始附件、规则及用户已经作出的选择。完整任务启动G0—G9；局部任务仅执行相关阶段及必要依赖。优先修复阻断当前阶段的问题，保留可独立复用的产物。

## 实际入口
仓库使用 `python3 workflow/workflow.py new-run --slug <name>` 创建运行；已安装包从项目根目录使用 `.math-modeling/workflow/workflow.py`。用 `check --state <state>` 查看当前要求，`meta-prompt --state <state> --task <task>` 输出阶段任务。它们不自动调用模型。

G0—G5由相关技能完成真实分析、计算与验证。G3在建模时规划图片对象，G6再生成核验。G7用 `scripts/paper.py --project <run> init` 建立论文计划，逐项绑定已经验证的文件。新增G7验收必须登记实际 `authoring_plan`，文件名为paper-plan.json。

## 路线决策
比较简单基线和有区分意义的候选。交代参数来源、可行性、复杂度、解释能力、验证手段与失败回退。没有必要不增加模型层。用户已经授权选择时自行作出有依据的决定，不反复确认常规步骤。

## 交接
每轮记录实际输入、产物、运行命令、验证及未完成事项。上游变更先invalidate，再重新登记。G7/G8对论文实时校验，不凭旧报告放行。将预期输出、失败原因和下一条可执行命令写入交接。
