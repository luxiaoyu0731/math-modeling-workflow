# 理解图链蓝图模板

> G3 完成设计，G6 生成正式图。每类图若不适用，写 `not_applicable + 原因`；不能等到有结果时才补画理解图。

| visual_id | 图类型 | 读者要回答的问题 | 对应 requirement_id / formula_id | 数据或模型对象源 | 生成方式 | 支持结论 | 不支持结论 | 正文位置 | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| V-01 | 问题结构图 | 对象、信息、决策、约束和子问题如何耦合？ | | `problem_analysis_contract.md` | ImageGen / 精确数据层 | | | 问题分析 | template |
| V-02 | 模型对象/场景图 | 模型的边界、坐标、状态或集合关系是什么？ | | `model_object_figure_specs.md` / model card | ImageGen / 精确数据层 | | | 模型建立 | template |
| V-03 | 公式解释对象图 | 公式中的变量、区域、连接、时间窗或变换分别对应什么数学对象？ | | `model_object_figure_specs.md` / `formula_derivation_ledger.csv` | ImageGen / 精确数据层 | 解释模型设定 | 不证明数值、因果或最优性 | 模型建立 | template |
| V-04 | 结果证据图 | 哪个比较、敏感性或机制直接支持结果？ | | final evaluator/results | ImageGen / 精确数据层 | | | 结果与验证 | template |

## 视觉语法

- 变量名、单位、颜色、线型、箭头、图例、语言、中英规则和有效数字：
- 色盲友好方案与灰度可读性：
- 版面约束：正式纸面字体不小于 8pt；无原始浮点刻度、乱码、遮挡、重叠和无信息留白：
- ImageGen：按调用合同记录生成与核验；数值层独立保持数据真实性。
