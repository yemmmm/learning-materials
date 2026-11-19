# 大模型常见概念分享

当前版本 **v0.9**，2026-11-19。面向无需机器学习背景的 IT 同事，介绍模型、推理服务和 Agent 应用中的常见概念。

- [离线 HTML 演示](exports/llm-basics-slides-v0.9.html)
- [PDF 阅读版](exports/llm-basics-slides-v0.9.pdf)
- [逐页讲稿](exports/llm-basics-speech-v0.9.md)
- [本版大纲与新旧页码对照](outline-v0.9.md)
- [制作源码与重建说明](v0.9/README.md)
- [资料与素材来源](v0.9/sources.md)

共 33 页。P01–P31 为主讲与回顾，建议约 65 分钟，另留交流时间。P32–P33 为参考资料和演示口径。

## 内容

先讲 AI、深度学习和 NLP，再用实际模型仓库讲分词、自回归生成、权重文件和推理服务。用翻译和会议通知解释预训练、监督微调、对齐、多轮对话和提示词。

应用部分用差旅案例演示 RAG 和 ReAct，用构建排查示例解释任务状态以及 Tool、MCP 和 Skill 的分工。最后比较非 LLM 模型，说明推理指标，并用一页回顾已讲概念和可选补讲主题。

P17 讲稿可复制完整 vLLM 请求体。各页核对材料随讲稿列出。

## 使用

HTML 可独立离线打开，字体、图片、样式、交互和讲稿均已内嵌。方向键或空格翻页；`G` 打开目录；`N` 打开当前页讲稿及来源；`F` 全屏。手机支持滑动翻页，建议横屏。页面按 1920×1080 画布整体缩放。

`E` 开关文字编辑；编辑保存到当前浏览器，`Ctrl+S` 下载修改后的 HTML。下载内容不会自动同步制作源码、PDF 和 Markdown 讲稿。

五个离线演示如下。

1. 对照词表查看英文分词，切换中文和代码示例。
2. 逐步追加 Token，看到模型输出结束符时如何停止生成。
3. 对照示范对话与助手的续写起点，切换到第二轮观察历史怎样带回。
4. 查看一次换算调用的请求、回执与回答。
5. 切换审批材料并查看提交结果，观察 ReAct 如何在等待补件与提交申请之间切换。

PDF 展开三种真实分词、单 Token 追加、一次换算调用和 ReAct 的提交分支。聊天模板页展示第二轮请求。现场操作使用 HTML。

## 历史版本

- [v0.8 HTML](exports/llm-basics-slides-v0.8.html)
- [v0.8 PDF](exports/llm-basics-slides-v0.8.pdf)
- [v0.8 讲稿](exports/llm-basics-speech-v0.8.md)
- [v0.8 大纲](outline-v0.8.md)
- [v0.7 HTML](exports/llm-basics-slides-v0.7.html)
- [v0.7 PDF](exports/llm-basics-slides-v0.7.pdf)
- [v0.7 讲稿](exports/llm-basics-speech-v0.7.md)
- [v0.7 大纲](outline-v0.7.md)
- [v0.6 HTML](exports/llm-basics-slides-v0.6.html)
- [v0.6 PDF](exports/llm-basics-slides-v0.6.pdf)
- [v0.6 讲稿](exports/llm-basics-speech-v0.6.md)
- [v0.6 大纲](outline-v0.6.md)
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
