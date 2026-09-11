# 工作流内核

从仓库根目录运行。需要 Python 3.10+，内核和测试仅使用标准库。

```sh
python3 workflow/workflow.py new-run --slug my-project
python3 workflow/workflow.py check --state workflow/runs/my-project/state/workflow_state.json
python3 workflow/workflow.py meta-prompt --state workflow/runs/my-project/state/workflow_state.json --task '检查输入并完成当前阶段'
```

`new-run` 不覆盖同名运行；`check` 只读；`meta-prompt` 输出提示词，不调用模型。新建运行出现缺失证据是预期行为。

先完成真实产物，再登记（路径相对于运行目录）：

```sh
python3 workflow/workflow.py register-artifact --state workflow/runs/my-project/state/workflow_state.json --id input_audit --path evidence/input_audit.md --source '实际输入核验'
```

用 `check` 获取当前阶段需要的全部产物。完成内容复核后，使用 `accept-gate --state ... --gate G0 --outputs input_audit,contest_profile --note '实际复核依据'`。不能用此命令补造未完成的内容审核。

修改已登记材料前，执行 `invalidate --state ... --artifact <id> --reason <原因>`，再重做、登记和验收相关下游材料。各命令完整参数见 `python3 workflow/workflow.py --help`。

内核验证存在性、哈希、依赖和阶段顺序，不证明模型正确、引用可靠或图形真实。模板需实例化；不适用的检查应给出理由，不填伪造证据。

新建v8运行在G7要求登记authoring_plan（实际paper-plan.json），G7实时运行内容审计，G8/G9实时运行交付验收。计划中的文件相对于计划所在目录。详见[论文交付](../docs/authoring.md)。历史v7状态不自动迁移。
