# 分层验证与审核合同

paper-plan.json 可引用 model_review、validation_ledger、change_impact 三个相对 JSON 路径。已有 TeX 模式必须提供前两个；原 v1 生成式项目保持兼容，新增项目建议全部按需使用。文件及其引用证据进入构建快照。

## 模型口径

model_review 文件包含 reviewer、notes、relations。每条关系记录 id、given（题给关系与位置）、interpretation、choice（as_given/additional/modified）、reason、status（accepted/conditional）。附加或改写关系必须提供 comparison（文件到哈希），或明确 limitation。未解决事项不能填写 accepted。采用 limitation 只表示公开限制，不表示完成物理验证。

## 验证强度

validation_ledger 的 checks 每项有 id、level、status、scope、limitations。level 彼此独立，不自动升级：

| level | 能证明的范围 |
|---|---|
| historical_hash | 当前产物与某次历史检查的对象相同 |
| recomputed | 本次执行指定范围计算或后处理 |
| isolated_rebuild | 在独立目录从材料重建指定成品 |
| cold_start | 从规定输入开始重新执行完整计算链 |
| cross_environment | 在不同环境重复指定流程 |

status 为 passed/failed/not_run。passed 必须有 artifacts（相对文件路径到 SHA-256）、scope 和 limitations；除 historical_hash 外，还需 command（实际命令）、environment（版本/工具说明）、log（包含在 artifacts 中的日志路径）。cross_environment 还需 source_environment。失败项阻止内容验收；not_run 不伪装为通过，是否属于提交前必需工作仍由任务要求决定。文件齐全不能证明命令真的执行，需保留实际工具输出并人工核对。

## 变更影响

change_impact 文件包含 changes 列表。每项包括 path、before_sha256、after_sha256、effect、affected_outputs、decision（rerun/compatible/pending）、evidence（对照日志或新结果到哈希）。前后哈希分别保存，不回填旧运行记录。决定 compatible 必须说明容差、比较范围及 NaN/边界等情况；pending 阻止验收。文件绑定能检查新鲜度，不能代替科学判断。

## 页数和逐页记录

profile.page_parts 是格式到分区列表的映射，例如：

```json
{"latex":[{"role":"abstract","start":1,"end":1,"max_pages":1},{"role":"body","start":2,"end":5,"max_pages":10}]}
```

数字仅是结构示例，按实际要求填写，不是统一论文配额。分区需覆盖整份对应 PDF，无重叠；首页为物理页 1。总页数约束与分区约束可同时启用。分区标签真实性需要查看页面，软件不猜测哪一页开始正文。

profile.require_page_review=true 时，delivery/visual-review.json 使用以下结构。先查看对应 PDF，再填写：

```json
{"schema":"mm-visual/v2","status":"NOT_REVIEWED","reviewer":"","notes":"","pdfs":{},"pages":{},"page_reviews":{}}
```

pdfs 填 PDF 相对路径到哈希，pages 填格式到总页数，page_reviews 填格式到列表。每页记录 page（从 1 开始）、method（contact_sheet/full_size/zoomed）、status（通过时 passed）、notes（观察内容或已处理缺陷）。缺页、重复页、未解决问题和 PDF 变化都会拒绝验收。复杂公式和密集图表通常需要放大，联系表不足以证明所有细节正确；如实记录检查方式，不自动填写 PASS。
