# 大模型常见概念分享

当前版本 **v0.4**，2026-11-18。以公司差旅助手为贯穿案例，面向无需机器学习背景的 IT 同事。

- [离线 HTML 演示](exports/llm-basics-slides-v0.4.html)
- [PDF 阅读版](exports/llm-basics-slides-v0.4.pdf)
- [逐页讲稿](exports/llm-basics-speech-v0.4.md)
- [本版大纲](outline-v0.4.md)
- [v0.3 逐页审阅与新旧页码](review-v0.3.md)
- [制作源码与重建说明](v0.4/README.md)
- [资料与素材来源](v0.4/sources.md)

共 48 页。P01–P32 为主讲与回顾，建议约 60 分钟，另留交流时间。P33–P45 按听众问题选讲，P46–P48 为参考资料与示例说明。

## 内容

开场先看差旅助手怎样给出缺乏依据的报销结论。接着介绍模型、API、自部署、Token、训练和对话。通过真实分词、单 Token 追加和两轮对话，观察模型怎样处理输入。

应用部分拆解一次上下文请求，再从制度检索、汇率查询和程序算账逐步走到 Agent。ReAct 演示比较有无审批记录时的下一步。最后展示同一笔费用的核对说明，用一条不存在的制度条款做交流题。

模型配置和权重分片、Dense 与 MoE、数值格式、量化、InstructGPT 的 RLHF、Embedding 和重排留在附录。各页讲稿附参考链接，P16 讲稿可复制完整 vLLM 请求体。

## 使用

HTML 可独立离线打开，字体、图片、样式、交互和讲稿均已内嵌。方向键或空格翻页；`G` 打开目录；`N` 打开当前页讲稿及来源；`F` 全屏。手机支持滑动翻页，建议横屏。页面按 1920×1080 画布整体缩放。

`E` 开关文字编辑；编辑保存到当前浏览器，`Ctrl+S` 下载修改后的 HTML。下载内容不会自动同步制作源码、PDF 和 Markdown 讲稿。

五个离线演示如下。

1. 分别查看中文、英文和代码的实际分词结果。
2. 逐步追加单个 Token，观察新内容怎样接回上下文。
3. 对照 SFT 样本和聊天模板，切换轮次观察历史怎样进入推理请求。
4. 查看工具请求、程序执行、工具结果与最终回答。
5. 切换有无审批记录，观察 ReAct 如何选择不同的下一步。

PDF 展开单 Token 追加、两次工具调用和 ReAct 的审批分支。聊天模板页展示第二轮请求，分词页展示中文样例。现场操作使用 HTML。

## 历史版本

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

v0.1 源码在 `deck/`。v0.2 和 v0.3 的源码分别在对应版本目录。
