# v0.9 资料与素材来源

2026-11-19 核对其他模型页的代表模型及其输入、输出。Agent Harness 和推理指标依据 v0.8 核对的资料，权重节选沿用 v0.7。

## 自然语言处理与大语言模型

- [Hugging Face LLM Course 的 NLP 任务介绍](https://huggingface.co/learn/llm-course/chapter1/2)。
- [LSTM 原始论文（1997）](https://doi.org/10.1162/neco.1997.9.8.1735)，[Transformer 原始论文（2017）](https://arxiv.org/abs/1706.03762)，[BERT 预印本（2018）](https://arxiv.org/abs/1810.04805)。
- 2022-11-30 发布的 ChatGPT 基于 GPT‑3.5 系列模型微调。 [OpenAI 发布说明](https://openai.com/index/chatgpt/)。

## 模型、文件与训练

- Hugging Face LLM Course：https://huggingface.co/learn/llm-course/chapter1/4
- SFT：https://huggingface.co/learn/llm-course/chapter11/1
- Chat templates：https://huggingface.co/docs/transformers/main/en/chat_templating
- Qwen3-8B 文件：https://huggingface.co/Qwen/Qwen3-8B/tree/main
- Qwen3-8B 配置：https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json
- Qwen3-8B 的输入词嵌入权重在第 1 片，输出层权重在第 5 片。 [官方权重分片索引](https://huggingface.co/Qwen/Qwen3-8B/blob/main/model.safetensors.index.json)
- 从 ModelScope 的 Qwen3-8B 第一权重分片读取字节 `0–65535`，服务返回 HTTP 206。文件头给出 `model.embed_tokens.weight` 的数据类型 `BF16` 和形状 `[151936, 4096]`。数据区解码出的前三个值为 `0.049560546875`、`0.037109375`、`0.0291748046875`，演示保留五位小数。 [ModelScope 仓库文件](https://modelscope.cn/models/Qwen/Qwen3-8B/files) · [Safetensors 元数据说明](https://huggingface.co/docs/safetensors/metadata_parsing)
- 用 Qwen3-8B 的 `tokenizer.json` 和 `vocab.json` 核对英文、中文、代码的切分与编号。英文示例的 `Ġworld` 对应含空格的 ` world`。分词校验使用 Hugging Face `tokenizers` 0.22.2。 [固定版本的分词器](https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/tokenizer.json) · [同版本词表](https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/vocab.json)
- 续写示例依次追加 ` pending`（15280）、`.`（13）和 `<|im_end|>`（151645）。后者是 Qwen3-8B 的结束 Token 之一。 [特殊 Token 与模板配置](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json) · [生成配置](https://huggingface.co/Qwen/Qwen3-8B/blob/main/generation_config.json)
- [Transformers 文本生成策略](https://huggingface.co/docs/transformers/generation_strategies)。
- Qwen3 官方说明：https://qwenlm.github.io/blog/qwen3/
- Qwen3-8B BF16 和参数量见 [官方模型卡](https://huggingface.co/Qwen/Qwen3-8B)。
- Qwen3-8B-AWQ 的 `quantization_config.bits` 为 4，`quant_method` 为 `awq`。 [配置文件](https://huggingface.co/Qwen/Qwen3-8B-AWQ/blob/main/config.json)
- Qwen3-8B-GGUF 的 Q4_K_M 文件大小为 5.03 GB。 [文件清单](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main)
- Qwen3-30B-A3B：https://huggingface.co/Qwen/Qwen3-30B-A3B
- Qwen3-30B-A3B-FP8 的量化格式为 E4M3。 [配置文件](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)
- Safetensors：https://huggingface.co/docs/safetensors/index
- [Transformers 量化与数值格式](https://huggingface.co/docs/transformers/quantization/concept_guide)
- [AWQ 原始论文](https://arxiv.org/abs/2306.00978)
- [GPTQ 原始论文](https://arxiv.org/abs/2210.17323)
- [GGUF 文件格式规范](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md)
- LoRA：https://huggingface.co/docs/peft/main/en/conceptual_guides/lora
- InstructGPT 的 §3.1 和图 2 描述 SFT、用人工排序训练奖励模型和 PPO 三步。 [InstructGPT 论文](https://arxiv.org/abs/2203.02155)
- 蒸馏：https://arxiv.org/abs/1503.02531

## 检索、工具与 Agent

- RAG：https://arxiv.org/abs/2005.11401
- 召回与重排序示例参考 [Sentence Transformers 的检索与重排文档](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)。
- Sentence Transformers 相似性：https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html
- 上下文工程：https://www.anthropic.com/research/effective-context-engineering-for-ai-agents
- 上下文窗口页采用 vLLM 的 Chat Completions 请求结构，包含 `model`、`max_completion_tokens` 和 `messages`。 [vLLM 请求模型](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- 工具调用：https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Workflow / Agent：https://www.anthropic.com/research/building-effective-agents
- ReAct：https://arxiv.org/abs/2210.03629
- Harness：https://www.anthropic.com/research/effective-harnesses-for-long-running-agents
- MCP：https://modelcontextprotocol.io/docs/getting-started/intro
- Agent Harness 的输入处理、工具调度及执行结果参见 [Anthropic 的 Agent 评测说明](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)。
- Agent Skills：https://agentskills.io/home

## 推理指标

- TTFT 和 TPOT 按客户端压测口径说明。输出吞吐量按生成的输出 Token 数与观测时长计算。 [vLLM 压测指标](https://docs.vllm.ai/en/v0.33.0/benchmarking/cli/#understanding-the-latency-metrics) · [vLLM 压测实现](https://docs.vllm.ai/en/latest/api/vllm/benchmarks/serve/)
- 前缀缓存命中率使用同一观测期的 `vllm:prefix_cache_hits` 与 `vllm:prefix_cache_queries` 增量，两者均以 Token 数计。 [vLLM 生产指标](https://docs.vllm.ai/en/latest/usage/metrics/)

## LLM 之外的模型

- 文本向量与重排序使用 BAAI 的模型卡。 [BGE-M3](https://huggingface.co/BAAI/bge-m3) · [bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- 文字识别与目标检测分别参考发布方文档。 [PP-OCRv5](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html) · [YOLO11](https://docs.ultralytics.com/models/yolo11/)
- 语音识别使用 Whisper，语音合成用 VITS 作例子。 [Whisper 官方仓库](https://github.com/openai/whisper) · [VITS 原始论文](https://arxiv.org/abs/2106.06103)
- 图像生成以 Stable Diffusion 3.5 系列为例。 [Stability AI 发布说明](https://stability.ai/news-updates/introducing-stable-diffusion-3-5)

## 教学数据与图片

- 会议通知、构建排查、差旅制度、汇率、金额、工具响应和预写回答均为教学设定。
- Token 分词取指定分词器的实际结果。逐步生成内容、Embedding 数值和 ReAct 分支为教学设定。
- Qwen3-8B 文件列表依据官方仓库摘录，以 HTML 重新排版。两幅插图沿用 v0.2 素材。 [素材清单](../v0.2/assets/manifest.json)
- 封面与 Dense/MoE 图由 AI 生成。Dense/MoE 图用四选二示意局部前馈层。
- 前馈神经网络图来自 Michael Clark，演示中裁掉英文标签，添加中文层名与示例权重。 [原图](https://m-clark.github.io/img/nnet.png) · [作者的许可说明](https://m-clark.github.io/#reuse) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- 中文字体及基础样式沿用工作区既有许可记录，见 ../deck/THIRD-PARTY-NOTICES.txt。

## RAG 插图

P18 插图由内置 ImageGen 生成，透明 PNG 保存为 [rag-retrieve-rerank.png](assets/rag-retrieve-rerank.png)。中文标签与条款例子由演示源码排版。

```text
Use case: scientific-educational. Create one panoramic paper-craft illustration for a Chinese introductory presentation. It explains retrieval-augmented generation for a work travel reimbursement question, including reranking. The presentation will add labels below the image.

Make exactly five evenly spaced visual stations in a single continuous horizontal left-to-right journey, centered at approximately 10%, 30%, 50%, 70%, and 90% of the width. Connect adjacent stations with four clean and readily visible right-pointing arrows. Keep the stations about the same height, within one narrow horizontal band in the center. Use the widest landscape composition you can, about 3:1. Keep generous safe margins so none of the artwork is cut off.

1. An incoming speech bubble with a simple hotel-key/bed pictogram.
2. A small indexed file drawer, with a magnifying glass finding a few loose policy excerpts. Some excerpts are dark green and some gray.
3. Three candidate slips sorted into a shortlist, two green lodging-related slips visibly above one gray travel slip, showing how the best evidence moves to the top.
4. A slim open folder gathering the two green slips together with a small speech bubble, visibly combining the evidence and the question.
5. One newly written answer sheet with short schematic lines, green check marks, and a single small amber pending-approval dot.

Match a restrained professional editorial slide deck: off-white paper (#f2f0e8), dark forest green (#163b31), muted sage (#d8e3d2), amber (#9b6630), and cool gray. Small paper-cut shadows and simple shapes that project cleanly. Transparent background outside the objects and arrows. No compartment boxes, decorative icons, people, headings, letters, characters, numbers, fake writing, badges, legends, or watermark. Paper marks may be plain horizontal lines only.
```
