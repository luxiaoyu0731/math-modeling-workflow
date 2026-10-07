# 从合成示例跑通

示例只有基础算术，不是任何真实赛题、数据或论文。不会调用 ImageGen，也不伪造图像调用记录。

在仓库根目录运行，目标目录必须不存在：

```sh
python3 examples/create_demo.py --destination /tmp/mm-demo
python3 scripts/paper.py --project /tmp/mm-demo audit
python3 scripts/paper.py --project /tmp/mm-demo build --formats latex
python3 scripts/paper.py --project /tmp/mm-demo render --format latex
python3 scripts/paper.py --project /tmp/mm-demo verify
```

Windows 把 `/tmp/mm-demo` 换成自己的新目录。构建 TeX 不需要文档依赖；实际渲染需要 XeLaTeX 及 docs/requirements.txt 中的 PDF 依赖。先运行 `python3 scripts/paper.py doctor`。需要 Word 时将 build 的格式换成 docx；render 也换成 docx，并准备 LibreOffice。

预期：audit 返回 PASS，build 返回 BUILT_REVIEW_REQUIRED，render 产生 PDF；**最后 verify 应因尚未视觉审核而失败**。这表示检查在正常工作。打开实际 PDF 查看每一页，再按 [审核合同](review-contracts.md) 写入记录，不能直接复制测试里的虚构审核数据。

体验已有工程模式：

```sh
python3 examples/create_demo.py --destination /tmp/mm-native --mode existing_tex
python3 scripts/paper.py --project /tmp/mm-native audit
python3 scripts/paper.py --project /tmp/mm-native build --formats latex
python3 scripts/paper.py --project /tmp/mm-native render --format latex
```

它会在临时目录复制声明过的源文件并编译，原来的 main.tex 不被改写。接入自己的工程见 [已有 TeX 工程](existing-project.md)。
