# v0.4 资料与素材来源

模型规格、训练流程和接口示例沿用 v0.3 在 2026-11-18 核对的资料。本版用 cl100k_base 核对了分步追加的两个 Token，分别是带前导空格的 ¥（ID 72588）和 560（ID 17698）。

## 模型、文件与训练

- Hugging Face LLM Course：https://huggingface.co/learn/llm-course/chapter1/4
- SFT：https://huggingface.co/learn/llm-course/chapter11/1
- Chat templates：https://huggingface.co/docs/transformers/main/en/chat_templating
- Qwen3-8B 文件：https://huggingface.co/Qwen/Qwen3-8B/tree/main
- Qwen3-8B 配置：https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json
- Qwen3-8B 的输入词嵌入权重在第 1 片，输出层权重在第 5 片。 [官方权重分片索引](https://huggingface.co/Qwen/Qwen3-8B/blob/main/model.safetensors.index.json)
- 用 Qwen3-8B 的分词文件核对了 `Hello, world!` 的 Token ID `[9707, 11, 1879, 0]`。 [官方分词文件](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json) · [特殊 Token 与模板配置](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)
- Qwen3 官方说明：https://qwenlm.github.io/blog/qwen3/
- Qwen3-8B BF16 和参数量见 [官方模型卡](https://huggingface.co/Qwen/Qwen3-8B)。
- Qwen3-8B-AWQ 的 `quantization_config.bits` 为 4，`quant_method` 为 `awq`。 [配置文件](https://huggingface.co/Qwen/Qwen3-8B-AWQ/blob/main/config.json)
- Qwen3-8B-GGUF 的 Q4_K_M 文件大小为 5.03 GB。 [文件清单](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main)
- Qwen3-30B-A3B：https://huggingface.co/Qwen/Qwen3-30B-A3B
- Qwen3-235B-A22B：https://huggingface.co/Qwen/Qwen3-235B-A22B
- Qwen3-30B-A3B-FP8 的量化格式为 E4M3。 [配置文件](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)
- Safetensors：https://huggingface.co/docs/safetensors/index
- [Transformers 量化与数值格式](https://huggingface.co/docs/transformers/quantization/concept_guide)
- [AWQ 原始论文](https://arxiv.org/abs/2306.00978)
- [GPTQ 原始论文](https://arxiv.org/abs/2210.17323)
- [GGUF 文件格式规范](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md)
- LoRA：https://huggingface.co/docs/peft/main/en/conceptual_guides/lora
- InstructGPT 的 §3.1 和图 2 描述 SFT、用人工排序训练奖励模型和 PPO 三步。 [InstructGPT 论文](https://arxiv.org/abs/2203.02155)
- 蒸馏：https://arxiv.org/abs/1503.02531
- [tiktoken 与 cl100k_base](https://github.com/openai/tiktoken) 用于分词与生成步骤的 Token 边界核对。

## 检索、工具与 Agent

- RAG：https://arxiv.org/abs/2005.11401
- Sentence Transformers 相似性：https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html
- 上下文工程：https://www.anthropic.com/research/effective-context-engineering-for-ai-agents
- 上下文窗口页采用 vLLM 的 Chat Completions 请求结构，包含 `model`、`max_completion_tokens` 和 `messages`。 [vLLM 请求模型](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- 工具调用：https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Workflow / Agent：https://www.anthropic.com/research/building-effective-agents
- ReAct：https://arxiv.org/abs/2210.03629
- Harness：https://www.anthropic.com/research/effective-harnesses-for-long-running-agents
- MCP：https://modelcontextprotocol.io/docs/getting-started/intro
- MCP 架构：https://modelcontextprotocol.io/docs/learn/architecture
- Agent Skills：https://agentskills.io/home

## 教学数据与图片

- 公司差旅制度、报销任务、汇率、金额、工具响应与预写回答均是教学设定，不代表真实公司的规定或实时市场信息。
- Token 分词取指定分词器的实际结果。逐步生成内容、Embedding 数值和 ReAct 分支为教学设定。
- Qwen3-8B 文件列表依据官方仓库摘录，以 HTML 重新排版。两幅插图沿用 v0.2 素材。 [素材清单](../v0.2/assets/manifest.json)
- 封面与 Dense/MoE 图由 AI 生成。Dense/MoE 图用四选二示意局部前馈层。
- 中文字体及基础样式沿用工作区既有许可记录，见 ../deck/THIRD-PARTY-NOTICES.txt。
