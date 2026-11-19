# 大模型常见概念：一个模型如何成为 AI 助手

v0.5 · 2026-11-19。对应 45 页演示。

P01–P43 为主讲与回顾，P44–P45 为参考资料与演示说明。建议约 70 分钟，另留交流时间。

| 页码 | 内容 | 预计用时 |
| --- | --- | --- |
| P01–P07 | 开场、模型能力、使用方式与文件 | 9 分钟 |
| P08–P16 | 分词、生成、加载、规格与推理服务 | 15 分钟 |
| P17–P24 | 训练、对话、最小应用和上下文 | 13 分钟 |
| P25–P30 | 检索证据与外部工具 | 11 分钟 |
| P31–P38 | Agent、运行环境与任务方法 | 13 分钟 |
| P39–P43 | 多模态、交付、评测与回顾 | 8 分钟 |

## P01 大模型常见概念

今天用一笔报销任务理解常见的大模型概念。先看模型的文件怎样支撑生成和部署，再看模型接收到的对话与资料。最后沿着工具执行的结果，看固定流程和 Agent 分别怎样推进任务。整场用同一笔费用收尾。

## P02 这笔差旅费可以全额报销吗？

先请大家找出需要核实的说法。这个回答看起来很顺，但它没有解释 600 元的来源，也没有处理外币和审批。记住 560 元和 120 新币，后面用相同材料交付一份核对说明。现在先定位给出这句回答的模型。

## P03 AI、机器学习与大语言模型

左边从大范围到具体技术路线，AI 还包括规则、搜索等方法，机器学习也有其他算法。我们主要讨论现代语言模型的文本生成机制。下一页从技术换到工作对象，看同一个语言模型能处理哪些语言任务。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P04 语言模型能处理哪些文本任务？

横着看信息抽取这一行。程序交给模型一段文字并要求固定字段，处理的结果可以给下一步使用。这和直接问模型一个开放问题是不同的任务形式。开发者要用到这些能力，通常有两种接入路线。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P05 托管 API 与自行部署

对普通用户，聊天网页是另一种入口。对开发应用的人，重点是责任如何分配。自行部署的设备可以是自己的工作站，也可以是自管的云 GPU。选择自行部署时，接下来要查模型公开了哪些材料。

来源（不朗读）：

- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P06 开放权重、训练资料与使用许可

口头说“开源模型”时，可能有人专指权重开放。看实际交付会更清楚。权重用于运行，训练信息关系到复现，使用和再分发需要核对许可。本例的模型仓库里已经有运行所需的主要文件，下一页打开看看。

来源（不朗读）：

- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)
- [Qwen3-8B · 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)

## P07 模型仓库的三类文件

这不是仓库的完整列表。权重有五个分片，表里只列一个。配置、权重、分词器是理解加载过程的三个入口，具体文件名和组合会随模型变化。先看分词器怎样给一段文字编码，随后再回头看加载时配置和权重如何配合。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)

## P08 Token 与 Token ID

【演示】依次切换中文、英文和代码。英文示例中空格跟着 world 进入一个 Token，代码中的标点有自己的切法。Token 可能是词、词的一部分、标点，或字符的部分字节。编号序列交给模型后，就可以演示怎样计算下一步。

来源（不朗读）：

- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)

## P09 逐个 Token 生成文本

【演示】点第一个 Token，再点第二个。请大家指一下追加 560 时，模型比最初多看到了什么。实际生成时，候选分布由整个当前输入与已加载的权重共同计算。下一页把“权重从哪里来”和“现在怎样用权重”分开。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)

## P10 训练与推理

模型供应方和应用团队都可能做训练。LoRA 这类方法回答的是微调时更新哪些参数。日常调用 API 时做的是推理，当前输入会影响输出。下一页从推理框架的角度，看配置和权重怎样组成一个可运行的模型。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [PEFT · LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)

## P11 配置和权重怎样装进模型？

先指配置里的类型和两个维度，再指索引里的词嵌入名称。框架用模型类定义计算，按名称从权重文件加载数值。Token ID 恰好对应输入词嵌入矩阵的一行。要让这个匹配成立，应用得使用该模型对应的分词器。

来源（不朗读）：

- [Qwen3-8B · config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json)
- [Qwen3-8B · 权重分片索引](https://huggingface.co/Qwen/Qwen3-8B/blob/main/model.safetensors.index.json)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)

## P12 同一段文字在不同分词器中的编号

比较 Hello 的 9906 和 9707，即使切分看起来一样，编号也依赖词表。后面讲聊天模板时，这两个对话边界会再次出现。现在输入已经能变成模型所需的编号，接下来读模型规格，关注参与计算的参数规模。

来源（不朗读）：

- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)
- [Qwen3-8B · tokenizer.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)

## P13 Dense 与 MoE 的前馈层

左图的 FFN 是前馈网络。右图中的专家是子网络，路由按 Token 选中一部分。四选二是教学示意，Qwen3-235B-A22B 的模型卡列的是 128 个专家、每 Token 激活其中 8 个。读模型名时，先分别找总参数量和激活参数量。

来源（不朗读）：

- [Qwen3-235B-A22B · 模型卡](https://huggingface.co/Qwen/Qwen3-235B-A22B)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P14 模型名里的参数量与数值格式

B 表示十亿，型号写的是约数。官方模型卡给出总参数 30.5B、激活参数 3.3B。FP16 与 BF16 虽然位宽相同，可表示范围和精度的取舍不同。这页用统一位宽粗估纯权重的十进制 GB。下一页把这个估算与具体发布文件对照。

来源（不朗读）：

- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-30B-A3B-FP8 · 量化配置](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)
- [Transformers · 量化与数值格式](https://huggingface.co/docs/transformers/quantization/concept_guide)

## P15 同一模型的原始权重与量化版本

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

## P16 推理框架与服务接口

第一条是启动服务时做的事，第二条随请求反复发生。自部署应用照样可以用 API 请求模型服务。到这里模型能运行了，接下来看训练怎样让续写模型按用户要求回答。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)
- [vLLM · Chat Completions 请求结构](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)

## P17 预训练与监督微调

左侧演示“继续写”，右侧演示“按任务要求回答”。两边都在训练，训练目标和给定的样本不同。后训练还包括基于偏好的方法。下一页保留同一个报销问题，请人比较两个候选回答。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Hinton 等 · 知识蒸馏](https://arxiv.org/abs/1503.02531)

## P18 RLHF 怎样使用人类偏好？

这里示范的是 InstructGPT 的做法。监督微调先给出一个能按指令作答的助手。人工排序得到偏好数据，奖励模型学习打分，接着给助手的新回答评分，并用 PPO 等强化学习步骤更新助手。线上使用时输入的消息怎样对应训练时见过的角色和回复？接下来打开一个对话请求。

来源（不朗读）：

- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)

## P19 聊天模板与多轮对话

【演示】先指左侧 assistant 的示范回复，再指右侧第一轮推理的生成起点。点“加入第二轮”，观察原来的回复怎样进入历史。边界符号与前面分词器页相呼应。这是简化的 ChatML 风格示例，实际服务使用部署模型匹配的模板。现在回到开场，看看一次自然的对话仍可能漏掉哪些核对依据。

来源（不朗读）：

- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)

## P20 差旅回答中的三个核对缺口

编造制度上限是幻觉的一种表现。训练知识过时、模型看不到内部材料、算错金额，都是实际使用时要区分的问题。后续出现的检索和工具会补齐这些信息。先画出最小应用，确认问题和已提供的材料怎样到达模型。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P21 一个最小的差旅问答应用

这个最小版本没有自动查制度，用户把条款给了应用。界面、会话、资料和校验由应用管理，模型处理的是实际发送给它的输入。在第二步，任务要求怎样写，决定了回答能否被程序直接检查。

## P22 提示词里的目标、约束与示例

请大家先说左边的“整理好”可能有几种理解，再看右边怎样指定缺失值和输出字段。Few-shot 这些示例会和指令一起进入本次上下文。SFT 则以样本为训练输入，调整参数。应用要回答整个报销问题，还需要挑选历史和证据。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)

## P23 上下文工程要选择哪些信息？

上一页的提示词仍是这里的任务指令。除此之外，应用要决定什么时候带历史、条款或者工具结果。比如本轮只讨论住宿，可以舍去无关的机票记录。下一页把这些选择放进一条具体请求，并看看窗口大小的影响。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P24 一次对话请求的上下文窗口

沿图从左到右看，前三块编码为输入 Token。请求参数 max_completion_tokens 为 300，这是本次生成的上限。窗口内既要留出输入，也要有生成空间。这里明确两晚各花了 560 元，才可以逐晚核对标准。请求中的原始条款从哪里找？下一节介绍检索。

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

## P25 RAG 的资料准备和回答流程

顺序是先备好可检索的资料，再在收到住宿问题时选择适用片段。索引支持的检索方式可以不同，向量数据库只是可能的实现之一。下一页先区分前面看到的 Token ID 和这里用于检索的向量。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)

## P26 Token ID 与 Embedding 向量

前面同一个 Hello 在两套词表里的整数不同，这里利用它说明 ID 的作用。整数大小和语义远近没有对应关系。检索模型的输出通常有很多维，按模型支持的方式比较问题与文档向量。下一页让召回和重排各做一步。

来源（不朗读）：

- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)
- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)

## P27 检索候选与重排

召回适合在大量文档中找一批候选，重排再逐个比较问题与候选片段。这里没有实时评分，排序是为了讲清过程。找到住宿条款后，先看原文是否支持要写入回答的事实。

来源（不朗读）：

- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)

## P28 制度条款怎样支持报销结论？

请大家指一下这两个结论分别来自哪条规定。模型拿到相关片段后仍可能解释错误，引用链接也要与具体主张相对应。住宿能核对到这个程度，还有一笔 120 新币，需要查本次适用的汇率并计算。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)

## P29 Function Calling 的调用请求

指一下左边的参数定义，再看右边的参数是怎样从一笔外币费用得到的。此时只看到模型提出的请求。查询和计算是后面由应用完成的两次往返，下一页沿着调用结果看下去。

来源（不朗读）：

- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P30 两次工具调用完成一次换算

【演示】依次点击四步。请大家指出谁提出查询、谁实际执行，以及输出中的 636 来自哪里。教学数据已预写。应用可以把这个顺序固定下来，也可以在完成换算后，根据已经取得的结果选择要查的下一项。

来源（不朗读）：

- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P31 Workflow 与 Agent 的决策分工

两边都能处理这笔费用，差别是主要路径由谁决定。左侧由程序定义审批条件与分支。右侧先看结果再判断缺什么，应用按授权执行它选的动作。下一页只改变最后一份材料，看选择怎样改变。

来源（不朗读）：

- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P32 ReAct 的行动与观察

【演示】先走完前三步，第四步切换有无审批记录。材料缺失时，今天的范围内可以给出待补说明。用户已提供记录时，还要去审批系统核验。当前判断是教学用的状态摘要。ReAct 是交替使用推理与动作的一种模式。接下来把模型之外负责执行、保存状态和停止的东西画出来。

来源（不朗读）：

- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P33 Harness 怎样运行 Agent？

ReAct 页展示模型根据观察选了哪个动作，这里换成运行软件的视角。Harness 管每轮模型请求、执行环境和结果记录，具体边界随实现变化。工具结果到手后，先保存再检查是否需要继续。长任务换到新上下文时，要知道从哪里接起。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P34 长任务的记忆与上下文压缩

先请大家指出下一轮还要做哪一件事。每次恢复不必逐字带回所有历史，也不能把已确认和待办混淆。这里的记忆依赖模型外的存储和取回，压缩是管理窗口中的信息量。恢复之后，如果仍没有审批，运行环境还要决定这轮在哪里停。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P35 工具执行与停止条件

汇率超时属于运行错误，可以按规则重试。没提供审批是业务缺件，重复问同一个工具不一定有用。沙箱限制执行位置和资源，避免程序越过被允许的范围。工具如何接到应用、做事方法如何复用，就是下一组概念。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P36 Tool、MCP 与 Skill 的分工

这三个词描述的是不同问题。在这笔报销里，Skill 的规则帮助决定什么时候要看审批。应用可以通过 MCP 接到审批系统，真正执行查询的是一个工具。先从连接关系看 MCP 的几个参与者。

来源（不朗读）：

- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P37 MCP 的 Host、Client 与 Server

沿上面一条连接看。宿主应用内的文档客户端发现服务端的制度搜索工具，应用可以把工具说明提供给模型。业务客户端另连一个 Server。具体能用哪些能力，取决于服务提供的能力和应用权限。连通系统后，还要决定报销核对按哪套步骤做。

来源（不朗读）：

- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [MCP · 架构与参与者](https://modelcontextprotocol.io/docs/learn/architecture)

## P38 Skill 的任务说明与按需加载

这个示例的 Skill 只要求在交付阶段读模板，到核对具体地区时才看对应资料。按需加载可以减少无关说明占用上下文。它与前面训练更新参数是不同的操作。说到开始核对，有时用户提供的金额在票据图片上，接下来看应用怎样取得原始字段。

来源（不朗读）：

- [Agent Skills · 官方格式](https://agentskills.io/home)

## P39 多模态怎样读出票据字段？

左边是示意票据，右边是后续程序要用的四个字段。本页没有在线识别。可以用视觉语言模型直接读取，也可以由 OCR 技术识别文字再解析。语音转写或播报会用到其他能力。下一页把这些模型放回完整应用。

## P40 差旅任务中各类模型的分工

沿着这条链路看输入和输出。Embedding 与重排是生成前的检索环节。计算和系统查询交给程序。文本生成模型擅长把这些内容组织成一份说明。图片和视频生成也可以用各自的模型，需看输入输出能力。最后展示这笔费用实际交出的一页说明。

来源（不朗读）：

- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P41 差旅助手交付的核对说明

对照开场那句“可以全额报销”。现在已经核对金额、换算和适用条款。这里的一千一百九十六是费用合计，是否能全额报销仍须核验审批。让大家指出每一项数字的出处。下一页把同样的核对做成应用评测标准。

## P42 整项任务的效果与成本

把开场的初答与最终说明放进同一套检查。换算错、条款找不到、审批被当作完成，都要分别计入。带工具的 Agent 经常执行多次模型请求，评估整项任务比只比较一轮 Token 价格更接近真实使用。最后用一条找不到的制度规定练习定位问题。

来源（不朗读）：

- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P43 助手引用了不存在的条款，怎么排查？

先独立查看适用的制度原文，再沿检索记录和请求定位丢失或错误使用的证据。任务要求不清时可以改提示词，缺外部资料时可以改检索或接口，计算缺口交给工具。如果携带正确依据后仍反复出现稳定的任务行为问题，再评估是否需要训练。到这里结束主讲，余下两页供会后查阅。

## P44 参考资料

本页供会后找资料。按主题跳到相应页可查看该页的模型配置、论文或协议说明。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)
- [Transformers · 量化与数值格式](https://huggingface.co/docs/transformers/quantization/concept_guide)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)
- [vLLM · Chat Completions 请求结构](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)

## P45 案例数据与演示口径

整场交互在本地运行。公开的模型规格、代码和物料出处可在逐页讲稿或同版资料说明中查到。
