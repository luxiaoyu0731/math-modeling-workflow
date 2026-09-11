# 公式推导依赖图模板

> 这是推导链，不是装饰性“建模流程图”。每个节点须填 `requirement_id`、`formula_id`、代码函数或输出字段；正式版本按 ImageGen 调用合同生成并核验。

```mermaid
flowchart LR
  R["题意/数据\nrequirement_id"] --> D["定义与符号\nformula_id"]
  D --> L["引理、守恒或变换\nderivation_id"]
  L --> P["事件谓词\nformula_id + code"]
  P --> M["指标与聚合\nformula_id + code"]
  M --> C["目标与约束\nformula_id + code"]
  C --> A["算法输入\nmodule:function"]
  A --> O["结果字段\nresult selector"]
  O --> K["可主张结论\nclaim_id"]
```

每条边在 `formula_derivation_ledger.csv` 中具有相应的推导步骤、前提和测试映射。若某节点只是在近似、代理或条件模型中成立，节点和边必须显示其边界。
