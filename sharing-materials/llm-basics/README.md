# 大模型常见概念分享

当前版本 **v0.5**，2026-11-19。以公司差旅助手为贯穿案例，面向无需机器学习背景的 IT 同事。

- [离线 HTML 演示](exports/llm-basics-slides-v0.5.html)
- [PDF 阅读版](exports/llm-basics-slides-v0.5.pdf)
- [逐页讲稿](exports/llm-basics-speech-v0.5.md)
- [本版大纲](outline-v0.5.md)
- [v0.4 逐页审阅与新旧页码](review-v0.4.md)
- [制作源码与重建说明](v0.5/README.md)
- [资料与素材来源](v0.5/sources.md)

共 45 页。P01–P43 为主讲与回顾，建议约 70 分钟，另留交流时间。P44–P45 为参考资料和演示口径。

## 内容

开场提出一笔需要核对的差旅费用。先认识模型和两种调用方式，再沿实际模型仓库讲分词、生成、权重加载、规格和推理服务。接下来用 SFT 样本、人工偏好和两轮对话解释训练与线上请求。

应用部分拆解一次上下文请求，再讲制度召回、重排、引用核对和两次工具调用。ReAct 演示比较有无审批记录时的下一步，随后介绍 Harness、MCP 与 Skill。最后展示开场同一笔费用的核对说明，用报告评测和不存在的条款回顾。

P24 讲稿可复制完整 vLLM 请求体。各页来源随讲稿列出，模型规格沿用 2026-11-18 核对的资料。

## 使用

HTML 可独立离线打开，字体、图片、样式、交互和讲稿均已内嵌。方向键或空格翻页；`G` 打开目录；`N` 打开当前页讲稿及来源；`F` 全屏。手机支持滑动翻页，建议横屏。页面按 1920×1080 画布整体缩放。

`E` 开关文字编辑；编辑保存到当前浏览器，`Ctrl+S` 下载修改后的 HTML。下载内容不会自动同步制作源码、PDF 和 Markdown 讲稿。

五个离线演示如下。

1. 分别查看中文、英文和代码的实际分词结果。
2. 逐步追加单个 Token，观察新内容怎样接回上下文。
3. 对照 SFT 样本和聊天模板，切换轮次观察历史怎样进入推理请求。
4. 查看工具请求、程序执行、工具结果与最终回答。
5. 切换有无审批记录，观察 ReAct 如何选择不同的下一步。

PDF 展开三种真实分词、单 Token 追加、两次工具调用和 ReAct 的审批分支。聊天模板页展示第二轮请求。现场操作使用 HTML。

## 历史版本

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
