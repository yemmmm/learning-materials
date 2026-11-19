# 大模型常见概念：一个模型如何成为 AI 助手

v0.4 · 2026-11-18。对应 48 页演示。

P01–P32 为主讲与交流，P33–P48 为附录。以下为 60 分钟讲述安排，另留交流时间。

| 页码 | 内容 | 预计用时 |
| --- | --- | --- |
| P01–P04 | 开场案例与 LLM | 6 分钟 |
| P05–P11 | 模型运行、生成和对话 | 15 分钟 |
| P12–P18 | 应用、上下文与制度依据 | 13 分钟 |
| P19–P26 | 工具、Agent 与运行环境 | 17 分钟 |
| P27–P32 | MCP、Skill、多模态、交付与回顾 | 9 分钟 |

## P01 大模型常见概念

今天沿着差旅报销这个任务看大模型。先认识模型、文件和推理，再看聊天时模型收到了哪些信息，最后看差旅助手如何查制度、做换算并交付结果。

## P02 这笔差旅费可以全额报销吗？

先展示这句没有依据的回答，请大家说出最想核对的地方。把 560 元住宿和 120 新币记下来，结束时会看到同一笔费用的核对说明。接下来先看模型怎样生成文字，再往差旅助手里加入资料、计算与任务控制。

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

## P06 一个模型仓库里的三类文件

Qwen3-8B 的权重分在五个文件里，索引记录每个张量落在哪一片。它的分词器除词表外还用了合并规则和特殊 Token 配置。接下来顺着一次输入走，先看分词器怎么读文本，再看模型怎么用权重继续生成。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)

## P07 文字进入模型前，会变成 Token

【演示】切换中文、英文和代码，看空格、标点怎样参与切分。分词器把句子变成编号序列，模型会用这些编号查到各个 Token 的向量表示。下一页看看模型收到输入后怎样继续生成。

来源（不朗读）：

- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)

## P08 生成一个 Token，再接回上下文

【演示】按顺序点击。第一步追加带前导空格的货币符号，第二步追加 560。用与上一页相同的分词器核对过，两个片段各占一个 Token。请大家指一下第二步可以看到的前文，比最初多了什么。模型在实际生成时利用上下文和权重计算下一步的分布。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)

## P09 训练与推理，发生在不同阶段

训练可以发生在模型提供方，也可以发生在应用团队的微调流程中。推理是我们日常使用模型的阶段。下一页继续看预训练和后训练如何影响模型的对话行为。后面比较提示词、检索和微调时再用到这个区分。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P10 预训练与后训练

回想前面的训练与推理。预训练和后训练使用不同的训练数据和目标。比如 SFT 用问题与示范回答教模型按要求作答。RLHF 会引入人类的回答偏好，附录有具体训练过程。下一页用同一个报销问题对照训练样本和线上输入。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)

## P11 从 SFT 样本到聊天模板

【演示】先找左侧要学习的示范回复，再看右侧第一轮推理的生成起点。点“加入第二轮”，观察原来的回复怎样进入历史，“两晚”因此有了指代。让大家指出模型从哪里接着生成。后面讲上下文时会把这条追问拆成消息。

来源（不朗读）：

- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)

## P12 差旅助手目前还缺什么？

让大家回想开场的回答。编造上限属于幻觉，沿用旧规定则可能是资料已经过期。即使提供了长附件，模型也可能没有利用关键条款。接下来先看应用和模型各负责哪一部分，再逐步弥补这些缺口。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P13 一个最小的差旅问答应用

这页是从模型到应用的桥梁。把聊天产品拆开看，模型是其中的组件，产品还包含状态、输入组织和结果处理。我们先保留最小结构，不急着叫它 Agent。下一节开始，每增加一个新概念，都要能指出它放在这张图的哪里、解决了哪个实际问题。

## P14 提示词工程：目标、示例与格式

先请大家看“整理好”有哪些可能理解。再用右侧的约束处理北京这条记录，对照输出里的 null。Few-shot 把输入输出示例放进本次上下文，SFT 则用示例执行训练。“回答正确奖励 100 美元”可以作为口头插曲，效果依模型与任务而异。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P15 上下文工程：每一步给它什么信息

上下文工程关心模型在哪一步需要哪份信息，以及应用应该怎样获取、更新和压缩这些信息。下一页打开一次请求，看看历史、资料和当前问题放在什么位置。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P16 一次请求怎样用到上下文窗口？

沿着图从左到右看。本轮沿用上一轮的住宿话题，并加入适用条款。服务按 Qwen3-8B 的模板编码消息，输入和生成共用部署服务的上下文窗口。300 是此请求里的生成上限。可以省掉无关的订机票历史。请问这里的两条制度从哪里来？下一页用检索找出它们。

完整请求体

    {
      "model": "Qwen/Qwen3-8B",
      "max_completion_tokens": 300,
      "messages": [
        {"role": "system", "content": "按给定差旅制度回答。"},
        {"role": "user", "content": "一晚花了 560 元，能全额报销吗？"},
        {"role": "assistant", "content": "超出 60 元。全额报销要看事前审批记录。"},
        {"role": "user", "content": "§3.2 上限 500 元/晚。§3.3 超标须事前审批。\n问题：两晚共花了 1,120 元呢？"}
      ]
    }

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [vLLM · Chat Completions 请求结构](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)

## P17 RAG：检索资料，再生成回答

用开卷答题作比喻。先找到相关条款，再根据它回答。资料准备可以提前完成，回答问题时再取片段。下一页直接核对回答和条款的关系。向量、关键词和重排的细节可以在附录展开。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)

## P18 有资料的回答，怎样才算有依据？

这里刻意让模型无法仅凭一条标准就做出全额报销结论。检索到住宿上限还不够，例外条款决定后续问题。一个好回答既说明已知结论，也指出还缺什么证据。制度、金额、版本号都是教学设定。下一节引入工具，让应用获取缺失信息或执行确定的计算。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)

## P19 Function Calling：生成一个调用请求

工具定义相当于告诉模型：有这项能力，它解决什么问题，需要哪些参数。模型并不是自己获得了网络连接，而是输出一个让运行环境解释的请求。应用需要实际调用业务接口，再返回成功、失败或数据。查汇率的日期也不能随意省略，业务任务可能要求发生日、报销日或某个规定日期。

来源（不朗读）：

- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P20 两次工具调用完成一次换算

【演示】四步依次点击。前两步请大家指出谁提出请求、谁执行。第三步观察应用接到第二次调用后返回 636，最后把这两次返回用在回答里。汇率和响应均为预写教学数据。实际业务还需要核对币种、时间、四舍五入以及制度采用的汇率来源。

来源（不朗读）：

- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P21 提示、RAG、微调与工具，各补什么？

这一页把前面容易混淆的方案摆在一起。同样是让模型回答得更好，作用位置不同。资料频繁更新时通常先考虑检索和实时接口；输出习惯不稳可以先改指令和示例，再根据真实任务证据决定是否训练。没有必要一开始就把全部技术都堆进去。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P22 Workflow 与 Agent

两边都处理同一笔差旅费用。左侧顺序和分支由程序指定，右侧的模型根据当前状态决定接下来调用哪个工具。沿右侧的回线看工具结果怎样进入下一次决策。固定流程里也可以有由模型选动作的环节。下一页用有无审批记录演示两种走法。

来源（不朗读）：

- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P23 ReAct · 根据观察决定下一步

【演示】前三步依次找到条款、汇率和两个计算结果。进入“检查审批”，先看未提供记录的情况。助手交付已有的核对结论，并把审批列为待补。再切到已提供记录，下一步变为查询并核验审批。请大家指出是哪条观察改变了动作。“当前判断”是教学用的简短状态说明。

来源（不朗读）：

- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P24 Harness：模型周围的运行与控制系统

Harness 可以理解为让模型在任务中运行的整套外部软件。它和上下文工程有交集，但范围更广，还包括执行环境、事件循环、预算和检查。并不是列上这些能力就自动可靠，具体实现是否有效还需要真实任务验证。记忆和压缩是用户特别关心的部分，下一页展开。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P25 记忆与压缩：长任务怎样接着做？

任务记录不是把全部对话原样存一遍。关键是下一次能知道哪些事实已确认、哪些来源可复查、哪些动作已执行，避免重复工作或把待办当作完成。普通聊天记录、当前上下文、长期记忆的区别在这里汇合。金额合计是六百三十六加五百六十，得到一千一百九十六。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P26 工具执行、沙箱与停止条件

用汇率超时和缺审批来区分两种停止条件。超时可以按规则重试，材料缺失则要记录待补。预算、时限、权限和必要的人类确认由运行环境处理。核对实际工具返回与产物，才能知道哪些动作已经完成。

来源（不朗读）：

- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)

## P27 Tool、MCP、Skill 的分工

可以沿着一个任务描述：Skill 指导按什么步骤做，Agent 选择工具，工具通过直接接口或 MCP 暴露，Harness 负责执行和状态管理。不要说 Skill 天然比 Tool 更强，或者 MCP 自动让工具更聪明。它们解决的问题并不相同。

来源（不朗读）：

- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

## P28 MCP：应用连接外部系统的标准协议

图中客户端处在宿主应用里，并不是语言模型直接运行协议连接。一个服务可以提供多个工具和资源。应用先连接和发现能力，再根据运行方式提供给模型或用户使用。协议支持不意味着所有客户端都实现相同功能或所有服务都提供全部类型。

来源（不朗读）：

- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [MCP · 架构与参与者](https://modelcontextprotocol.io/docs/learn/architecture)

## P29 Skill：把任务说明和材料打包

Skill 可以只有说明文件，也可以包含脚本等资料。它不是一种新模型，也不是必须通过微调安装进去。发现、启用和执行的渐进加载减少了不相关说明占用的上下文。具体能加载和执行哪些内容，取决于兼容的 Agent 客户端和环境。

来源（不朗读）：

- [Agent Skills · 官方格式](https://agentskills.io/home)

## P30 多模态 · 从住宿票据提取字段

让大家指出这张示意票据给后续计算提供了什么。图像、音频和视频都可能是输入，具体要看模型支持的方向。类似的应用还可把语音转成文字，或将结果用语音播报。视频理解和图像生成也各有相应模型。附录保留各类模型和程序的输入输出。

## P31 差旅助手交付的核对说明

把这份说明与开场的回答放在一起看。现在可以追到具体条款、汇率和计算，知道哪些已经核对、哪些仍待补。模型在应用组织的上下文中撰写说明，工具通过直接接口或 MCP 接入，Skill 可以提供报告模板，Harness 保存状态、限制执行并核对结果。

来源（不朗读）：

- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)

## P32 如果助手引用了不存在的条款

请听众先说自己的排查顺序。可以先在适用的制度原文中核实条款，再检查检索记录和模型实际收到的上下文。如果依据已经送达，继续比较回答和原文，看看模型有没有正确使用依据。用这个问题回顾模型、上下文、检索与应用的分工。主讲到这里结束，后面按问题跳到附录。

## P33 “开源模型”开放了哪些东西？

这页只建立辨认意识，不讲许可证法务细节。模型仓库通常有模型卡、配置和权重等，但是否提供完整训练数据、训练代码，要逐项看。Qwen3 这组模型的官方说明给出了 Apache 2.0 许可；其他模型可能采用不同许可，不能从一个模型推及所有模型。

来源（不朗读）：

- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)

## P34 配置、实现代码与权重如何配合

这里展示 Qwen3-8B 的几个配置字段。框架按这些字段确定层数和维度，用模型类定义计算。下一页从框架刚建好的层出发，找出它的参数保存在哪个文件里。

来源（不朗读）：

- [Qwen3-8B · config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)

## P35 权重文件怎样保存模型参数？

配置页的 vocab_size 为 151,936，hidden_size 为 4,096，因此 Qwen3-8B 的输入词嵌入矩阵有 151,936 行、每行 4,096 个数。框架按张量名称查索引，再从分片加载整张矩阵到模型对应的位置。算出输出分数时还会用到另一个张量，也就是 lm_head 权重。下一页看看词嵌入矩阵所用的编号怎样从文本得到。

来源（不朗读）：

- [Qwen3-8B · config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json)
- [Qwen3-8B · 权重分片索引](https://huggingface.co/Qwen/Qwen3-8B/blob/main/model.safetensors.index.json)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)

## P36 分词器文件怎样把文本变成 ID？

这一页对照 Qwen3-8B 的文件。Hello 的编号是 9707，world 前面的空格也属于该 Token，在词表内部用 Ġworld 表示。这两个对话边界同样有专用编号，后面讲聊天模板时能看到它们。前面的交互页使用了另一个分词器，因此同一段英文会看到不同编号。

来源（不朗读）：

- [Qwen3-8B · tokenizer.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json)
- [Qwen3-8B · tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)

## P37 Dense 与 MoE

左图是共享前馈网络，右图为部分激活的专家前馈网络；它们都只是整体 Transformer 中的局部示意。图中的专家不是独立 Agent，也不一定具有可命名的人类专业。Qwen3-235B-A22B 的官方配置实际有 128 个专家、每 Token 激活其中 8 个；本图只用 4 选 2 便于演示。A22B 不能理解为仅需存储 22B 权重。

来源（不朗读）：

- [Qwen3-235B-A22B · 模型卡](https://huggingface.co/Qwen/Qwen3-235B-A22B)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P38 模型名里的数值格式与量化

B 表示十亿，A3B 指每个 Token 计算时约有 30 亿参数参与。下一页会看到官方模型卡里的精确规格。FP16 和 BF16 的字节数相同，BF16 可表示的数值范围更大，FP16 有更多尾数位。量化常用缩放因子把高精度值映射到低位宽，也可能只转换一部分权重。用参数量乘以每个值的位宽，可以快速估算纯权重体积。下载文件还包括量化元数据等，推理需要为 KV Cache 和其他计算数据留空间。

来源（不朗读）：

- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-30B-A3B-FP8 · 量化配置](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)
- [Transformers · 量化与数值格式](https://huggingface.co/docs/transformers/quantization/concept_guide)
- [Lin 等 · AWQ](https://arxiv.org/abs/2306.00978)
- [Frantar 等 · GPTQ](https://arxiv.org/abs/2210.17323)
- [GGML · GGUF 文件格式](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md)

## P39 同一个模型的不同权重版本

先横着读一行，再比较前三行。Qwen3-8B 量化后仍是 8.2B。AWQ 版在配置里写明了 4 位，GGUF 仓库有多个量化文件，这里选 Q4_K_M，官方文件大小是 5.03 GB。后两行展示同一 MoE 模型的 BF16 和 FP8 版本。对照前面的图，区分总参数、每个 Token 的激活规模和权重的数值格式。

来源（不朗读）：

- [Qwen3-8B · 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-8B-AWQ · 量化配置](https://huggingface.co/Qwen/Qwen3-8B-AWQ/blob/main/config.json)
- [Qwen3-8B-GGUF · 权重文件](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main)
- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-30B-A3B-FP8 · 量化配置](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json)

## P40 推理框架把模型文件运行起来

推理框架负责生成，服务层把生成包装成请求和响应。有些项目把两者放在一起。模型运行起来了，为什么用户发出提问时，它会按要求给出回答？接着看训练怎样塑造这种行为。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P41 InstructGPT 的 RLHF 示例

先有监督微调数据和一个经 SFT 的助手，再收集像 A 优于 B 这样的排序。奖励模型学习给 A 更高的分数。训练助手时，让它为新问题生成回答，奖励模型给出标量奖励，然后使用 PPO 之类的算法更新助手。LoRA 可以用于 SFT，回答微调时更新哪些参数的问题。蒸馏关注怎样利用教师模型的信号，例如让小模型学习教师的报销问答能力。

来源（不朗读）：

- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)
- [PEFT · LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)
- [Hinton 等 · 知识蒸馏](https://arxiv.org/abs/1503.02531)

## P42 Token ID 与 Embedding：两种不同的数值

这页专门避免“模型都是数字，所以把 Token 直接拿去算相似度”的误解。Token ID 是离散标识。语言模型内部会把 ID 映射成向量，并进一步计算上下文表示；而检索中常用的 Embedding 模型会将一段文本表示为适合检索比较的向量。二者有关联，但不能随意拿语言模型某个内部层的向量替代经过验证的检索模型。

来源（不朗读）：

- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)
- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)

## P43 Embedding 检索与重排序

先对照这两份文档。交通指南也提到出差报销，但和具体的住宿问题相关性更低。重排是教学示意。选出相关候选后，再核对版本和适用范围。向量的特征通常分布在很多维度上，无法把一维直接读成“住宿”。是否加重排，需要结合真实问题评估效果与额外开销。

来源（不朗读）：

- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)

## P44 常见 AI 模型，在应用中的位置

这页把 RAG 出现过的 Embedding 和 Reranker 放回完整模型地图。它们不需要输出一段回答，任务和输出形式与生成模型不同。计算金额时也可以直接使用普通程序，并不要求每一步都由模型承担。并非所有 AI 模型都符合前面逐个生成文本 Token 的讲法，那个机制明确针对主流自回归文本生成。

来源（不朗读）：

- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)

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

