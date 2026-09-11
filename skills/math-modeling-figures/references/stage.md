# math-modeling-figures 阶段指南

## 图卡先行
从读者问题确定图的对象、关系、来源、公式、标签和正文位置。A—E用途分类帮助发现缺口，不规定图数、学科场景、配色或论文版本数。

## ImageGen 执行
调用实际可用的ImageGen工具，保存原始提示词与原始输出，不能把CLI生成的提示包当作图片完成。按对象数量、方向、连接、边界及符号核对生成图；精确文字可后期叠加，保存加工记录。生成工具不可用时报告明确阻断并继续其他可独立任务。

## 机器可查的记录
paper-plan.json的figures按ID记录path、sha256、caption、kind、review和review_note。ImageGen图还需prompt_path及其哈希、raw_path及其哈希、tool与generated_at。量化图kind为quantitative，关联data_evidence与code_evidence，禁止生成式图像改写曲线和刻度。

## 接入论文
章节中用 `[[figure:ID]]` 放置图片，不能用未登记图片绕过审核。审核既看科学语义又看最终版面，机器不能自动证明几何或因果正确。实际采用图与淘汰图分别记录。
