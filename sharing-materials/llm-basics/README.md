# 大模型常见概念分享

当前版本 **v0.6**，2026-11-19。以公司差旅助手为贯穿案例，面向无需机器学习背景的 IT 同事。

- [离线 HTML 演示](exports/llm-basics-slides-v0.6.html)
- [PDF 阅读版](exports/llm-basics-slides-v0.6.pdf)
- [逐页讲稿](exports/llm-basics-speech-v0.6.md)
- [本版大纲与 v0.5 页码对照](outline-v0.6.md)
- [制作源码与重建说明](v0.6/README.md)
- [资料与素材来源](v0.6/sources.md)

共 38 页。P01–P36 为主讲与回顾，建议约 70 分钟，另留交流时间。P37–P38 为参考资料和演示口径。

## 内容

先讲 AI、深度学习和 NLP，再用实际模型仓库讲分词、生成、权重加载和模型规格。比较预训练、监督微调和对齐，演示续写模型如何在助手轮次作答。

应用部分从提示词进入完整的上下文请求，再讲制度召回、重排、引用核对和两次工具调用。ReAct 演示比较有无审批记录时的下一步，随后介绍 Harness、MCP 与 Skill。最后用差旅核对说明回顾如何评测和排查问题。

P17 讲稿可复制完整 vLLM 请求体。各页核对材料随讲稿列出。

## 使用

HTML 可独立离线打开，字体、图片、样式、交互和讲稿均已内嵌。方向键或空格翻页；`G` 打开目录；`N` 打开当前页讲稿及来源；`F` 全屏。手机支持滑动翻页，建议横屏。页面按 1920×1080 画布整体缩放。

`E` 开关文字编辑；编辑保存到当前浏览器，`Ctrl+S` 下载修改后的 HTML。下载内容不会自动同步制作源码、PDF 和 Markdown 讲稿。

五个离线演示如下。

1. 对照词表查看英文分词，切换中文和代码示例。
2. 逐步追加 Token，看到模型输出结束符时如何停止生成。
3. 对照示范对话与助手的续写起点，切换到第二轮观察历史怎样带回。
4. 查看工具请求、程序执行、工具结果与最终回答。
5. 切换有无审批记录，观察 ReAct 如何选择不同的下一步。

PDF 展开三种真实分词、单 Token 追加、两次工具调用和 ReAct 的审批分支。聊天模板页展示第二轮请求。现场操作使用 HTML。

## 历史版本

- [v0.5 HTML](exports/llm-basics-slides-v0.5.html)
- [v0.5 PDF](exports/llm-basics-slides-v0.5.pdf)
- [v0.5 讲稿](exports/llm-basics-speech-v0.5.md)
- [v0.5 大纲](outline-v0.5.md)
- [v0.4 逐页审阅与新旧页码](review-v0.4.md)
- [v0.4 HTML](exports/llm-basics-slides-v0.4.html)
- [v0.4 PDF](exports/llm-basics-slides-v0.4.pdf)
- [v0.4 讲稿](exports/llm-basics-speech-v0.4.md)
- [v0.4 大纲](outline-v0.4.md)
- [v0.3 逐页审阅](review-v0.3.md)
- [v0.3 HTML](exports/llm-basics-slides-v0.3.html)
- [v0.3 PDF](exports/llm-basics-slides-v0.3.pdf)
- [v0.3 讲稿](exports/llm-basics-speech-v0.3.md)
- [v0.3 大纲](outline-v0.3.md)
- [v0.2 HTML](exports/llm-basics-slides-v0.2.html)
- [v0.2 PDF](exports/llm-basics-slides-v0.2.pdf)
- [v0.2 讲稿](exports/llm-basics-speech-v0.2.md)
- [v0.2 大纲](outline-v0.2.md)
- [v0.1 HTML](exports/llm-basics-slides-v0.1.html)
- [v0.1 PDF](exports/llm-basics-slides-v0.1.pdf)
- [v0.1 讲稿](exports/llm-basics-speech-v0.1.md)
- [原始大纲](outline.md)

v0.1 源码在 `deck/`。后续各版源码在对应版本目录。
