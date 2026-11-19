# 大模型常见概念

v0.10 · 2026-11-19。对应 34 页演示。

P01–P32 为主讲与回顾，P33–P34 为参考资料与演示说明。建议约 70 分钟，另留交流时间。

| 页码 | 内容 | 预计用时 |
| --- | --- | --- |
| P01–P05 | 开场、NLP、语言模型、使用方式与仓库 | 9 分钟 |
| P06–P13 | 分词、生成、模型规格、训练与推理 | 15 分钟 |
| P14–P17 | 训练、对话、提示词和上下文 | 11 分钟 |
| P18–P21 | 召回、重排序、Embedding 和单次工具调用 | 10 分钟 |
| P22–P29 | ReAct、Harness、记忆、上下文压缩、工具执行与任务方法 | 17 分钟 |
| P30–P32 | 其他模型、应用评价指标、概念回顾与可选补讲 | 7 分钟 |

## P01 大模型常见概念

先看真实模型仓库里的文件和分词，再用翻译、会议通知等短例子解释训练、对话和提示词。后面沿一笔报销申请看检索和工具怎样帮助 Agent 做事。最后比较专用模型，讨论应用怎样评测，再根据大家的兴趣补讲。

## P02 人工智能、深度学习与自然语言处理

先从 AI 缩到机器学习，再看到神经网络和多层网络。左边是技术路线，右边是典型语言任务。比如系统读到「周五上午十点在 A305 开会」，可以提取日期、时间和地点。现代大语言模型常用同一个模型处理多类语言任务。

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

## P13 模型的训练和推理

左边是监督微调的一条教学样本。训练时，根据输入和参考译文的已知前缀预测下一个 Token，比较预测与目标 Token 计算损失。优化器据此更新权重。重复这个过程后保存权重，微调也可以保存 LoRA 适配器。右边收到一条新的翻译请求。vLLM 等推理框架在启动时加载所需文件，通过 API 接收输入，组织分词、模型计算和逐步生成，再返回译文。服务可以复用已加载的权重处理后续请求。下一页分别看预训练、监督微调与对齐的训练目标。

来源（不朗读）：

- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [PEFT · LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Transformers · 文本生成策略](https://huggingface.co/docs/transformers/generation_strategies)
- [vLLM · 用 API 提供模型服务](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/)

## P14 预训练、监督微调与对齐

左侧的信号来自原始文本的后续内容。中间的信号来自示范答案，帮助模型学会按任务要求作答。右侧是在学哪种回答更好：标注者给同一问题的候选回答排序，InstructGPT 用排序训练奖励模型，再用评分和 PPO 更新助手。这是偏好对齐的一种做法。对齐是更广的训练目标，监督微调也可以用于对齐。下一页单看对话样本如何教模型扮演助手。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)

## P15 续写模型怎样成为对话助手

【演示】指左边的输入，读出用户要翻译的句子和后面的「助手：」。接下来用下方的参考译文当作训练目标。监督微调用目标回复的 Token 计算损失，更新权重，让模型更能在助手轮次按指令回答。演示用简化角色标记表示输入和参考答案。推理时，聊天模板在用户问题后添加助手的起始标记，模型从那里逐个生成 Token。点第二轮。「语气再正式一点」依赖上一轮译文，因此应用把历史一起传回。Qwen3 的模板用 <|im_start|>assistant 标记开始，用 <|im_end|> 标记结束。

来源（不朗读）：

- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)

## P16 提示词是什么，怎样写清楚？

「帮我整理好」就是一条提示词，但它没说要什么字段，也没交代缺项怎么处理。右边把字段、约束和格式写清楚，示例说明了 JSON 怎么写。本次输入没有地点，用 null 表示。Few-shot 示例随本次请求送入模型。接下来用一次制度问答，看任务指令之外还需要带哪些上下文。

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

用户说电脑连不上网，帮助文档的标题是网络连接故障排查。两段文字分别进同一个检索模型，应用可以用余弦相似度一类的度量找相关文档。例子省略了多数维度，数值为教学示意。前面词表里 Hello 的 9707 是定位词嵌入矩阵的一行所用的编号。接下来用汇率换算看工具调用。

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

【演示】用户目标是提交申请。先走完前三步，第四步切换审批记录，再点提交结果。缺记录时保存草稿并向用户要补件。有记录的分支预设审批系统核验通过，应用调用提交工具，收到教学申请单号 DEMO-018 后才报告已提交。整页为离线模拟，判断栏是讲述用的状态摘要。下一页看看是谁把模型调用、工具执行和回执连成循环。

来源（不朗读）：

- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P24 什么是 Agent Harness？

Anthropic 把 Agent Harness 也叫 scaffold，指让模型能够作为 Agent 工作的系统。Google Cloud 强调它处在运行时，负责控制执行循环。用公式提示分工。模型根据输入给出回复或提出动作。Harness 整理输入、接收输出，在授权范围内执行动作，把实际回执带入下一次调用，并按运行规则继续、暂停或停止。vLLM 等推理框架运行模型并提供推理接口，应用侧的 Harness 可以把这个接口与工具和执行环境连起来。上一页的申请提交可以说明闭环。模型提出调用，程序通过外部系统执行，回执确认成功后才报告申请单号。

下方是典型职责。能力随场景选择。例如高影响操作可以停下来等人工确认，遇到临时故障可以有限重试，长任务可以保存检查点或拆分给子 Agent。可观测性通过调用链串起模型调用和工具执行，帮助定位慢在哪一步、哪里报错、花了多少用量。接下来展开记忆和上下文压缩。

来源（不朗读）：

- [Anthropic · Agent 与 Harness 评测](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
- [Google Cloud · Agent Harness 定义](https://cloud.google.com/discover/agent-harness)
- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [LangChain · Deep Agents 运行能力](https://docs.langchain.com/oss/python/deepagents/overview)
- [OpenTelemetry · 大模型用量和调用链](https://opentelemetry.io/blog/2026/genai-observability/)

## P25 Agent 的记忆怎样起作用？

左侧是会话内连续性，框架也常称它为短期记忆。应用保存或取用同一个会话的历史，挑选本轮需要的部分。右侧是跨会话的长期记忆，Anthropic 的 Agent 记忆文章用这个较窄的含义。新会话可按用户、项目范围和当前任务检索保存的信息。举例时强调「这段」与「以后」的适用范围。可以把用户明确要求保留的偏好写入记忆。若用户后来要求中文优先，应以本次要求为准，并可按用户意愿更新长期偏好。两种做法都依赖应用把信息提供给模型。接下来看看同一个会话越来越长时，应用如何调整每次请求的内容。

来源（不朗读）：

- [Anthropic · Agent 记忆的组成](https://www.anthropic.com/research/components-of-agent-memory)
- [LangGraph · 会话内与跨会话记忆](https://docs.langchain.com/oss/python/concepts/memory)

## P26 上下文压缩怎样腾出空间？

以项目例会通知为例。在多轮讨论和改稿后，应用可按 Token 阈值或历史长度触发压缩。这里选出一批旧消息，归纳出仍有效的时间、地点和字数要求，用摘要代替旧消息进入下一轮。系统指令和最新消息保留原文。运行中还可以裁剪已用过的大段工具结果。重要数字、权限约束和待解问题值得保留。对摘要可能遗漏的内容，可以按需找回原文。记忆面向后续交互的信息复用，上下文压缩面向每次请求的空间。两种机制可以配合使用。下一页看看工具失败、缺输入或预算耗尽时怎么处理。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [Google ADK · 上下文压缩](https://adk.dev/context/compaction/)

## P27 工具执行与停止条件

文档搜索超时属于运行错误，可以按规则重试。缺输入时，助手列明缺项并等待补充。脚本的资源访问受沙箱约束。接下来看看应用怎样接入工具，以及怎样给 Agent 提供可复用的任务方法。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P28 Tool、MCP 与 Skill 的分工

这里的工具负责读构建日志，MCP 是应用接入这项能力时可以使用的协议。Skill 给出排查顺序和报告要求，也可以说明何时调用日志查询工具。下一页看同一个 Skill 怎样按需读入。

来源（不朗读）：

- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P29 Skill 的任务说明与按需加载

先用名称和描述选择排查 Skill，再读说明。碰到不熟悉的错误类型才打开参考文件，写结论时再读报告模板。接下来看看哪些应用能力可以交给专用模型。

来源（不朗读）：

- [Agent Skills · 官方格式](https://agentskills.io/home)

## P30 LLM 之外的常见模型

先从前面见过的 Embedding 和 Reranker 开始，前者给文本算向量，后者给查询和候选打相关性分。OCR 是从图里认字，目标检测是找图里的对象和位置。语音识别与合成的输入输出方向相反。图像生成的输出可以是一张图，Seedance 2.5 则能根据文字和参考素材生成带声音的视频。右边是各任务的代表模型。

来源（不朗读）：

- [BAAI · BGE-M3 模型卡](https://huggingface.co/BAAI/bge-m3)
- [BAAI · bge-reranker-v2-m3 模型卡](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- [PaddleOCR · PP-OCRv5](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html)
- [Ultralytics · YOLO11 视觉模型](https://docs.ultralytics.com/models/yolo11/)
- [OpenAI · Whisper 语音识别](https://github.com/openai/whisper)
- [Kim 等 · VITS 语音合成](https://arxiv.org/abs/2106.06103)
- [Stability AI · Stable Diffusion 3.5](https://stability.ai/news-updates/introducing-stable-diffusion-3-5)
- [ByteDance Seed · Seedance 2.5](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5)

## P31 大模型应用的常见评价指标

按实际任务定义达标条件。知识问答可以分别测是否检索到所需证据、结论是否有证据支持，以及答案是否符合参考答案。工具型 Agent 可以核对工具与参数，并用数据库记录或操作结果验证任务终态。重复运行同一批任务还能观察结果的一致性。评估安全时分别准备应拦截的任务和合法任务，统计越权拦截率与误拦率。

以 vLLM 客户端压测为例，首 Token 时延 TTFT 从发出请求计到收到首个输出 Token。输出超过一个 Token 时，TPOT 等于端到端时延减去 TTFT，再除以输出 Token 数减一。输出吞吐量按观测期的输出 Token 总数除以观测时长。前缀缓存命中率按同一观测期的命中 Token 增量除以查询 Token 增量。P50 是中位数，P95 表示约 95% 的请求在该时延以内。比较时固定并发、输入输出长度分布和缓存冷热。应用层的端到端耗时还包括检索、工具和多次模型请求。

用页上的教学数字说明计量口径。一次问答对应一次请求，100 次中有 98 次正常返回，最终有 87 道题答对。如果这一批总共花了 8.70 元，每个成功任务成本为 0.10 元。总成本包括失败和重试的开销，比较时用同一批任务和一致的计费范围。

来源（不朗读）：

- [vLLM · 压测时延与吞吐量](https://docs.vllm.ai/en/v0.33.0/benchmarking/cli/#understanding-the-latency-metrics)
- [vLLM · 生产指标与缓存计数](https://docs.vllm.ai/en/latest/usage/metrics/)
- [Ragas · RAG 与工具调用指标](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [Anthropic · Agent 与 Harness 评测](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
- [Google ADK · Agent 质量、安全与任务完成](https://adk.dev/evaluate/criteria/)
- [OpenTelemetry · 大模型用量和调用链](https://opentelemetry.io/blog/2026/genai-observability/)

## P32 概念回顾与可选补讲

先顺着模型、应用和 Agent 快速回顾，再请听众从右侧选感兴趣的词。

VLM 怎样理解图片？Diffusion 和 DiT 是怎样的关系？
为什么微调时可以只训练 LoRA 适配器？DPO、GRPO 分别利用什么训练信号？
Temperature 和 Top-p 怎样影响采样？怎样约束模型返回符合 JSON Schema 的结果？
Prefill 处理输入，Decode 逐步生成。KV Cache 保存了什么？投机解码怎样减少生成时的等待？
什么时候把向量检索与关键词检索结合？GraphRAG 如何用图表示实体及其关系？
怎样按任务选模型？多个 Agent 如何协作，什么情况下该请人确认？
怎样用一套固定样题比较两版应用？能否用 Trace 追到其中哪一步出错？
系统怎样识别来源不可信的指令？何处检查身份和工具权限？

来源（不朗读）：

- [vLLM · 推理服务功能](https://docs.vllm.ai/en/latest/features/)
- [PEFT · LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)
- [Transformers · 文本生成策略](https://huggingface.co/docs/transformers/generation_strategies)
- [Microsoft · GraphRAG 项目](https://github.com/microsoft/graphrag)
- [A2A · Agent 间通信协议](https://a2a-protocol.org/latest/)
- [Anthropic · Agent 与 Harness 评测](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
- [OpenTelemetry · 大模型用量和调用链](https://opentelemetry.io/blog/2026/genai-observability/)

## P33 参考资料

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
- [ByteDance Seed · Seedance 2.5](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)
- [vLLM · Chat Completions 请求结构](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- [vLLM · 压测时延与吞吐量](https://docs.vllm.ai/en/v0.33.0/benchmarking/cli/#understanding-the-latency-metrics)
- [vLLM · 生产指标与缓存计数](https://docs.vllm.ai/en/latest/usage/metrics/)
- [Ragas · RAG 与工具调用指标](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [Anthropic · Agent 与 Harness 评测](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Sentence Transformers · 召回与重排](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Google Cloud · Agent Harness 定义](https://cloud.google.com/discover/agent-harness)
- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)

## P34 案例数据与演示口径

整场交互在本地运行。公开的模型规格、代码和物料出处可在逐页讲稿或同版资料说明中查到。
