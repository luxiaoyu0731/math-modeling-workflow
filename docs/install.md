# 安装与打包

先下载或克隆仓库。直接读取skill无需安装；需要客户端发现入口时，可安装到独立项目：

```sh
python3 scripts/package.py install --platform codex --target <project-directory>
```

platform支持codex、claude、trae。安装器复制9个技能、各自参考资料和完整运行时到项目中；不覆盖同名技能、已有运行时或AGENTS.md，不写全局配置。重复安装会明确停止。升级前由用户保留项目运行数据，选择新目录安装，暂不提供破坏性覆盖升级。

安装后让助手读取所需skill。完整运行时在项目的.math-modeling/；命令示例：

```sh
python3 .math-modeling/scripts/paper.py --project <run-directory> doctor
```

## 可重建分享包

```sh
python3 scripts/package.py archive --output <new-archive.zip>
```

压缩包使用固定时间戳、明确文件列表和SHA-256清单。忽略运行数据、状态、构建成品、Git历史及缓存。命令拒绝覆盖现有压缩包。相同源文件重复打包应字节一致。

本仓库只包含通用规则与合成软件验收材料，不含赛题或真实论文实例。
