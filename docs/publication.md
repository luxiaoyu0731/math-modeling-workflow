# 公开范围与来源

发布内容是通用工作流内核、阶段提示词、空模板及重写的可移植技能说明。未复制原始提示词文档、私有技能库整体、第三方插件整包、题目、论文、论文生成图、数据、运行状态或历史审计记录。README 的通用宣传插画单独位于 docs/assets，并保存实际查看与哈希记录。

本包保留现有工作流接口，并去掉具体任务的视觉与格式设置。ImageGen 是单一图形工作流，定量数据层仍需可复算。

检索过 [MathModel-Skill](https://github.com/yushui2022/MathModel-Skill) 作为同类方案参考，其仓库展示MIT许可和分阶段实现；本次增强复用其MIT公式转换模块，并保留固定提交和许可；其余工作流实现按现有接口独立编写。详见THIRD_PARTY_NOTICES.md。

本仓库原创部分采用根目录 MIT LICENSE；复用的公式模块遵循保留的上游 MIT 许可。第三方工具和服务遵循各自条款。

发布前检查：只提交本目录明确选择的通用文件；检查个人路径、联系方式、凭据、具体题目与结果；运行内核测试、模板路径和技能入口检查；核对暂存区。忽略规则不等于历史清理，勿将已有私人仓库历史推入公开仓库。


## 实际发布命令与检查顺序

```sh
python3 -B -m unittest discover -s workflow/tests -v
python3 -B -m unittest discover -s tests -v
python3 scripts/release_check.py --git . --mode tracked
python3 scripts/release_check.py --git . --mode index
python3 scripts/release_check.py --git . --mode history
python3 scripts/package.py archive --output /tmp/math-modeling-workflow.zip
python3 scripts/release_check.py --zip /tmp/math-modeling-workflow.zip
```

tracked 只看已追踪文件的工作区内容，不包含未追踪新增文件；index 检查整个将提交的索引内容；history 检查所有本地引用可达的文件历史。新增文件在实际 ZIP 中也会按发布白名单扫描。Git 作者姓名/邮箱、远程地址和历史提交消息仍需人工核对，不应宣称仅做内容扫描已清理整个历史。

可传 `--terms <private-list.txt>` 指定本任务不应公开的题名、人名或标识，每行一项；词表留在仓库外。扫描结果仅输出规则、文件与行号，不输出命中的凭据文本。默认不会自动识别所有真实题目或个人信息，不能用 PASS 代替内容审阅。

正式发布就绪记录应写明：提交范围、测试实际通过/跳过项、渲染已验证格式、扫描范围、ZIP SHA-256、未验证环境、许可证及上游来源检查。确认后才按用户授权提交/推送；脚本不会操作 Git 分支或自动上传。远端 CI 未执行时明确记录，不提前宣称通过。

公开插画使用同目录 asset-review.json（mm-public-assets/v1）记录 reviewer、reviewed_at、assets；每张图含 sha256、status=passed 和实际查看 notes。扫描器仅解除匹配哈希图片的二进制待审状态，路径/凭据/题目词告警仍保留。声明不能代替真实视觉检查。
