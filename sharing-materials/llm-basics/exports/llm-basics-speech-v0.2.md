# 大模型常见概念：一个模型如何成为 AI 助手

版本：v0.2。日期：2026-11-18。对应 47 页演示。

P01–P44 为主讲与交流；P45 为按需展开的成本与评测；P46–P47 为参考资料。建议约 60–70 分钟，模型规格与训练名词可快速带过，另留交流时间。具体时间按排练调整。

制度、汇率、金额与工具响应均为教学示例；不连接模型或业务 API。分词是 tiktoken / cl100k_base 的实际结果；其他交互是预写演示。文件清单摘录自官方仓库，已标注非网页截图。插图由 AI 生成。

## P01 大模型常见概念

今天不要求大家记住算法公式。我们要建立一张地图：看到模型名字时能读出规格，聊天时知道模型拿到了什么信息，看到 Agent 产品时能辨认它如何获取资料和执行动作。后半场一直沿用差旅助手这个例子，把新概念接到已经理解的系统上。封面插图只是工作台的比喻，不是网络结构示意。

## P02 一项任务，串起整场分享

先请大家把这个任务记住。一个人完成它会读制度、看票据、查汇率、算金额并整理说明。语言模型本身能生成文字，但是完整任务需要这些额外信息和动作。我们会先用约半场理解模型，再把后面每一项能力加到差旅助手中。整体约六十到七十分钟，规格表和训练名词可以按听众基础快速带过。

## P03 AI、机器学习与深度学习

可以把左边看作常见技术范围的嵌套示意，而不是发展历史或每个领域的严格数学定义。机器学习不只包含神经网络，AI 也不只包含机器学习。现代大语言模型通常位于深度学习这条技术路线中。语言模型的历史比 Transformer 更长，因此不要把语言模型一词直接定义成 Transformer。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P04 语言模型与常见 NLP 任务

过去这些任务经常分别训练专用模型，现在可以把任务描述写进输入，让一个语言模型处理多种任务。这不代表专用模型失去价值。下一页我们拆开文本进入模型前的第一步。大模型中的“大”没有统一的参数门槛，通常涉及参数、训练数据和计算规模，不能只凭某个 B 数字做严格划分。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P05 文字进入模型前，会变成 Token

【演示】切换中文、英文和代码，看空格、标点怎样参与切分。这里使用指定分词器的实际结果，不代表 Qwen 的分词结果。Token 可以理解为模型使用的文本单位，ID 是在词表里的编号。后面讲 Embedding 时会再次用到这一点：整数编号和特征向量是不同对象。

来源（不朗读）：

- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)

## P06 生成下一步，再把结果接回上下文

【演示】点生成一步和继续生成，说明输出会重新成为后续输入的一部分。示意句子不是实时模型输出。这里避免把模型讲成简单查找下一个词的词典，它会通过多层计算利用上下文。也不要从这一机制直接推导它只能抄写或必然理解，实际任务能力需要看训练和评测。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P07 训练与推理，发生在不同阶段

训练可以发生在模型提供方，也可以发生在应用团队的微调流程中。推理是我们日常使用模型的阶段。先建立这一差异，后面才能解释为什么 RAG 的资料更新不等于重新训练，为什么长期记忆也通常不写进权重。我们稍后会把训练进一步分成预训练和后训练。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)

## P08 使用模型的两条路线

从普通用户角度还可以直接使用聊天产品；这里讨论开发应用怎样使用模型，因此聚焦 API 和自行部署。不要把开源模型理解为只能本地使用，也不要把本地理解为一定在笔记本电脑上。自管的云 GPU 同样属于自行部署。

来源（不朗读）：

- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P09 “开源模型”开放了哪些东西？

这页只建立辨认意识，不讲许可证法务细节。模型仓库通常有模型卡、配置和权重等，但是否提供完整训练数据、训练代码，要逐项看。Qwen3 这组模型的官方说明给出了 Apache 2.0 许可；其他模型可能采用不同许可，不能从一个模型推及所有模型。

来源（不朗读）：

- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)

## P10 一个模型仓库里的三类文件

请直接观察仓库：权重分成五个文件，不是五个独立模型；index.json 记录张量落在哪个分片中。分词器也不是一个 vocab.json 就必然完整，它还可能依赖合并规则、特殊 Token 设置等。讲稿中的链接可以打开原仓库。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)

## P11 配置、实现代码与权重如何配合

这里展示真实配置的节选，省略了其他字段。它能告诉框架这个模型有多少层、每层维度多大，但仅凭这些数字并没有定义全部运算逻辑。权重中的张量名和形状也能反映部分结构信息，所以不能把权重说成毫无结构的信息；只是不能把它直接等同于完整网络程序。

来源（不朗读）：

- [Qwen3-8B · config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)

## P12 模型名字里的信息

Qwen3-30B-A3B 的模型卡列出约 30.5B 总参数和约 3.3B 激活参数。名字不一定是精确计数。模型版本也不只是参数量，可能同时包含训练阶段、精度、量化方式、用途和发布修订。GGUF 是一种文件格式，它可以承载不同精度或量化类型，不能只看后缀就推断位宽。

来源（不朗读）：

- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P13 代表性公开模型规格

本表选择有清晰公开资料、便于比较的代表性型号，不试图罗列今天所有热门模型。Dense 不用表里的斜线规则报告激活数，以免把不同统计口径混起来。DeepSeek 模型卡还提示权重可能包含额外的预测模块，下载体积与主干参数口径需要分别看。闭源 API 的未公开参数不要估算成事实。

来源（不朗读）：

- [Qwen3-8B · 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-32B · 模型卡](https://huggingface.co/Qwen/Qwen3-32B)
- [Llama 3.3 70B Instruct · 模型卡](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct)
- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-235B-A22B · 模型卡](https://huggingface.co/Qwen/Qwen3-235B-A22B)
- [DeepSeek-V3 · 模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V3)

## P14 Dense 与 MoE

左图是共享前馈网络，右图为部分激活的专家前馈网络；它们都只是整体 Transformer 中的局部示意。图中的专家不是独立 Agent，也不一定具有可命名的人类专业。Qwen3-235B-A22B 的官方配置实际有 128 个专家、每 Token 激活其中 8 个；本图只用 4 选 2 便于演示。A22B 不能理解为仅需存储 22B 权重。

来源（不朗读）：

- [Qwen3-235B-A22B · 模型卡](https://huggingface.co/Qwen/Qwen3-235B-A22B)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P15 量化与蒸馏：怎样降低使用门槛

权重估算采用十进制 GB，只用于理解参数数目与位宽的关系，不能直接给出显存采购结论。实际峰值内存取决于上下文、并发与实现。量化是否更快也取决于内核和设备支持。蒸馏通常更小，但定义重点是使用教师提供的信号，不是必须缩小参数量。

来源（不朗读）：

- [Transformers · 量化](https://huggingface.co/docs/transformers/main/en/quantization/overview)
- [Hinton 等 · 知识蒸馏](https://arxiv.org/abs/1503.02531)

## P16 SFT、RLHF 与 LoRA

先让大家认识缩写，下一节用训练样本具体讲 SFT 为什么能把续写模型变成对话助手。RLHF 是常见路线，不要说所有现代模型只靠人工逐条评分，也不要求把训练流程写成固定流水线。LoRA 不是知识库，也不是与 SFT 对立的另一类任务目标。

来源（不朗读）：

- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)
- [PEFT · LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)

## P17 推理框架把模型文件运行起来

不要把模型文件本身叫成服务。推理引擎承担计算，服务层将它包装成请求响应接口，有些项目把两者集成在一起。这里只建立位置感，不要求听众记住安装命令。Qwen 官方说明中提供了多个框架的加载和服务示例，实际部署仍需核对版本兼容性。

来源（不朗读）：

- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)

## P18 预训练与后训练

回到前面留下的问题：为什么一个续写模型会成为助手？并不是突然有了另一个完全不同的生成机制，而是训练改变了它在给定输入下倾向生成什么。预训练和后训练都能影响能力与知识，不要把预训练仅仅说成记知识、后训练仅仅说成学礼貌。这里给出常见侧重点，不把模型配方说成统一标准。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)

## P19 监督微调：用示例学习如何回答

这里展开 SFT 与模板的关系。训练数据按角色和边界组织，模型学习接下来轮到 assistant 回复，也学习答案的内容、风格和形式。这里金额是教学数据。严格格式要求可以在应用侧结合接口支持的约束解码或 Schema 校验，这属于推理和程序处理层，和训练模型养成习惯不同。

来源（不朗读）：

- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)

## P20 聊天界面背后的消息与模板

【演示】默认展示两轮上下文。先点“第一轮”，再点“加入第二轮”，观察用户追问“那两晚呢”时输入怎样变化。右边会出现前一轮问题与回答，最后再次以 assistant 起始标记结束。API 中的 messages 是应用层结构；服务端或框架再套用模型需要的模板。不同模型可能使用完全不同的控制标记，不能把本页的 ChatML 当成所有模型都采用的统一底层协议。

来源（不朗读）：

- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)

## P21 上下文窗口与聊天记录

解释为什么对话久了可能出现忘记早先要求：有时是应用没有提供完整历史，有时是压缩丢失细节，有时是模型没有正确利用已提供的信息。不能只看产品界面还显示记录，就断言模型一定看到了所有内容。记忆部分会说明怎样把重要事项保存在外部，再按需带回。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)

## P22 差旅助手目前还缺什么？

举一个幻觉例子：模型给出很像公司制度的“每晚六百元”，甚至附了不存在的条款编号。语气坚定并不是证据。知识过时和幻觉也不是完全同义：旧知识曾经可能正确，但如今不适用。后面的方法分别增加新信息、内部资料和可靠执行能力，并不承诺消除所有错误。

来源（不朗读）：

- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P23 一个最小的差旅问答应用

这页是从模型到应用的桥梁。把聊天产品拆开看，模型是其中的组件，产品还包含状态、输入组织和结果处理。我们先保留最小结构，不急着叫它 Agent。下一节开始，每增加一个新概念，都要能指出它放在这张图的哪里、解决了哪个实际问题。

## P24 提示词工程：目标、示例与格式

提示词工程不是背神奇咒语。奖励金额的说法曾经很流行，但不能用它定义这个领域，也不能在没有对照实验时宣称有效。Few-shot 的价值是让模型看到任务的判定和输出形式。对比 SFT：两者都可以有示例，Few-shot 把示例放进本次上下文，SFT 用示例执行训练。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

## P25 上下文工程：每一步给它什么信息

上下文工程不是模型能力变强以后提示词就没用了。它描述更大的工程问题：模型在哪一步需要哪份信息，信息怎么来、怎么更新、怎么压缩。接下来 RAG 负责按问题找资料，工具负责取实时数据或做动作，Agent 则可以在一定范围内决定下一步要获取什么。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)

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

本页无需朗读。HTML 中可直接点击来源，或按 N 查看当前页讲稿与引用。差旅制度、汇率、金额、工具响应和示意向量是教学构造；分词样例是指定分词器的实际结果；文件清单与插图来源见源码目录中的素材清单。

来源（不朗读）：

- [Hugging Face · 语言模型与 Transformer](https://huggingface.co/learn/llm-course/chapter1/4)
- [tiktoken · cl100k_base](https://github.com/openai/tiktoken)
- [Qwen3-8B · 官方文件列表](https://huggingface.co/Qwen/Qwen3-8B/tree/main)
- [Qwen3-8B · config.json](https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json)
- [Safetensors · 张量存储格式](https://huggingface.co/docs/safetensors/index)
- [Qwen3 · 官方发布说明](https://qwenlm.github.io/blog/qwen3/)
- [Qwen3-8B · 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-32B · 模型卡](https://huggingface.co/Qwen/Qwen3-32B)
- [Qwen3-30B-A3B · 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B)
- [Qwen3-235B-A22B · 模型卡](https://huggingface.co/Qwen/Qwen3-235B-A22B)
- [Llama 3.3 70B Instruct · 模型卡](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct)
- [DeepSeek-V3 · 模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V3)
- [Hugging Face · 监督微调](https://huggingface.co/learn/llm-course/chapter11/1)
- [Transformers · Chat templates](https://huggingface.co/docs/transformers/main/en/chat_templating)
- [InstructGPT · 人类反馈与指令遵循](https://arxiv.org/abs/2203.02155)
- [PEFT · LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)
- [Hinton 等 · 知识蒸馏](https://arxiv.org/abs/1503.02531)
- [Transformers · 量化](https://huggingface.co/docs/transformers/main/en/quantization/overview)

## P47 参考资料：检索、工具与 Agent

本页无需朗读。HTML 中可直接点击来源，或按 N 查看当前页讲稿与引用。差旅制度、汇率、金额、工具响应和示意向量是教学构造；分词样例是指定分词器的实际结果；文件清单与插图来源见源码目录中的素材清单。

来源（不朗读）：

- [Anthropic · 上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [Lewis 等 · RAG](https://arxiv.org/abs/2005.11401)
- [Sentence Transformers · 语义相似性](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Claude · 工具调用](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Anthropic · Workflow 与 Agent](https://www.anthropic.com/research/building-effective-agents)
- [Yao 等 · ReAct](https://arxiv.org/abs/2210.03629)
- [Anthropic · 长任务 Harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [MCP · 官方介绍](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Agent Skills · 官方格式](https://agentskills.io/home)

