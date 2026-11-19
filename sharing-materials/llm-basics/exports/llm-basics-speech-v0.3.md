# 大模型常见概念：一个模型如何成为 AI 助手

版本：v0.3。日期：2026-11-18。对应 48 页演示。

P01–P44 为主讲与交流，P45 为成本与评测选讲，P46–P47 为参考资料，P48 为资料与演示说明。建议约 60–70 分钟，另留交流时间。

## P01 大模型常见概念

今天沿着差旅报销这个任务看大模型。先认识模型、文件和推理，再看聊天时模型收到了哪些信息，最后看差旅助手如何查制度、做换算并交付结果。

## P02 一项任务，串起整场分享

先请大家把这个任务记住。一个人完成它会读制度、看票据、查汇率、算金额并整理说明。语言模型本身能生成文字，但是完整任务需要这些额外信息和动作。我们会先用约半场理解模型，再把后面每一项能力加到差旅助手中。整体约六十到七十分钟，规格表和训练名词可以按听众基础快速带过。

## P03 AI、机器学习与深度学习

可以把左边看作常见技术范围的嵌套示意，而不是发展历史或每个领域的严格数学定义。机器学习不只包含神经网络，AI 也不只包含机器学习。现代大语言模型通常位于深度学习这条技术路线中。语言模型的历史比 Transformer 更长，因此不要把语言模型一词直接定义成 Transformer。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P04 语言模型与常见 NLP 任务

过去这些任务经常分别训练专用模型，现在可以用同一个语言模型处理多种任务。接下来看看应用如何获得这种能力，再打开一个模型仓库，看里面有哪些文件。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P05 使用模型的两条路线

从普通用户角度还可以直接使用聊天产品；这里讨论开发应用怎样使用模型，因此聚焦 API 和自行部署。不要把开源模型理解为只能本地使用，也不要把本地理解为一定在笔记本电脑上。自管的云 GPU 同样属于自行部署。

来源（不朗读）：

- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P06 “开源模型”开放了哪些东西？

这页只建立辨认意识，不讲许可证法务细节。模型仓库通常有模型卡、配置和权重等，但是否提供完整训练数据、训练代码，要逐项看。Qwen3 这组模型的官方说明给出了 Apache 2.0 许可；其他模型可能采用不同许可，不能从一个模型推及所有模型。

来源（不朗读）：

- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)

## P07 一个模型仓库里的三类文件

Qwen3-8B 的权重分在五个文件里，索引记录每个张量落在哪一片。它的分词器除词表外还用了合并规则和特殊 Token 配置。接下来顺着一次输入走，先看分词器怎么读文本，再看模型怎么用权重继续生成。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)

## P08 文字进入模型前，会变成 Token

【演示】切换中文、英文和代码，看空格、标点怎样参与切分。分词器把句子变成编号序列，模型会用这些编号查到各个 Token 的向量表示。下一页看看模型收到输入后怎样继续生成。

来源（不朗读）：

- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)

## P09 生成下一步，再把结果接回上下文

【演示】点生成一步和继续生成。新生成的文字会接回前文，作为继续生成的依据。这个计算过程使用了训练得到的权重。下面区分形成权重的训练和使用权重的推理。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P10 训练与推理，发生在不同阶段

训练可以发生在模型提供方，也可以发生在应用团队的微调流程中。推理是我们日常使用模型的阶段。先建立这一差异，后面才能解释为什么 RAG 的资料更新不等于重新训练，为什么长期记忆也通常不写进权重。我们稍后会把训练进一步分成预训练和后训练。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P11 配置、实现代码与权重如何配合

这里展示 Qwen3-8B 的几个配置字段。框架按这些字段确定层数和维度，用模型类定义计算。下一页从框架刚建好的层出发，找出它的参数保存在哪个文件里。

来源（不朗读）：

- [Qwen3-8B · config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)

## P12 权重文件怎样保存模型参数？

配置页的 vocab_size 为 151,936，hidden_size 为 4,096，因此 Qwen3-8B 的输入词嵌入矩阵有 151,936 行、每行 4,096 个数。框架按张量名称查索引，再从分片加载整张矩阵到模型对应的位置。算出输出分数时还会用到另一个张量，也就是 lm_head 权重。下一页看看词嵌入矩阵所用的编号怎样从文本得到。

来源（不朗读）：

- [Qwen3-8B · config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json)
- [Qwen3-8B · 权重分片索引](https://huggingface.co/Qwen/Qwen3-8B/blob/main/model.safetensors.index.json)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)

## P13 分词器文件怎样把文本变成 ID？

这一页对照 Qwen3-8B 的文件。Hello 的编号是 9707，world 前面的空格也属于该 Token，在词表内部用 Ġworld 表示。这两个对话边界同样有专用编号，后面讲聊天模板时能看到它们。前面的交互页使用了另一个分词器，因此同一段英文会看到不同编号。

来源（不朗读）：

- [Qwen3-8B · tokenizer.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)

## P14 模型名里的数值格式与量化

B 表示十亿，A3B 指每个 Token 计算时约有 30 亿参数参与。下一页会看到官方模型卡里的精确规格。FP16 和 BF16 的字节数相同，BF16 可表示的数值范围更大，FP16 有更多尾数位。量化常用缩放因子把高精度值映射到低位宽，也可能只转换一部分权重。用参数量乘以每个值的位宽，可以快速估算纯权重体积。下载文件还包括量化元数据等，推理需要为 KV Cache 和其他计算数据留空间。

来源（不朗读）：

- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-30B-A3B-FP8 · 量化配置](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)
- [Transformers · 量化与数值格式](https://huggingface.co/docs/transformers/quantization/concept_guide)
- [Lin 等 · AWQ](https://arxiv.org/abs/2306.00978)
- [Frantar 等 · GPTQ](https://arxiv.org/abs/2210.17323)
- [GGML · GGUF 文件格式](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md)

## P15 同一个模型的不同权重版本

先横着读一行，再比较前三行。Qwen3-8B 量化后仍是 8.2B。AWQ 版在配置里写明了 4 位，GGUF 仓库有多个量化文件，这里选 Q4_K_M，官方文件大小是 5.03 GB。后两行则展示同一个 MoE 模型的 BF16 和 FP8 版本。它为什么会同时写总参数和激活参数？下一页看 Dense 和 MoE 的计算方式。

来源（不朗读）：

- [Qwen3-8B · 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-8B-AWQ · 量化配置](https://huggingface.co/Qwen/Qwen3-8B-AWQ/blob/main/config.json)
- [Qwen3-8B-GGUF · 权重文件](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main)
- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-30B-A3B-FP8 · 量化配置](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)

## P16 Dense 与 MoE

左图是共享前馈网络，右图为部分激活的专家前馈网络；它们都只是整体 Transformer 中的局部示意。图中的专家不是独立 Agent，也不一定具有可命名的人类专业。Qwen3-235B-A22B 的官方配置实际有 128 个专家、每 Token 激活其中 8 个；本图只用 4 选 2 便于演示。A22B 不能理解为仅需存储 22B 权重。

来源（不朗读）：

- [Qwen3-235B-A22B · 模型卡](https://huggingface.co/Qwen/Qwen3-235B-A22B)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P17 推理框架把模型文件运行起来

推理框架负责生成，服务层把生成包装成请求和响应。有些项目把两者放在一起。模型运行起来了，为什么用户发出提问时，它会按要求给出回答？接着看训练怎样塑造这种行为。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P18 预训练与后训练

回想前面的训练与推理。预训练和后训练都在训练，区别在于数据和训练目标。比如 SFT 给出问题和期望回复，让模型模仿。LoRA 关注微调时改哪些参数，蒸馏关注怎样使用教师的信号，它们可以跟其他训练方法配合。现在仍用报销问题，看看人工比较的结果怎样进入强化学习。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)
- [PEFT · LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)
- [Hinton 等 · 知识蒸馏](https://arxiv.org/abs/1503.02531)

## P19 RLHF：先训练奖励模型，再优化回答

这里讲的是 InstructGPT 的做法。先有一批监督微调数据和一个经 SFT 的助手，再收集像 A 优于 B 这样的排序。奖励模型学习给 A 更高的分数。训练助手时，让它为新问题生成回答，奖励模型根据问题和回答给出标量奖励，接着使用 PPO 这类强化学习算法更新助手。奖励模型给分和助手生成是两项分工。下一页回到同一个问题，对照训练样本与上线时的输入。

来源（不朗读）：

- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)

## P20 从 SFT 样本到聊天模板

【演示】先看左边的训练样本，assistant 位置已有要学习的回复。右边先点“推理：第一轮”，看最后留下 assistant 的起始标记。再点“推理：加入第二轮”，旧的用户消息和助手回复一起成了历史，模型从新的 assistant 起始标记继续。训练和推理会使用匹配模型的聊天模板。接下来看看运行起来的助手还缺哪些信息和能力。

来源（不朗读）：

- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)

## P21 差旅助手目前还缺什么？

举一个幻觉例子：模型给出很像公司制度的“每晚六百元”，甚至附了不存在的条款编号。语气坚定并不是证据。知识过时和幻觉也不是完全同义：旧知识曾经可能正确，但如今不适用。后面的方法分别增加新信息、内部资料和可靠执行能力，并不承诺消除所有错误。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P22 一个最小的差旅问答应用

这页是从模型到应用的桥梁。把聊天产品拆开看，模型是其中的组件，产品还包含状态、输入组织和结果处理。我们先保留最小结构，不急着叫它 Agent。下一节开始，每增加一个新概念，都要能指出它放在这张图的哪里、解决了哪个实际问题。

## P23 提示词工程：目标、示例与格式

提示词工程不是背神奇咒语。奖励金额的说法曾经很流行，但不能用它定义这个领域，也不能在没有对照实验时宣称有效。Few-shot 的价值是让模型看到任务的判定和输出形式。对比 SFT：两者都可以有示例，Few-shot 把示例放进本次上下文，SFT 用示例执行训练。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P24 上下文工程：每一步给它什么信息

上下文工程关心模型在哪一步需要哪份信息，以及应用应该怎样获取、更新和压缩这些信息。下一页打开一次请求，看看历史、资料和当前问题放在什么位置。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P25 一次请求怎样用到上下文窗口？

这是一个 vLLM 的 Chat Completions 请求体。两条历史消息让模型知道用户在追问住宿，最后一条 user 消息把本轮问题和适用条款放在一起。服务按 Qwen3-8B 的聊天模板编码消息，输入长度和可生成的长度受服务配置的上下文窗口约束。若此前对话还谈了订机票，应用可以省掉那部分，把空间留给住宿问题及依据。这里条款已经放进请求，下一页讲应用怎样用 RAG 找出这些条款。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [vLLM · Chat Completions 请求结构](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)

## P26 RAG：检索资料，再生成回答

可以用开卷答题作直观比喻：先找到相关页，再根据它回答。准备资料和回答问题是两个阶段，前者不必每次用户提问都重做。Embedding 是常见的索引工具，但 RAG 的核心是检索与生成结合，不是必须有向量数据库。这里介绍工程中常见模式，原始论文有更具体的模型训练方案。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)

## P27 Token ID 与 Embedding：两种不同的数值

这页专门避免“模型都是数字，所以把 Token 直接拿去算相似度”的误解。Token ID 是离散标识。语言模型内部会把 ID 映射成向量，并进一步计算上下文表示；而检索中常用的 Embedding 模型会将一段文本表示为适合检索比较的向量。二者有关联，但不能随意拿语言模型某个内部层的向量替代经过验证的检索模型。

来源（不朗读）：

- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)
- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)

## P28 Embedding 检索与重排序

不要把每个向量维度想象成一个能读懂的标签，例如第一维固定代表住宿。大多数表示是分布式的，维度通常也远不止二维。为了不制造误解，这里不用伪装成真实计算结果的散点图，而是展示检索目标。Reranker 也不是所有系统都必需，它可以在候选集上改善排序，增加相应开销。

来源（不朗读）：

- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)

## P29 有资料的回答，怎样才算有依据？

这里刻意让模型无法仅凭一条标准就做出全额报销结论。检索到住宿上限还不够，例外条款决定后续问题。一个好回答既说明已知结论，也指出还缺什么证据。制度、金额、版本号都是教学设定。下一节引入工具，让应用获取缺失信息或执行确定的计算。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)

## P30 Function Calling：生成一个调用请求

工具定义相当于告诉模型：有这项能力，它解决什么问题，需要哪些参数。模型并不是自己获得了网络连接，而是输出一个让运行环境解释的请求。应用需要实际调用业务接口，再返回成功、失败或数据。查汇率的日期也不能随意省略，业务任务可能要求发生日、报销日或某个规定日期。

来源（不朗读）：

- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P31 一次工具调用的完整往返

【演示】四步依次点击。前两步让大家辨认模型输出和运行环境执行，第三步说明工具返回后模型可以继续请求计算。最后回复使用查询结果和计算结果。汇率与响应都是预写教学数据，界面不会真的访问查询服务。业务里还需要处理币种、时间、四舍五入以及制度采用的汇率来源。

来源（不朗读）：

- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P32 提示、RAG、微调与工具，各补什么？

这一页把前面容易混淆的方案摆在一起。同样是让模型回答得更好，作用位置不同。资料频繁更新时通常先考虑检索和实时接口；输出习惯不稳可以先改指令和示例，再根据真实任务证据决定是否训练。没有必要一开始就把全部技术都堆进去。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P33 Workflow 与 Agent

这里采用 Anthropic 给出的实用架构区分，行业对 Agent 的用法并不完全一致。重要的是看控制方式，而不是产品是否给自己贴了 Agent 标签。固定流程也能调用模型和多个工具，Agent 也可能只在一个流程环节里动态工作。先解决实际需求，再增加自主性。

来源（不朗读）：

- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P34 ReAct：判断、行动、观察，再继续

【演示】四步分别获取制度、汇率、计算和交付。最终知道合计金额，也知道超标住宿需要审批，因此报告中要保留缺失审批的提示。这里的“当前判断”只是为了讲解系统状态而写的简短理由，不声称揭示真实模型的内部推理。原始 ReAct 研究强调推理轨迹和行动交替，现代工具调用系统可以采用不同实现。

来源（不朗读）：

- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P35 Harness：模型周围的运行与控制系统

Harness 可以理解为让模型在任务中运行的整套外部软件。它和上下文工程有交集，但范围更广，还包括执行环境、事件循环、预算和检查。并不是列上这些能力就自动可靠，具体实现是否有效还需要真实任务验证。记忆和压缩是用户特别关心的部分，下一页展开。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P36 记忆与压缩：长任务怎样接着做？

任务记录不是把全部对话原样存一遍。关键是下一次能知道哪些事实已确认、哪些来源可复查、哪些动作已执行，避免重复工作或把待办当作完成。普通聊天记录、当前上下文、长期记忆的区别在这里汇合。金额合计是六百三十六加五百六十，得到一千一百九十六。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P37 工具执行、沙箱与停止条件

这页不展开安全架构，只解释常见产品能力的用途。用户问一个复杂问题，背后可能有很多次模型请求和工具执行。预算和停止条件属于运行控制，错误处理把异常变成下一轮决策的信息。动作是否完成，要看真实工具状态和产物，不能只看自然语言的完成声明。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P38 Tool、MCP、Skill 的分工

可以沿着一个任务描述：Skill 指导按什么步骤做，Agent 选择工具，工具通过直接接口或 MCP 暴露，Harness 负责执行和状态管理。不要说 Skill 天然比 Tool 更强，或者 MCP 自动让工具更聪明。它们解决的问题并不相同。

来源（不朗读）：

- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P39 MCP：应用连接外部系统的标准协议

图中客户端处在宿主应用里，并不是语言模型直接运行协议连接。一个服务可以提供多个工具和资源。应用先连接和发现能力，再根据运行方式提供给模型或用户使用。协议支持不意味着所有客户端都实现相同功能或所有服务都提供全部类型。

来源（不朗读）：

- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [MCP · 架构与参与者](https://modelcontextprotocol.io/docs/learn/architecture)

## P40 Skill：把任务说明和材料打包

Skill 可以只有说明文件，也可以包含脚本等资料。它不是一种新模型，也不是必须通过微调安装进去。发现、启用和执行的渐进加载减少了不相关说明占用的上下文。具体能加载和执行哪些内容，取决于兼容的 Agent 客户端和环境。

来源（不朗读）：

- [Agent Skills · 官方格式](https://agentskills.io/home)

## P41 多模态：输入输出可以超出文字

前面一直用文本模型建立基本概念，现在扩展输入输出。图片如何编码到模型内部有不同架构，不要简单说所有内容都用同一种文本 Token。对业务而言先区分接收什么、产生什么，再看需不需要组合 OCR、视觉模型、语音模型和工具。

## P42 常见 AI 模型，在应用中的位置

这页把 RAG 出现过的 Embedding 和 Reranker 放回完整模型地图。它们不需要输出一段回答，任务和输出形式与生成模型不同。计算金额时也可以直接使用普通程序，并不要求每一步都由模型承担。并非所有 AI 模型都符合前面逐个生成文本 Token 的讲法，那个机制明确针对主流自回归文本生成。

来源（不朗读）：

- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)

## P43 差旅助手的完整组成

回到开场的问题。一个完整任务并非模型输出一段文字就自然结束，还涉及资料、执行和检查。最终报告要写明一千一百九十六元是教学费用合计，不能直接把它当成已批准报销金额，因为住宿超标的审批还缺失。这也是为什么我们要把总金额、制度结论和业务完成分别判断。

来源（不朗读）：

- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)

## P44 把名词放回它解决的问题

可以用不存在的制度条款这个问题做收尾互动。可能没有提供资料，可能检索漏掉了正确条款，可能文档版本不适用，也可能模型没有正确使用已提供的资料。不要一上来就认定必须换模型、微调或加一个 Agent。请听众用这张表定位问题，再回到具体证据。

## P45 一次用户任务的成本与效果

这一页按时间选讲，避免打断主线。没有加入易过期的供应商价格。对于 Agent 应用，单次 Token 价格只是成本的一部分，一项任务有多少次调用、工具多慢、是否反复失败都很重要。评测不要只看语气顺不顺，金额和制度引用要有明确标准。

来源（不朗读）：

- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P46 参考资料：模型、文件与训练

HTML 中可直接点击资料链接。各主题页的讲稿也附有对应来源。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Qwen3-8B · config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json)
- [Qwen3-8B · 权重分片索引](https://huggingface.co/Qwen/Qwen3-8B/blob/main/model.safetensors.index.json)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)
- [Qwen3-8B · tokenizer.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)
- [Qwen3-8B · 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-8B-AWQ · 量化配置](https://huggingface.co/Qwen/Qwen3-8B-AWQ/blob/main/config.json)
- [Qwen3-8B-GGUF · 权重文件](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main)
- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-30B-A3B-FP8 · 量化配置](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)
- [Qwen3-235B-A22B · 模型卡](https://huggingface.co/Qwen/Qwen3-235B-A22B)
- [Transformers · 量化与数值格式](https://huggingface.co/docs/transformers/quantization/concept_guide)
- [Lin 等 · AWQ](https://arxiv.org/abs/2306.00978)
- [Frantar 等 · GPTQ](https://arxiv.org/abs/2210.17323)
- [GGML · GGUF 文件格式](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)
- [PEFT · LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)
- [Hinton 等 · 知识蒸馏](https://arxiv.org/abs/1503.02531)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)

## P47 参考资料：检索、工具与 Agent

HTML 中可直接点击资料链接。各主题页的讲稿也附有对应来源。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [vLLM · Chat Completions 请求结构](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)
- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)

## P48 资料与演示说明

本页集中记录内部分享、案例数据、互动和图文的来源。前两页有可点击的参考链接。

