# v0.2 资料与素材来源

核对日期：2026-11-18。使用官方文档、官方模型卡和原始论文；模型表是代表性规格示例，不是最新模型榜单。页面与模型仓库之后可能更新。

## 模型、文件与训练

- Hugging Face LLM Course：https://huggingface.co/learn/llm-course/chapter1/4
- SFT：https://huggingface.co/learn/llm-course/chapter11/1
- Chat templates：https://huggingface.co/docs/transformers/main/en/chat_templating
- Qwen3-8B 文件：https://huggingface.co/Qwen/Qwen3-8B/tree/main
- Qwen3-8B 配置：https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json
- Qwen3 官方说明：https://qwenlm.github.io/blog/qwen3/
- Qwen3-32B：https://huggingface.co/Qwen/Qwen3-32B
- Qwen3-30B-A3B：https://huggingface.co/Qwen/Qwen3-30B-A3B
- Qwen3-235B-A22B：https://huggingface.co/Qwen/Qwen3-235B-A22B
- DeepSeek-V3：https://huggingface.co/deepseek-ai/DeepSeek-V3
- Llama-3.3-70B-Instruct：https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct
- Safetensors：https://huggingface.co/docs/safetensors/index
- 量化：https://huggingface.co/docs/transformers/main/en/quantization/overview
- LoRA：https://huggingface.co/docs/peft/main/en/conceptual_guides/lora
- RLHF / InstructGPT：https://arxiv.org/abs/2203.02155
- 蒸馏：https://arxiv.org/abs/1503.02531
- 真实分词样例使用 tiktoken cl100k_base：https://github.com/openai/tiktoken

## 检索、工具与 Agent

- RAG：https://arxiv.org/abs/2005.11401
- Sentence Transformers 相似性：https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html
- 上下文工程：https://www.anthropic.com/research/effective-context-engineering-for-ai-agents
- 工具调用：https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Workflow / Agent：https://www.anthropic.com/research/building-effective-agents
- ReAct：https://arxiv.org/abs/2210.03629
- Harness：https://www.anthropic.com/research/effective-harnesses-for-long-running-agents
- MCP：https://modelcontextprotocol.io/docs/getting-started/intro
- MCP 架构：https://modelcontextprotocol.io/docs/learn/architecture
- Agent Skills：https://agentskills.io/home

## 教学数据与图片

- 公司差旅制度、报销任务、汇率、金额、工具响应与预写回答均是教学设定，不代表真实公司的规定或实时市场信息。
- Token 分词取指定分词器的实际结果。Embedding 数值与二维相似性示意仅为教学构造，不冒充模型实际输出。
- 文件列表依据公开官方模型仓库摘录并重排，已明确标注非网页截图。本机浏览器访问官方站点超时，没有将重排视图冒充原始网页。素材来源记录在 assets/manifest.json。
- AI 生成插图仅解释概念，不代表完整网络结构或真实产品界面；Dense/MoE 图为局部前馈层示意，4 选 2 专家不代表 Qwen 的实际专家数量。
- 中文字体及基础样式沿用工作区既有许可记录，见 ../deck/THIRD-PARTY-NOTICES.txt。
