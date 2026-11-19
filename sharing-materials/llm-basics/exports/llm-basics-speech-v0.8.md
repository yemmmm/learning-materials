# 大模型常见概念：一个模型如何成为 AI 助手

v0.8 · 2026-11-19。对应 36 页演示。

P01–P34 为主讲与回顾，P35–P36 为参考资料与演示说明。建议约 70 分钟，另留交流时间。

| 页码 | 内容 | 预计用时 |
| --- | --- | --- |
| P01–P05 | 开场、NLP、语言模型、使用方式与仓库 | 9 分钟 |
| P06–P13 | 分词、生成、加载、规格与推理服务 | 15 分钟 |
| P14–P17 | 训练、对话、提示词和上下文 | 11 分钟 |
| P18–P21 | 召回、重排序、Embedding 和单次工具调用 | 10 分钟 |
| P22–P28 | 提交报销、ReAct、Harness 与任务方法 | 12 分钟 |
| P29–P34 | 多模态、交付、任务评测与推理指标 | 9 分钟 |

## P01 大模型常见概念

今天用一笔报销任务理解常见的大模型概念。案例包含一晚 560 元的住宿和一笔 120 新币的费用。先看模型的文件怎样支撑生成和部署，再看模型接收到的对话与资料。最后沿着工具执行的结果，看固定流程和 Agent 分别怎样推进任务。整场用同一笔费用收尾。

## P02 人工智能、深度学习与自然语言处理

先从 AI 缩到机器学习，再看到神经网络和多层网络。左边说的是技术，右边说的是用这些技术能做的语言任务。比如系统读到「在上海住了两晚，共 980 元」，可以抓取城市、晚数和金额，也可以按别的指令归类或回答问题。现代大语言模型让多种语言任务可以用同一个模型处理。

来源（不朗读）：

- [Hugging Face · 自然语言处理的常见任务](https://huggingface.co/learn/llm-course/chapter1/2)

## P03 大语言模型与 NLP 的发展

这是神经网络在 NLP 中的几个节点。RNN 逐步读入序列，LSTM 是其中一种改进。Transformer 引入以注意力为基础的架构。BERT 和 GPT 都基于 Transformer，BERT 侧重语言理解，GPT 系列沿逐步生成的路线发展。2022 年的 ChatGPT 从 GPT‑3.5 系列模型微调而来，公众可以用聊天界面直接体验。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [Hochreiter 与 Schmidhuber · LSTM（1997）](https://doi.org/10.1162/neco.1997.9.8.1735)
- [Vaswani 等 · Transformer（2017）](https://arxiv.org/abs/1706.03762)
- [Devlin 等 · BERT（2018）](https://arxiv.org/abs/1810.04805)
- [OpenAI · 首次发布 ChatGPT（2022）](https://openai.com/index/chatgpt/)

## P04 托管 API 与自行部署

先问谁负责让模型上线。团队用托管服务时主要关心业务输入和用量。团队自行部署时，需要取得权重并核对发布许可。接下来看一个公开的模型仓库里可以下载哪些文件。

来源（不朗读）：

- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P05 模型仓库的三类文件

左边是官方文件列表的节选，颜色对应三类文件。权重有五个分片，索引记录每个张量放在哪一片。分词器也有几个文件，词表里的编号要和切分规则一起使用。下一页打开 vocab.json 看一段实际记录。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)
- [Qwen3-8B · vocab.json](https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/vocab.json)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)

## P06 Token 与 Token ID

【演示】先从 Hello, world! 找到词表的四条记录，再切换中文和代码。前导空格随 world 进入同一个 Token。Token 可能是词、词的一部分、标点或字符的部分字节。这里的分词和词表都来自 Qwen3-8B。

来源（不朗读）：

- [Qwen3-8B · tokenizer.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json)
- [Qwen3-8B · vocab.json](https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/vocab.json)

## P07 逐个 Token 生成文本

【演示】依次点 pending、句号和结束符。自回归指每一步都以当前序列为条件，这个序列包含提示词和此前已生成的 Token。句号是普通 Token，例子最后选中 <|im_end|> 才触发停止。这是 Qwen3-8B 配置的结束标记之一。服务也可以按最大输出长度等限制停下。生成依赖加载好的网络和权重，接下来拆开看。

来源（不朗读）：

- [Transformers · 文本生成策略](https://huggingface.co/docs/transformers/generation_strategies)
- [Qwen3-8B · tokenizer.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)
- [Qwen3-8B · 生成与停止设置](https://huggingface.co/Qwen/Qwen3-8B/blob/main/generation_config.json)

## P08 网络结构与模型权重

左图是简化的前馈网络，粗线上的 0.8 是教学示意。右上看配置的 36 层和 4,096 维。右下是从真实二进制分片读出的输入词嵌入张量，形状和 BF16 来自文件头，三个数值从二进制参数区解码并四舍五入。Token ID 对应词嵌入矩阵的一行。框架用 Qwen3 的 Transformer 实现构建各层，读取索引定位权重，例如输入词嵌入在第 1 片、输出层在第 5 片。

来源（不朗读）：

- [Michael Clark · 前馈神经网络示意图](https://m-clark.github.io/img/nnet.png)
- [Qwen3-8B · config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json)
- [Qwen3-8B · 权重分片索引](https://huggingface.co/Qwen/Qwen3-8B/blob/main/model.safetensors.index.json)
- [Qwen3-8B · 第 1 个 Safetensors 权重分片](https://modelscope.cn/models/Qwen/Qwen3-8B/file/view/master/model-00001-of-00005.safetensors)
- [Safetensors · 分片元数据读取说明](https://huggingface.co/docs/safetensors/metadata_parsing)

## P09 模型名称里的参数量和量化规格

第一行的模型是 Dense，官方模型卡的总参数是 8.2B，AWQ 配置为 4 位。第二行是 MoE，官方给出 30.5B 总参数和 3.3B 激活参数。FP8 指这个发布版本主要权重采用 8 位浮点量化。先用下一页解释为什么会有 A3B，再估算较低位宽对权重大小的影响。

来源（不朗读）：

- [Qwen3-8B · 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-8B-AWQ · 量化配置](https://huggingface.co/Qwen/Qwen3-8B-AWQ/blob/main/config.json)
- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-30B-A3B-FP8 · 量化配置](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)

## P10 Dense 与 MoE 的前馈层

左图的 FFN 是前馈网络。右图中的专家是子网络，路由按 Token 选中一部分。四选二是教学示意，Qwen3-30B-A3B 的模型卡列出 128 个专家，每个 Token 选 8 个。A3B 加上了共享部分所用的参数，描述每个 Token 激活的总规模。

来源（不朗读）：

- [Qwen3-8B · 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P11 低精度、量化与蒸馏

低精度格式例如 FP8 和 INT4。量化可以在训练后进行，也可以在训练中考虑量化误差。左侧假设所有权重用同一位宽，只计算十进制 GB；部署还需给其他数据和运行状态留空间。蒸馏的关键是来自教师的训练信号，例如用教师的预测概率或输出答案训练学生。两种方法可以组合。

来源（不朗读）：

- [Transformers · 量化与数值格式](https://huggingface.co/docs/transformers/quantization/concept_guide)
- [Lin 等 · AWQ](https://arxiv.org/abs/2306.00978)
- [Hinton 等 · 知识蒸馏](https://arxiv.org/abs/1503.02531)

## P12 同一模型的原始权重与量化版本

指前两行的参数规模。量化改变数值表示，同一发布系列的参数规模保持一致。AWQ 借助激活统计保护重要权重，GPTQ 用校准数据逐层减小误差。实际部署可以先看框架是否支持模型和文件，再用业务样例核对量化效果。

来源（不朗读）：

- [Qwen3-8B · 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-8B-AWQ · 量化配置](https://huggingface.co/Qwen/Qwen3-8B-AWQ/blob/main/config.json)
- [Qwen3-8B-GGUF · 权重文件](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main)
- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-30B-A3B-FP8 · 量化配置](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)
- [Lin 等 · AWQ](https://arxiv.org/abs/2306.00978)
- [Frantar 等 · GPTQ](https://arxiv.org/abs/2210.17323)
- [GGML · GGUF 文件格式](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md)

## P13 训练后的模型怎样提供推理服务？

上面只在训练产出和服务启动时发生。微调也可能只产出适配器，例如 LoRA。下面是 API 上的一次往返，应用给问题和资料，推理框架组织生成并返回答复。vLLM 和 SGLang 可提供并发推理服务，Transformers 提供模型实现和生成接口，llama.cpp 常用于本地运行 GGUF 模型。接下来看看训练中的不同阶段让模型学到什么。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)
- [vLLM · Chat Completions 请求结构](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- [PEFT · LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)

## P14 预训练、监督微调与对齐

左侧的信号来自原始文本的后续内容。中间的信号来自示范答案，帮助模型学会按任务要求作答。右侧是在学哪种回答更好：标注者给同一问题的候选回答排序，InstructGPT 用排序训练奖励模型，再用评分和 PPO 更新助手。这是偏好对齐的一种做法。对齐是更广的训练目标，监督微调也可以用于对齐。下一页单看对话样本如何教模型扮演助手。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)

## P15 续写模型怎样成为对话助手

【演示】两侧都已提供每晚 500 元、超标须事前审批的制度。训练时给出用户和助手的完整对话，示范一个合适的回答。使用时，应用提供用户问题，模板在末尾加上助手的起始标记。模型仍然预测下一个 Token，续写的这段话就是回复。点第二轮，指一下上一轮的回复和新的起始位置。比如 Qwen3 的模板用 <|im_start|>assistant 标记开始，用 <|im_end|> 标记结束。更流畅的作答仍依赖这次请求确实带上了正确的依据。

来源（不朗读）：

- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)

## P16 提示词是什么，怎样写清楚？

「帮我整理好」就是一条提示词，但它没说要什么字段，也没交代缺项怎么处理。右边把结果、取值范围和格式写清楚，示例又说明了 JSON 怎么写。本次输入没有晚数，用 null 表示。Few-shot 示例随本次请求送入模型。接下来从一段任务指令扩展到整次请求，看还需要带哪些信息。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P17 一次请求里的上下文与窗口

沿左侧从上到下看。这条请求有四条消息，最后一条 user 消息含制度与问题，图里把它拆开说明用途。应用留住了必要历史和条款，可以舍去无关机票记录。如果这轮涉及工具，还可按需提供工具说明和实际回执。300 是这次请求的生成上限，仍需在模型窗口里留出空间。按给定规则，两晚共花 1,120 元，超标 120 元，审批仍待核验。接下来讲这些原始条款怎样找出来。

完整请求体

    {
      "model": "Qwen/Qwen3-8B",
      "max_completion_tokens": 300,
      "messages": [
        {"role": "system", "content": "按给定差旅制度回答。"},
        {"role": "user", "content": "一晚花了 560 元，能全额报销吗？"},
        {"role": "assistant", "content": "超出 60 元。全额报销要看事前审批记录。"},
        {"role": "user", "content": "§3.2 上限 500 元/晚。§3.3 超标须事前审批。\n问题：两晚各花了 560 元呢？"}
      ]
    }

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [vLLM · Chat Completions 请求结构](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)

## P18 RAG 怎样查到条款并回答？

上一页把两段条款手动写进请求。实际用 RAG 时，先准备可检索的制度片段，保留编号和出处。收到问题后，用向量、关键词或混合检索找一批候选。这里召回同时命中住宿、审批和机票，重排序再逐一比较每段与本轮问题的相关性，把住宿和审批推到前面。应用取前两段交给模型。§3.2 给出每晚 500 元，§3.3 给出审批条件，回答可据此算出两晚超标 120 元。重排序是这个示例中的一步，结果仍要核对版本和适用范围。下一页看语义召回如何用文本向量。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Sentence Transformers · 召回与重排](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)

## P19 文本 Embedding 与 Token ID

先看住酒店和住宿标准。这两段文字分别进同一个检索模型，得到两组数，应用可以用余弦相似度一类的度量找相关篇章。例子里省略了多数维度，数值是预写的。再想起前面词表中的 Hello，9707 只是查词表或词嵌入矩阵的索引。差旅制度可以走检索，另外一笔 120 新币需要查指定日期的汇率，接下来用工具调用完成。

来源（不朗读）：

- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Qwen3-8B · vocab.json](https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/vocab.json)

## P20 Function Calling 的调用请求

指一下左边工具说明中的金额、币种和日期，再看右边由模型填出的参数。此时是模型提出调用。下一页看应用怎样执行这一次换算，并把结果交还模型。

来源（不朗读）：

- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P21 一次工具调用完成换算

【演示】本例把「今天」设为 2026-11-08。先看模型给出的一次工具请求。应用执行 convert_currency，在一次调用中查询汇率并换算，把汇率和金额一起回传。模型随后依据回执写出 636 元。现在把目标换成提交整笔差旅报销申请，助手还要处理制度和审批。

来源（不朗读）：

- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P22 Workflow 与 Agent 的决策分工

两边都能处理这笔费用，差别是主要路径由谁决定。左侧由程序定义审批条件与分支。右侧先看结果再判断缺什么，应用按授权执行它选的动作。下一页只改变最后一份材料，看选择怎样改变。

来源（不朗读）：

- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P23 ReAct 的行动与观察

【演示】用户目标是提交申请。先走完前三步，第四步切换审批记录，再点提交结果。缺记录时保存草稿并向用户要补件。有记录的分支预设审批系统核验通过，应用调用提交工具，收到教学申请单号 DEMO-018 后才报告已提交。整页为离线模拟，判断栏是讲述用的状态摘要。下一页讲模型提出动作后，由谁执行和记住进度。

来源（不朗读）：

- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P24 什么是 Harness？

用这个式子帮助理解分工。上一页 LLM 提出调用提交工具，Harness 检查可执行条件并代为调用，再把真实回执送回模型。它可以记录制度、费用、待补审批和申请单号，也管理权限、重试和费用上限。不同实现会拆成不同模块。下一页看任务中断后怎样恢复这些状态。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · Agent 与 Harness 评测](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)

## P25 长任务的记忆与上下文压缩

先请大家指出下一轮还要做哪一件事。每次恢复不必逐字带回所有历史，也不能把已确认和待办混淆。这里的记忆依赖模型外的存储和取回，压缩是管理窗口中的信息量。恢复之后，如果仍没有审批，运行环境还要决定这轮在哪里停。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P26 工具执行与停止条件

汇率超时属于运行错误，可以按规则重试。没提供审批是业务缺件，重复问同一个工具不一定有用。沙箱限制执行位置和资源，避免程序越过被允许的范围。工具如何接到应用、做事方法如何复用，就是下一组概念。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P27 Tool、MCP 与 Skill 的分工

在这笔报销里，Skill 的说明帮助决定什么时候要看审批。应用可以通过 MCP 接到审批系统，真正查记录的是一个工具。下一页看报销核对的做法怎样写进 Skill。

来源（不朗读）：

- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P28 Skill 的任务说明与按需加载

这个示例的 Skill 只要求在交付阶段读模板，到核对具体地区时才看对应资料。按需加载可以减少无关说明占用上下文。它与前面训练更新参数是不同的操作。说到开始核对，有时用户提供的金额在票据图片上，接下来看应用怎样取得原始字段。

来源（不朗读）：

- [Agent Skills · 官方格式](https://agentskills.io/home)

## P29 多模态怎样读出票据字段？

左边是示意票据，右边是后续程序要用的四个字段。本页没有在线识别。可以用视觉语言模型直接读取，也可以由 OCR 技术识别文字再解析。语音转写或播报会用到其他能力。下一页把这些模型放回完整应用。

## P30 差旅任务中各类模型的分工

沿着这条链路看输入和输出。Embedding 与重排是生成前的检索环节。计算和系统查询交给程序。文本生成模型擅长把这些内容组织成一份说明。图片和视频生成也可以用各自的模型，需看输入输出能力。最后展示这笔费用实际交出的一页说明。

来源（不朗读）：

- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P31 差旅助手交付的核对说明

这页对应 ReAct 演示的缺件分支。一千一百九十六是差旅费用合计。事前审批待补，申请停在草稿状态。请大家指出金额和当前状态的依据。下一页把同样的核对做成应用评测标准。

## P32 整项任务的效果与成本

按同一套标准核对不同应用版本的结果。换算错、条款找不到、审批被当作完成，都要分别计入。带工具的 Agent 经常执行多次模型请求，评估整项任务比只比较一轮 Token 价格更接近真实使用。最后用一条找不到的制度规定练习定位问题。

来源（不朗读）：

- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P33 助手引用了不存在的条款，怎么排查？

先独立查看适用的制度原文，再沿检索记录和请求定位丢失或错误使用的证据。任务要求不清时可以改提示词，缺外部资料时可以改检索或接口，计算缺口交给工具。如果携带正确依据后仍反复出现稳定的任务行为问题，再评估是否需要训练。最后补看推理服务的常见指标。

## P34 推理服务的常见评价指标

以 vLLM 客户端压测为例，TTFT 从发出请求量到首个流式输出。输出超过一个 Token 时，TPOT 以端到端时延减去 TTFT，再除以输出 Token 数减一。输出吞吐量按整个服务汇总。前缀缓存复用相同输入前缀的计算，命中率按同一观测期的命中 Token 增量除以查询 Token 增量。P50 是中位数，P95 表示约 95% 的请求在该时延以内。这里量的是模型请求，整笔报销任务还包含检索、工具和申请结果的评测。

来源（不朗读）：

- [vLLM · 压测时延与吞吐量](https://docs.vllm.ai/en/v0.33.0/benchmarking/cli/#understanding-the-latency-metrics)
- [vLLM · 生产指标与缓存计数](https://docs.vllm.ai/en/latest/usage/metrics/)

## P35 参考资料

本页供会后找资料。按主题跳到相应页可查看该页的模型配置、论文或协议说明。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [Vaswani 等 · Transformer（2017）](https://arxiv.org/abs/1706.03762)
- [Devlin 等 · BERT（2018）](https://arxiv.org/abs/1810.04805)
- [OpenAI · 首次发布 ChatGPT（2022）](https://openai.com/index/chatgpt/)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Qwen3-8B · vocab.json](https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/vocab.json)
- [Transformers · 量化与数值格式](https://huggingface.co/docs/transformers/quantization/concept_guide)
- [Hinton 等 · 知识蒸馏](https://arxiv.org/abs/1503.02531)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)
- [vLLM · Chat Completions 请求结构](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- [vLLM · 压测时延与吞吐量](https://docs.vllm.ai/en/v0.33.0/benchmarking/cli/#understanding-the-latency-metrics)
- [vLLM · 生产指标与缓存计数](https://docs.vllm.ai/en/latest/usage/metrics/)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Sentence Transformers · 召回与重排](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)

## P36 案例数据与演示口径

整场交互在本地运行。公开的模型规格、代码和物料出处可在逐页讲稿或同版资料说明中查到。
