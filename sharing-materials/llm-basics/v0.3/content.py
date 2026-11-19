"""v0.3: visible slide content, notes and citations kept together."""
import html

SOURCES = {
 'llm': ('Hugging Face · 语言模型与 Transformer', 'https://huggingface.co/learn/llm-course/chapter1/4'),
 'tokens': ('tiktoken · cl100k_base', 'https://github.com/openai/tiktoken'),
 'files': ('Qwen3-8B · 官方文件列表', 'https://huggingface.co/Qwen/Qwen3-8B/tree/main'),
 'config': ('Qwen3-8B · config.json', 'https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json'),
 'weight_index': ('Qwen3-8B · 权重分片索引', 'https://huggingface.co/Qwen/Qwen3-8B/blob/main/model.safetensors.index.json'),
 'tokenizer': ('Qwen3-8B · tokenizer.json', 'https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json'),
 'tokenizer_config': ('Qwen3-8B · tokenizer_config.json', 'https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json'),
 'safetensors': ('Safetensors · 张量存储格式', 'https://huggingface.co/docs/safetensors/index'),
 'qwen': ('Qwen3 · 官方发布说明', 'https://qwenlm.github.io/blog/qwen3/'),
 'q8': ('Qwen3-8B · 模型卡', 'https://huggingface.co/Qwen/Qwen3-8B'),
 'q8awq': ('Qwen3-8B-AWQ · 量化配置', 'https://huggingface.co/Qwen/Qwen3-8B-AWQ/blob/main/config.json'),
 'q8gguf': ('Qwen3-8B-GGUF · 权重文件', 'https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main'),
 'q30': ('Qwen3-30B-A3B · 模型卡', 'https://huggingface.co/Qwen/Qwen3-30B-A3B'),
 'q30fp8': ('Qwen3-30B-A3B-FP8 · 量化配置', 'https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json'),
 'q235': ('Qwen3-235B-A22B · 模型卡', 'https://huggingface.co/Qwen/Qwen3-235B-A22B'),
 'sft': ('Hugging Face · 监督微调', 'https://huggingface.co/learn/llm-course/chapter11/1'),
 'chat': ('Transformers · Chat templates', 'https://huggingface.co/docs/transformers/main/en/chat_templating'),
 'rlhf': ('InstructGPT · 人类反馈与指令遵循', 'https://arxiv.org/abs/2203.02155'),
 'lora': ('PEFT · LoRA', 'https://huggingface.co/docs/peft/main/en/conceptual_guides/lora'),
 'distill': ('Hinton 等 · 知识蒸馏', 'https://arxiv.org/abs/1503.02531'),
 'quant': ('Transformers · 量化与数值格式', 'https://huggingface.co/docs/transformers/quantization/concept_guide'),
 'awq': ('Lin 等 · AWQ', 'https://arxiv.org/abs/2306.00978'),
 'gptq': ('Frantar 等 · GPTQ', 'https://arxiv.org/abs/2210.17323'),
 'gguf': ('GGML · GGUF 文件格式', 'https://github.com/ggml-org/ggml/blob/master/docs/gguf.md'),
 'context': ('Anthropic · 上下文工程', 'https://www.anthropic.com/research/effective-context-engineering-for-ai-agents'),
 'vllm_api': ('vLLM · Chat Completions 请求结构', 'https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest'),
 'rag': ('Lewis 等 · RAG', 'https://arxiv.org/abs/2005.11401'),
 'embedding': ('Sentence Transformers · 语义相似性', 'https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html'),
 'tools': ('Claude · 工具调用', 'https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview'),
 'agents': ('Anthropic · Workflow 与 Agent', 'https://www.anthropic.com/research/building-effective-agents'),
 'react': ('Yao 等 · ReAct', 'https://arxiv.org/abs/2210.03629'),
 'harness': ('Anthropic · 长任务 Harness', 'https://www.anthropic.com/research/effective-harnesses-for-long-running-agents'),
 'mcp': ('MCP · 官方介绍', 'https://modelcontextprotocol.io/docs/getting-started/intro'),
 'mcp_arch': ('MCP · 架构与参与者', 'https://modelcontextprotocol.io/docs/learn/architecture'),
 'skills': ('Agent Skills · 官方格式', 'https://agentskills.io/home'),
}
SLIDES=[]

def p(t, cls=''): return f'<p class="{cls}">{t}</p>'
def block(title, text, cls=''): return f'<div class="text-block {cls}"><h3>{title}</h3>{text}</div>'
def cols(*items, cls=''): return f'<div class="columns {cls}">' + ''.join(items) + '</div>'
def note(t): return f'<div class="annotation">{t}</div>'
def code(t, cls=''): return f'<pre class="{cls}"><code>{html.escape(t)}</code></pre>'
def table(headers, rows, cls=''): return f'<table class="{cls}"><thead><tr>'+''.join(f'<th>{x}</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{x}</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table>'
def flow(*steps): return '<ol class="flow">'+''.join(f'<li><b>{t}</b><span>{d}</span></li>' for t,d in steps)+'</ol>'
def image(name,alt,cls=''):return f'<figure class="{cls}"><img data-asset="{name}" alt="{html.escape(alt)}"></figure>'
def buttons(attr, labels):return '<div class="choices">'+''.join(f'<button class="choice {"selected" if i==0 else ""}" data-{attr}="{i}" aria-pressed="{str(i==0).lower()}">{v}</button>' for i,v in enumerate(labels))+'</div>'
def add(chapter,title,lead,body,takeaway,notes,sources=(),cls=''):
 SLIDES.append(dict(chapter=chapter,title=title,lead=lead,body=body,takeaway=takeaway,notes=notes.strip(),sources=list(sources),cls=cls))

add('开场','大模型常见概念','一个语言模型怎样成为能查资料、用工具的 AI 助手？',
 cols('<div class="cover-copy"><h2>从生成一句话，<br>到完成一项任务。</h2><p class="small">v0.3 · 2026 年 11 月</p></div>',image('model-workbench.png','语言模型连接资料、计算器与终端的纸艺插图'),cls='cover-columns'),
 '',
 '今天沿着差旅报销这个任务看大模型。先认识模型、文件和推理，再看聊天时模型收到了哪些信息，最后看差旅助手如何查制度、做换算并交付结果。',cls='cover')

add('开场','一项任务，串起整场分享','“帮我核对这次出差费用，按公司制度整理一份报销说明。”',
 table(['任务推进','需要什么','会遇到的名词'],[
 ('理解这句话并生成回答','语言处理与生成能力','LLM、Token、参数、推理'),
 ('知道公司住宿标准','找到当前有效的内部资料','上下文、RAG、Embedding'),
 ('换算外币并汇总金额','调用外部查询和计算能力','Function Calling、Tool'),
 ('根据缺口继续查找并交付结果','动态决策、状态与运行环境','Agent、ReAct、Harness'),
 ]),
 '先认识模型，再逐步补齐资料、行动和运行环境。',
 '先请大家把这个任务记住。一个人完成它会读制度、看票据、查汇率、算金额并整理说明。语言模型本身能生成文字，但是完整任务需要这些额外信息和动作。我们会先用约半场理解模型，再把后面每一项能力加到差旅助手中。整体约六十到七十分钟，规格表和训练名词可以按听众基础快速带过。')

add('01 / 模型是什么','AI、机器学习与深度学习','这些词描述的范围不同，常常同时出现在同一个产品里。',
 cols('<div class="taxonomy"><div><b>人工智能 AI</b><span>让计算机执行通常需要智能的任务</span><div><b>机器学习 ML</b><span>从数据中学习规律，而非逐条写出规则</span><div><b>神经网络</b><span>用相互连接的计算单元表示和学习关系</span><div><b>深度学习 DL</b><span>通常使用多层神经网络学习表示</span></div></div></div></div></div>',
 block('大语言模型在什么位置？',p('现代 LLM 通常是基于深度神经网络的语言模型，主流架构是 Transformer。')+p('语言模型按“处理语言的任务”命名；历史上也有基于统计方法的语言模型。')+p('AI 的实现也可以包含规则、搜索等方法。不能把所有 AI 都等同于 LLM。','small'))),
 'LLM 是 AI 中的一类模型；“语言模型”与“深度学习”观察的是不同维度。',
 '可以把左边看作常见技术范围的嵌套示意，而不是发展历史或每个领域的严格数学定义。机器学习不只包含神经网络，AI 也不只包含机器学习。现代大语言模型通常位于深度学习这条技术路线中。语言模型的历史比 Transformer 更长，因此不要把语言模型一词直接定义成 Transformer。',('llm',))

add('01 / 模型是什么','语言模型与常见 NLP 任务','NLP 是自然语言处理的任务领域；LLM 可以用统一的输入输出方式完成其中许多任务。',
 table(['任务','输入示例','期望输出'],[
 ('文本分类','“这个月的住宿费怎么报？”','报销咨询'),('信息抽取','“11 月 8 日在上海住了两晚，共 980 元。”','城市：上海；晚数：2；金额：980 元'),('翻译与摘要','一封外文邮件或一份长差旅说明','中文译文或关键事项'),('问答与生成','“解释这条报销规则，并起草一份说明。”','依据材料给出解释，生成文本'),
 ])+note('Large Language Model：通过大规模数据与训练，获得广泛语言处理和生成能力的模型。'),
 'NLP 是做什么；神经网络和 Transformer 是怎样实现。',
 '过去这些任务经常分别训练专用模型，现在可以用同一个语言模型处理多种任务。接下来看看应用如何获得这种能力，再打开一个模型仓库，看里面有哪些文件。',('llm',))

add('02 / 使用与部署','使用模型的两条路线','应用可以调用托管 API，也可以在自己的机器或云算力上运行模型。',
 cols(block('调用托管模型 API',p('应用发送消息和参数，供应商运行模型并返回结果。')+p('团队主要负责组织输入、接入资料与工具、开发应用逻辑和管理调用用量。')),
 block('自己部署开放权重模型',p('获取模型文件，选择推理框架，在自己管理的设备或云算力上提供服务。')+p('<b>团队还需负责：</b>硬件、模型加载、服务并发和运维。'))),
 '同一个开放权重模型，也可以用托管 API 提供给应用。',
 '从普通用户角度还可以直接使用聊天产品；这里讨论开发应用怎样使用模型，因此聚焦 API 和自行部署。不要把开源模型理解为只能本地使用，也不要把本地理解为一定在笔记本电脑上。自管的云 GPU 同样属于自行部署。',('qwen',))

add('02 / 使用与部署','“开源模型”开放了哪些东西？','模型权重、训练资料和使用条件，可以在仓库与许可证里分别查看。',
 table(['组成','得到它能做什么','需要进一步确认'],[
 ('模型权重','加载已有参数执行推理，在许可范围内微调','权重是否可下载，是否限制特定用途'),('结构配置与实现','知道模型类型、维度和计算过程','是否依赖特定库或仓库里的实现代码'),('训练代码与数据信息','了解或尝试复现训练过程','是否完整公开，数据是否可获取'),('许可证','确认使用、修改、分发等条件','商业使用、再分发和衍生模型的具体约定'),
 ]),
 '权重用于运行模型，训练资料帮助复现，许可证规定使用条件。',
 '这页只建立辨认意识，不讲许可证法务细节。模型仓库通常有模型卡、配置和权重等，但是否提供完整训练数据、训练代码，要逐项看。Qwen3 这组模型的官方说明给出了 Apache 2.0 许可；其他模型可能采用不同许可，不能从一个模型推及所有模型。',('qwen','files'))

add('03 / 模型文件','一个模型仓库里的三类文件','从 Hugging Face 的 Qwen3-8B 仓库看配置、权重和分词器。',
 cols('<div class="repo-list"><div class="repo-heading"><h3>Qwen / Qwen3-8B</h3></div><div class="repo-file"><b>config.json</b><span>728 B</span></div><div class="repo-file"><b>generation_config.json</b><span>239 B</span></div><div class="repo-file weights"><b>model-00001-of-00005.safetensors</b><span>4 GB</span></div><div class="repo-file weights"><b>model-00002-of-00005.safetensors</b><span>3.99 GB</span></div><div class="repo-file weights"><b>… 另有 3 个权重分片</b></div><div class="repo-file"><b>model.safetensors.index.json</b><span>32.9 kB</span></div><div class="repo-file tokenizer"><b>tokenizer.json</b><span>11.4 MB</span></div><div class="repo-file tokenizer"><b>tokenizer_config.json</b><span>9.73 kB</span></div><div class="repo-file tokenizer"><b>vocab.json / merges.txt</b><span>词表 / 合并规则</span></div></div>',
 '<div class="file-explain">'+block('① 配置',p('<code>config.json</code><br>声明模型类型、层数、隐藏维度等，供对应实现读取。'))+block('② 权重',p('<code>model-*.safetensors</code><br>训练得到的张量。多个文件通常是分片，索引文件记录位置。'))+block('③ 分词器',p('<code>tokenizer.json</code>、<code>vocab.json</code>、<code>merges.txt</code> 等<br>保存文本与 Token ID 之间的转换规则。'))+'</div>',cls='media-left'),
 '配置说明结构，权重提供数值，分词器在文本和编号之间做转换。',
 'Qwen3-8B 的权重分在五个文件里，索引记录每个张量落在哪一片。它的分词器除词表外还用了合并规则和特殊 Token 配置。接下来顺着一次输入走，先看分词器怎么读文本，再看模型怎么用权重继续生成。',('files','safetensors'),cls='file-page')

add('04 / 模型如何运行','文字进入模型前，会变成 Token','分词器按规则切分文本，再把每个 Token 转成编号。',
 buttons('token',['中文','英文','代码'])+'<div class="token-demo"><div class="example-head"><b id="tokenText">今天开会。</b><span id="tokenCount">__TOKEN_COUNT__ 个 Token</span></div><div class="token-list" id="tokenPieces">__TOKENS__</div></div>'+
 cols(block('Token 是处理单位',p('一个 Token 可能对应一个词、部分词、标点，甚至一段字符的部分字节。中文、英文与代码的切分方式可能不同。')),block('Token ID 是词表编号',p('分词器为每个 Token 分配整数编号，模型用它找到对应的表示。'))),
 '字符数、字数、Token 数没有固定换算关系。',
 '【演示】切换中文、英文和代码，看空格、标点怎样参与切分。分词器把句子变成编号序列，模型会用这些编号查到各个 Token 的向量表示。下一页看看模型收到输入后怎样继续生成。',('tokens',),cls='token-page')

add('04 / 模型如何运行','生成下一步，再把结果接回上下文','自回归文本模型每一步计算下一个 Token 的概率分布，再选一个接到末尾。',
 cols('<div><div class="generation" id="generationText">今天的天气</div>'+buttons('generate',['初始输入','生成一步','继续生成'])+'</div>',
 block('每一步都利用前文',p('模型把当前上下文转换成内部表示，再计算下一个 Token 的候选分布。已生成的内容也会影响后续生成。')+p('Transformer 中的 Attention 帮助模型利用上下文里的不同位置。'))),
 '权重文件保存的参数参与每一步计算。',
 '【演示】点生成一步和继续生成。新生成的文字会接回前文，作为继续生成的依据。这个计算过程使用了训练得到的权重。下面区分形成权重的训练和使用权重的推理。',('llm',))

add('04 / 模型如何运行','训练与推理，发生在不同阶段','训练形成模型参数，推理使用这些参数处理当前输入。',
 table(['','训练 Training','推理 Inference'],[
 ('输入','训练数据与训练目标','用户问题、指令、历史和参考资料'),('主要动作','计算误差或奖励信号，调整可训练参数','执行模型计算，生成输出'),('产生什么','新的模型或适配器权重','一次回答、结构化结果或工具调用请求'),('差旅助手例子','用报销问答示例训练任务行为','把本次制度和问题提供给已有模型'),
 ]),
 '把一份资料放进上下文，与用它训练模型，是两种操作。',
 '训练可以发生在模型提供方，也可以发生在应用团队的微调流程中。推理是我们日常使用模型的阶段。先建立这一差异，后面才能解释为什么 RAG 的资料更新不等于重新训练，为什么长期记忆也通常不写进权重。我们稍后会把训练进一步分成预训练和后训练。',('llm',))

add('04 / 模型如何运行','配置、实现代码与权重如何配合','config.json 声明结构，模型实现代码定义具体计算。',
 cols('<div><p class="code-label">Qwen3-8B 配置节选</p>'+code('''{
  "architectures": ["Qwen3ForCausalLM"],
  "model_type": "qwen3",
  "num_hidden_layers": 36,
  "hidden_size": 4096,
  "num_attention_heads": 32,
  "vocab_size": 151936
}''')+'</div>',
 block('框架按什么顺序加载？',p('<b>1.</b> 识别 <code>model_type</code>，选择对应模型类。')+p('<b>2.</b> 按配置建立各层和张量形状。')+p('<b>3.</b> 将权重文件中的数值加载到对应位置。')+p('<b>4.</b> 用匹配的分词器编码输入、解码输出。')+p('Safetensors 保存张量及相关元数据；完整的前向计算逻辑由模型实现提供。','small'))),
 '模型文件必须与支持该架构的实现、分词器正确配合。',
 '这里展示 Qwen3-8B 的几个配置字段。框架按这些字段确定层数和维度，用模型类定义计算。下一页从框架刚建好的层出发，找出它的参数保存在哪个文件里。',('config','safetensors'))

add('04 / 模型如何运行','权重文件怎样保存模型参数？','训练得到的参数按张量名称存放。索引记录每个张量所在的文件分片。',
 cols('<div><p class="code-label">Qwen3-8B · model.safetensors.index.json 节选</p>'+code('''{
  "weight_map": {
    "model.embed_tokens.weight":
      "model-00001-of-00005.safetensors",
    "lm_head.weight":
      "model-00005-of-00005.safetensors"
  }
}''')+'</div>',
 '<div>'+block('索引指向文件',p('输入用的词嵌入矩阵在第 1 片，计算输出分数用的 lm_head 权重在第 5 片。'))+
 block('分片保存数值',p('Safetensors 文件头记录张量的数据类型、形状和字节位置。文件的数据区保存实际权重。'))+'</div>'),
 '分词得到的 Token ID，用来从词嵌入矩阵中取出对应的一行。',
 '配置页的 vocab_size 为 151,936，hidden_size 为 4,096，因此 Qwen3-8B 的输入词嵌入矩阵有 151,936 行、每行 4,096 个数。框架按张量名称查索引，再从分片加载整张矩阵到模型对应的位置。算出输出分数时还会用到另一个张量，也就是 lm_head 权重。下一页看看词嵌入矩阵所用的编号怎样从文本得到。',('config','weight_index','safetensors'))

add('04 / 模型如何运行','分词器文件怎样把文本变成 ID？','在 Qwen3-8B 中，分词规则、词表和特殊标记共同决定输入的编号序列。',
 cols('<div><p class="code-label">Qwen3-8B · 编码一段文本</p>'+code('''输入  "Hello, world!"
切分  ["Hello", ",", " world", "!"]
编号  [9707, 11, 1879, 0]''')+
 '<p class="code-label special-token-label">对话中的两个边界标记</p>'+code('''<|im_start|>  →  151644
<|im_end|>    →  151645''')+'</div>',
 block('仓库里的分词文件',p('<code>tokenizer.json</code> 打包分词规则与词表。')+p('<code>vocab.json</code> 保存 Token 到 ID 的映射，<code>merges.txt</code> 保存 BPE 合并规则。')+p('<code>tokenizer_config.json</code> 包含特殊 Token 和聊天模板等配置。'))),
 '输入时把文字编码成 ID，生成后再把 ID 解码回文字。',
 '这一页对照 Qwen3-8B 的文件。Hello 的编号是 9707，world 前面的空格也属于该 Token，在词表内部用 Ġworld 表示。这两个对话边界同样有专用编号，后面讲聊天模板时能看到它们。前面的交互页使用了另一个分词器，因此同一段英文会看到不同编号。',('tokenizer','tokenizer_config','files'))

add('05 / 模型规格','模型名里的数值格式与量化','量化用较低位宽表示权重，可减少模型文件体积和权重内存。',
 '<div class="model-name"><span>Qwen3<small>家族与代际</small></span><i>－</i><span>30B<small>约 300 亿总参数</small></span><i>－</i><span>A3B<small>约 30 亿激活参数</small></span><i>－</i><span>FP8<small>8 位浮点权重版本</small></span></div>'+
 cols(block('数值格式 · 一个值占多少位',p('<b>FP32</b>：32 位浮点，每个值 4 字节。<br><b>FP16 / BF16</b>：16 位浮点，每个值 2 字节。<br><b>FP8 / INT8</b>：8 位浮点或整数，每个值 1 字节。<br><b>INT4</b>：4 位整数，两个值可打包进 1 字节。')),
 block('量化方案和文件格式',p('<b>AWQ / GPTQ</b> 是权重量化方案，常见 4 位版本。AWQ 用激活统计保护重要权重，GPTQ 根据校准数据逐层减小量化误差。')+p('<b>GGUF</b> 是文件格式。<b>Q4_K_M</b> 是其中常见的量化规格，以 4 位为主。'))),
 '8B 权重按位宽估算，16 位约 16 GB，4 位约 4 GB。',
 'B 表示十亿，A3B 指每个 Token 计算时约有 30 亿参数参与。下一页会看到官方模型卡里的精确规格。FP16 和 BF16 的字节数相同，BF16 可表示的数值范围更大，FP16 有更多尾数位。量化常用缩放因子把高精度值映射到低位宽，也可能只转换一部分权重。用参数量乘以每个值的位宽，可以快速估算纯权重体积。下载文件还包括量化元数据等，推理需要为 KV Cache 和其他计算数据留空间。',('q30','q30fp8','quant','awq','gptq','gguf'))

add('05 / 模型规格','同一个模型的不同权重版本','对照 Qwen3 的原始权重与量化发布，观察参数量、数值表示和文件格式。',
 table(['官方发布版本','架构','总参数 / 激活参数','主要权重表示','文件格式'],[
 ('Qwen3-8B','Dense','8.2B','BF16（16 位）','Safetensors'),
 ('Qwen3-8B-AWQ','Dense','8.2B','AWQ（4 位）','Safetensors'),
 ('Qwen3-8B-GGUF','Dense','8.2B','Q4_K_M（以 4 位为主）','GGUF'),
 ('Qwen3-30B-A3B','MoE','30.5B / 3.3B','BF16（16 位）','Safetensors'),
 ('Qwen3-30B-A3B-FP8','MoE','30.5B / 3.3B','FP8（8 位）','Safetensors'),
 ],'model-table'),
 '量化版本沿用原模型的参数规模，改变的是权重的数值表示。',
 '先横着读一行，再比较前三行。Qwen3-8B 量化后仍是 8.2B。AWQ 版在配置里写明了 4 位，GGUF 仓库有多个量化文件，这里选 Q4_K_M，官方文件大小是 5.03 GB。后两行则展示同一个 MoE 模型的 BF16 和 FP8 版本。它为什么会同时写总参数和激活参数？下一页看 Dense 和 MoE 的计算方式。',('q8','q8awq','q8gguf','q30','q30fp8'))

add('05 / 模型规格','Dense 与 MoE','每个 Token 经过前馈层时，Dense 使用同一组参数，MoE 会选择部分专家。',
 cols(image('dense-moe.png','Dense 通过共享前馈网络，MoE 路由选中部分专家参与计算','moe-figure'),
 '<div>'+block('Dense：稠密模型',p('每个 Token 通常使用各层共同的一组稠密参数进行计算。'))+
 block('MoE：混合专家模型',p('部分层设多个专家子网络，路由为当前 Token 选中其中一部分。未选中的权重仍需存储和调度。'))+
 p('图中绿色分支参与当前 Token 的计算。','small')+'</div>',cls='moe-columns'),
 '总参数影响权重存储，激活参数反映单个 Token 用到的规模。',
 '左图是共享前馈网络，右图为部分激活的专家前馈网络；它们都只是整体 Transformer 中的局部示意。图中的专家不是独立 Agent，也不一定具有可命名的人类专业。Qwen3-235B-A22B 的官方配置实际有 128 个专家、每 Token 激活其中 8 个；本图只用 4 选 2 便于演示。A22B 不能理解为仅需存储 22B 权重。',('q235','qwen'),cls='moe-page')

add('06 / 推理服务','推理框架把模型文件运行起来','框架加载文件、执行生成，服务接口接收应用的请求。',
 flow(('模型文件','配置、权重、分词器'),('加载与推理','建立网络、执行生成'),('服务接口','接收请求、返回结果'),('业务应用','会话、资料与交互'))+
 table(['常见框架','用途'],[
 ('Transformers','提供模型实现、权重加载与文本生成接口'),('vLLM / SGLang','提供模型推理服务，调度并发请求'),('llama.cpp','常用于在本地设备上运行 GGUF 模型'),
 ]),
 '应用调用自己部署的模型，也可以使用 API。',
 '推理框架负责生成，服务层把生成包装成请求和响应。有些项目把两者放在一起。模型运行起来了，为什么用户发出提问时，它会按要求给出回答？接着看训练怎样塑造这种行为。',('files','qwen'))

add('07 / 训练对话助手','预训练与后训练','预训练让模型学会续写，后训练进一步塑造它怎样回答和完成任务。',
 table(['训练阶段','训练信号','模型学习什么'],[
 ('预训练','大规模数据中的后续 Token','语言规律、知识和续写能力'),
 ('后训练 · SFT（监督微调）','指令、问题与示范答案','按要求回答，例如根据差旅制度说明超标金额'),
 ('后训练 · RLHF（人类反馈强化学习）','从人类偏好中获得的奖励','更倾向于给出人类偏好的回答'),
 ])+
 cols(block('LoRA · 更新哪些参数',p('冻结原有权重，训练一组小型适配器。可以用 LoRA 做 SFT。')),
 block('蒸馏 · 训练信号从哪里来',p('用教师模型的输出等信号训练学生模型，例如把报销问答能力迁移给小模型。'))),
 'SFT 给模型看示范，RLHF 让模型学习人类偏好的答法。',
 '回想前面的训练与推理。预训练和后训练都在训练，区别在于数据和训练目标。比如 SFT 给出问题和期望回复，让模型模仿。LoRA 关注微调时改哪些参数，蒸馏关注怎样使用教师的信号，它们可以跟其他训练方法配合。现在仍用报销问题，看看人工比较的结果怎样进入强化学习。',('llm','sft','rlhf','lora','distill'),cls='training-page')

add('07 / 训练对话助手','RLHF：先训练奖励模型，再优化回答','住宿上限 500 元，超标须事前审批。一晚花了 560 元，能全额报销吗？',
 table(['候选回答','人工排序','理由'],[
 ('A · 超出 60 元。全额报销要看事前审批记录。','第 1','算出超额，指出审批条件'),
 ('B · 可以全额报销。','第 2','直接断定可以报销'),
 ])+
 flow(('收集人类偏好','让人比较同一问题的多个回答，记录哪些更好。'),
      ('训练奖励模型（RM）','用排序数据训练评分模型。给它问题和回答，它会输出一个分数。'),
      ('强化学习优化助手','让经 SFT 的助手生成新回答，用奖励模型打分，再根据奖励更新助手。')),
 '人工排序教会奖励模型怎样评分，分数再用于训练生成回答的模型。',
 '这里讲的是 InstructGPT 的做法。先有一批监督微调数据和一个经 SFT 的助手，再收集像 A 优于 B 这样的排序。奖励模型学习给 A 更高的分数。训练助手时，让它为新问题生成回答，奖励模型根据问题和回答给出标量奖励，接着使用 PPO 这类强化学习算法更新助手。奖励模型给分和助手生成是两项分工。下一页回到同一个问题，对照训练样本与上线时的输入。',('rlhf',))

add('08 / 对话请求','从 SFT 样本到聊天模板','同一段差旅对话，训练时带示范回复，推理时把生成位置留给模型。',
 buttons('chat',['推理：第一轮','推理：加入第二轮'])+
 cols('<div><p class="code-label">训练 · 带示范回复的 messages</p><pre class="chat-code" id="chatMessages"></pre>'+p('SFT 用 assistant 的示范回复提供学习目标，更新可训练参数。')+'</div>',
 '<div><p class="code-label">推理 · 套入 ChatML 风格模板后</p><pre class="chat-code" id="chatRaw"></pre>'+p('应用组织消息，框架套入模板并编码为 Token ID，模型从最后一行接着生成。')+'</div>'),
 '第二轮会带上先前的提问和回复，让模型理解“两晚”指什么。',
 '【演示】先看左边的训练样本，assistant 位置已有要学习的回复。右边先点“推理：第一轮”，看最后留下 assistant 的起始标记。再点“推理：加入第二轮”，旧的用户消息和助手回复一起成了历史，模型从新的 assistant 起始标记继续。训练和推理会使用匹配模型的聊天模板。接下来看看运行起来的助手还缺哪些信息和能力。',('sft','chat'),cls='chat-page')

add('09 / 常见局限','差旅助手目前还缺什么？','语言流畅，只能说明它生成了看似合理的文本；任务正确还需要信息与执行依据。',
 table(['用户问什么','可能发生的问题','后面怎样补齐'],[
 ('“给出公司最新住宿标准。”','编造内部规定，或沿用过时信息','检索有效制度，给出依据'),('“今天新币换人民币是多少？”','用训练中记住的旧数值回答','外部查询，保留日期和来源'),('“这几项费用一共多少？”','精确计算或单位换算出错','计算工具并检查输入'),('“按照附件的例外条款处理。”','遗漏长文中的关键细节','检索相关条款、组织上下文'),
 ])+note('幻觉包括编造事实、条款、来源和接口。检索与工具可以降低部分错误，仍需检查结果。'),
 '先辨认缺口：缺资料、缺计算，还是没有正确使用已有信息？',
 '举一个幻觉例子：模型给出很像公司制度的“每晚六百元”，甚至附了不存在的条款编号。语气坚定并不是证据。知识过时和幻觉也不是完全同义：旧知识曾经可能正确，但如今不适用。后面的方法分别增加新信息、内部资料和可靠执行能力，并不承诺消除所有错误。',('rag','context'))

add('10 / 模型到应用','一个最小的差旅问答应用','先把一次模型调用嵌进产品，再按需求增加资料、工具和流程。',
 flow(('用户界面','输入问题、展示答案'),('应用组织请求','指令、历史、当前问题'),('模型服务','托管 API 或自部署服务'),('应用处理结果','解析、校验与呈现'))+
 cols(block('模型提供什么？',p('使用当前上下文生成文本、结构化内容，或工具调用请求。模型本身不管理这个产品的页面和业务数据库。')),
 block('应用负责什么？',p('决定每次给模型哪些信息，保存会话，连接业务能力，处理失败，并将结果交给用户。')))+
 note('贯穿例子：先做“根据已提供制度回答”的助手，再加入自动检索和工具执行。'),
 '同一个模型接入不同资料、工具和流程，会成为不同应用。',
 '这页是从模型到应用的桥梁。把聊天产品拆开看，模型是其中的组件，产品还包含状态、输入组织和结果处理。我们先保留最小结构，不急着叫它 Agent。下一节开始，每增加一个新概念，都要能指出它放在这张图的哪里、解决了哪个实际问题。')

add('11 / 把任务交代清楚','提示词工程：目标、示例与格式','“回答正确奖励 100 美元”可以当趣味开场；更可控的做法是交代任务和判断标准。',
 cols('<div><p class="code-label">模糊要求</p>'+code('帮我看一下这些费用，整理好。')+p('“看什么”“怎样算整理好”“能否补写缺失信息”都没有明确。')+
 '<div class="example-quote">“回答对了给你 100 美元。”<span>流行提示技巧示例，效果依模型与任务而异。</span></div></div>',
 '<div><p class="code-label">明确任务 + Few-shot</p>'+code('''任务：从报销说明提取城市、晚数、金额。
约束：只依据原文；缺失字段写 null。
格式：JSON，不添加其他字段。

示例输入：上海住两晚，共 980 元。
示例输出：
{"city":"上海","nights":2,"amount":980}

现在处理：北京住宿花了 450 元。''')+'</div>'),
 'Few-shot 提供输入输出示例；它使用上下文，通常不更新参数。',
 '提示词工程不是背神奇咒语。奖励金额的说法曾经很流行，但不能用它定义这个领域，也不能在没有对照实验时宣称有效。Few-shot 的价值是让模型看到任务的判定和输出形式。对比 SFT：两者都可以有示例，Few-shot 把示例放进本次上下文，SFT 用示例执行训练。',('context',))

add('11 / 把任务交代清楚','上下文工程：每一步给它什么信息','除了写指令，还要管理历史、证据、工具说明与工具结果。',
 table(['上下文组成','差旅助手需要的内容','选择与组织'],[
 ('指令与输出约定','核对制度，列出计算过程和缺失信息','保持清晰，避免相互冲突'),('会话与任务状态','出差地点、日期、已确认费用','保留相关事实，更新已完成事项'),('检索资料','当前有效的住宿与汇率使用条款','提供相关片段、版本、出处'),('工具定义与结果','查询汇率、计算金额的接口与返回','定义清楚，返回必要数据与错误'),
 ])+note('关注点扩展到模型每次可见的完整上下文。提示词工程仍然是其中的一部分。'),
 '信息适用、相关、清晰，比把所有材料一次塞进去更有帮助。',
 '上下文工程关心模型在哪一步需要哪份信息，以及应用应该怎样获取、更新和压缩这些信息。下一页打开一次请求，看看历史、资料和当前问题放在什么位置。',('context',))

add('11 / 把任务交代清楚','一次请求怎样用到上下文窗口？','用户接着问“两晚共花了 1,120 元呢？” 应用把相关历史和住宿条款一起发给模型。',
 cols('<div><p class="code-label">vLLM · POST /v1/chat/completions</p>'+code(r'''{
  "model": "Qwen/Qwen3-8B",
  "max_completion_tokens": 300,
  "messages": [
    {"role": "system", "content": "按给定差旅制度回答。"},
    {"role": "user", "content": "一晚花了 560 元，能全额报销吗？"},
    {"role": "assistant",
     "content": "超出 60 元。全额报销要看事前审批记录。"},
    {"role": "user",
     "content": "§3.2 上限 500 元/晚。§3.3 超标须事前审批。\n问题：两晚共花了 1,120 元呢？"}
  ]
}''')+'</div>',
 '<div>'+block('应用选了哪些内容？',p('保留前一轮问答，说明“两晚”指住宿。把 §3.2 和 §3.3 放进最后一条消息，提供计算和判断依据。'))+
 block('窗口怎样限制长度？',p('消息经模板编码后占用输入 Token，输入与生成共用窗口。这次请求允许生成最多 300 个 Token。历史很长时，应用可留下相关问答或摘要。'))+'</div>'),
 '按每晚 500 元计算，两晚超出 120 元。能否全额报销要看事前审批记录。',
 '这是一个 vLLM 的 Chat Completions 请求体。两条历史消息让模型知道用户在追问住宿，最后一条 user 消息把本轮问题和适用条款放在一起。服务按 Qwen3-8B 的聊天模板编码消息，输入长度和可生成的长度受服务配置的上下文窗口约束。若此前对话还谈了订机票，应用可以省掉那部分，把空间留给住宿问题及依据。这里条款已经放进请求，下一页讲应用怎样用 RAG 找出这些条款。',('context','vllm_api','chat'),cls='context-request')

add('12 / 接入资料','RAG：检索资料，再生成回答','Retrieval-Augmented Generation 把外部资料带入回答过程。',
 '<div class="pipeline-row"><b class="lane-label">资料准备</b>'+flow(('解析与切分','按内容形成文档片段'),('索引','关键词、向量等索引'),('保留来源','文档、版本、段落位置'))+'</div>'+
 '<div class="pipeline-row"><b class="lane-label">回答问题</b>'+flow(('检索与重排','选出相关且适用的片段'),('组装上下文','问题 + 指令 + 资料'),('生成与关联来源','依据资料回答'))+'</div>'+
 note('向量检索是一种常见实现，关键词和混合检索也能参与。RAG 通常不会因此更新生成模型权重。'),
 'RAG 把“需要知道什么”从模型参数，扩展到可更新的外部资料。',
 '可以用开卷答题作直观比喻：先找到相关页，再根据它回答。准备资料和回答问题是两个阶段，前者不必每次用户提问都重做。Embedding 是常见的索引工具，但 RAG 的核心是检索与生成结合，不是必须有向量数据库。这里介绍工程中常见模式，原始论文有更具体的模型训练方案。',('rag','embedding'))

add('12 / 接入资料','Token ID 与 Embedding：两种不同的数值','都是数字，不代表它们表达相同的东西。',
 table(['','Token ID','Embedding 向量'],[
 ('形式','一个整数编号，例如 1205','一组数，例如 [0.12, −0.34, …]'),('含义','标识词表中的某个 Token','模型学到的一组特征表示'),('能否按数值相近比较语义','ID 1205 与 1206 相邻，不代表意思相近','在合适模型、空间和相似度下，用于比较内容相关性'),('典型用途','把文本编码成模型输入序列','模型内部表示，或为检索表达句子与文档'),
 ])+note('语言模型把 Token ID 映射为内部向量，检索模型则常为整句或文档生成向量。'),
 'Token ID 像编号；Embedding 像一组特征坐标。',
 '这页专门避免“模型都是数字，所以把 Token 直接拿去算相似度”的误解。Token ID 是离散标识。语言模型内部会把 ID 映射成向量，并进一步计算上下文表示；而检索中常用的 Embedding 模型会将一段文本表示为适合检索比较的向量。二者有关联，但不能随意拿语言模型某个内部层的向量替代经过验证的检索模型。',('tokens','embedding'),cls='embedding-page')

add('12 / 接入资料','Embedding 检索与重排序','不同措辞可以指向相同主题，准确型号和编号也可能需要关键词匹配。',
 cols('<div><div class="retrieval-example"><p class="kicker">用户问题</p><h3>出差住酒店，最多能报多少？</h3><div class="document-hit"><b>《差旅费用管理办法》§住宿标准</b><p>主题相关：员工出差住宿费用的标准与报销条件。</p></div><div class="document-hit muted-hit"><b>《会议室预订指南》</b><p>同样有“预订”，但解决的是另一个问题。</p></div></div><p class="small">相近含义的内容，合适的 Embedding 模型可给出较高相似度；仍需看文档是否适用。</p></div>',
 block('一次常见的检索组合',p('<b>向量检索：</b>根据语义特征召回内容。')+p('<b>关键词检索：</b>擅长匹配型号、术语、编号等明确字符串。')+p('<b>混合检索：</b>组合两类召回结果。')+p('<b>Reranker：</b>进一步比较问题与候选片段，调整相关性顺序。')+p('比较向量时应使用兼容的模型与配置；相似不等于事实正确。','small'))),
 '召回相关内容之后，还要核对版本、范围与回答依据。',
 '不要把每个向量维度想象成一个能读懂的标签，例如第一维固定代表住宿。大多数表示是分布式的，维度通常也远不止二维。为了不制造误解，这里不用伪装成真实计算结果的散点图，而是展示检索目标。Reranker 也不是所有系统都必需，它可以在候选集上改善排序，增加相应开销。',('embedding','rag'))

add('12 / 接入资料','有资料的回答，怎样才算有依据？','检索命中、生成答案、证据对应，需要分别检查。',
 cols('<div class="document-paper"><p class="kicker">制度版本 v2026.11</p><h3>差旅费用管理办法</h3><p><b>§ 3.2 住宿标准</b><br>员工在适用城市出差，住宿标准为每人每晚 500 元。</p><p><b>§ 3.3 例外情况</b><br>超标准费用须提供事前审批记录。</p><p class="small">来源标识：POLICY-DEMO / §3.2–3.3</p></div>',
 block('问题：一晚 560 元，能全额报吗？',p('<b>有依据的回答：</b>按本例标准超出 60 元。能否全额报销，还需查看事前审批记录。')+p('<b>依据：</b>§3.2 给出标准，§3.3 给出例外条件。')+p('<b>需要补充：</b>这次出差是否有有效审批记录。')+p('仅附一个链接仍不足以证明回答正确；条款必须支持具体结论。','small'))),
 'RAG 改善信息供应；文档适用性和答案推导仍需核对。',
 '这里刻意让模型无法仅凭一条标准就做出全额报销结论。检索到住宿上限还不够，例外条款决定后续问题。一个好回答既说明已知结论，也指出还缺什么证据。制度、金额、版本号都是教学设定。下一节引入工具，让应用获取缺失信息或执行确定的计算。',('rag',))

add('13 / 连接外部能力','Function Calling：生成一个调用请求','模型读工具说明并提出调用，外部程序执行，再把结果交给模型。',
 cols('<div><p class="code-label">应用提供的工具定义</p>'+code('''name: get_exchange_rate
description: 查询指定日期的币种换算率。
parameters:
  base: string   # 原币种
  quote: string  # 目标币种
  date: string   # YYYY-MM-DD''')+'</div>',
 '<div><p class="code-label">模型提出的结构化调用</p>'+code('''{
  "name": "get_exchange_rate",
  "arguments": {
    "base": "SGD",
    "quote": "CNY",
    "date": "2026-11-08"
  }
}''')+'</div>')+
 note('Tool 是可调用的具体能力，如检索、计算、读取文件、查询系统。'),
 '模型产生名称和参数；执行动作由应用或运行环境完成。',
 '工具定义相当于告诉模型：有这项能力，它解决什么问题，需要哪些参数。模型并不是自己获得了网络连接，而是输出一个让运行环境解释的请求。应用需要实际调用业务接口，再返回成功、失败或数据。查汇率的日期也不能随意省略，业务任务可能要求发生日、报销日或某个规定日期。',('tools',))

add('13 / 连接外部能力','一次工具调用的完整往返','查询汇率，再通过计算工具换算 120 新币。',
 buttons('tool',['① 提出查询','② 程序执行','③ 继续计算','④ 根据结果回答'])+
 '<div class="tool-demo"><div class="tool-index" id="toolIndex">01</div><div><h3 id="toolTitle">模型提出查询</h3><pre id="toolResult"></pre></div></div>'+
 cols(block('谁负责执行？',p('应用接收调用请求，执行实际函数，把结果作为工具消息返回。工具失败也应返回明确状态。')),
 block('怎样判断完成？',p('核对查询与计算各自返回的状态和结果。'))),
 '请求、执行、返回结果、生成回复，共同构成工具使用过程。',
 '【演示】四步依次点击。前两步让大家辨认模型输出和运行环境执行，第三步说明工具返回后模型可以继续请求计算。最后回复使用查询结果和计算结果。汇率与响应都是预写教学数据，界面不会真的访问查询服务。业务里还需要处理币种、时间、四舍五入以及制度采用的汇率来源。',('tools',),cls='tool-page')

add('13 / 连接外部能力','提示、RAG、微调与工具，各补什么？','它们可以组合使用，先找任务当前缺少的东西。',
 table(['当前问题','常用手段','主要改变什么'],[
 ('任务与输出要求不清楚','提示词、Few-shot','本次任务描述与示例'),('需要最新或内部资料','RAG / 检索工具','本次可用的外部证据'),('需要计算、查询或执行动作','Tool / Function Calling','应用可调用的外部能力'),('需要系统改善某类任务行为','微调，如 SFT','模型或适配器的可训练参数'),
 ])+note('RAG 可以由固定流程触发，也可以封装成工具供 Agent 选择。工具返回也会成为上下文。'),
 '先定位问题，再选择或组合方法。',
 '这一页把前面容易混淆的方案摆在一起。同样是让模型回答得更好，作用位置不同。资料频繁更新时通常先考虑检索和实时接口；输出习惯不稳可以先改指令和示例，再根据真实任务证据决定是否训练。没有必要一开始就把全部技术都堆进去。',('rag','tools','sft','context'))

add('14 / 自主推进任务','Workflow 与 Agent','关键区别在于：下一步主要由预先定义的程序决定，还是由模型根据反馈动态选择。',
 cols(block('Workflow：步骤与分支预先编排',p('例如：识别问题类型，检索制度，生成回答；缺少关键字段就按固定规则追问。')+flow(('分类','确定请求类型'),('检索','按规则选资料'),('回答','或转交人工'))+p('适合路径清晰的任务，执行过程通常更容易预测。','small')),
 block('Agent：在边界内动态选择行动',p('模型依据当前目标、已有资料和执行反馈，决定接下来查什么、调用什么，或何时结束。')+flow(('选择行动','判断当前缺口'),('执行工具','取得新结果'),('检查与继续','再选择或结束'))+p('适合路径难预先穷举的任务，也可能增加耗时、成本和错误。','small'))),
 '固定流程中也可以安排由模型动态选择行动的环节。',
 '这里采用 Anthropic 给出的实用架构区分，行业对 Agent 的用法并不完全一致。重要的是看控制方式，而不是产品是否给自己贴了 Agent 标签。固定流程也能调用模型和多个工具，Agent 也可能只在一个流程环节里动态工作。先解决实际需求，再增加自主性。',('agents',),cls='workflow-page')

add('14 / 自主推进任务','ReAct：判断、行动、观察，再继续','Reasoning + Acting 是理解 Agent 循环的一种典型模式。',
 '<div class="react-task"><b>任务</b><span>核对 120 新币费用和一晚 560 元住宿，整理报销说明。</span></div>'+
 buttons('react',['① 找制度','② 查汇率','③ 做计算','④ 检查并交付'])+
 '<div class="react-demo"><div class="react-row"><b>当前判断</b><span id="reactReason"></span></div><div class="react-row"><b>行动 Action</b><span id="reactAction"></span></div><div class="react-row"><b>观察 Observation</b><span id="reactObservation"></span></div><div class="react-row"><b>下一步</b><span id="reactNext"></span></div></div>',
 '工具返回的信息会改变 Agent 接下来的行动。',
 '【演示】四步分别获取制度、汇率、计算和交付。最终知道合计金额，也知道超标住宿需要审批，因此报告中要保留缺失审批的提示。这里的“当前判断”只是为了讲解系统状态而写的简短理由，不声称揭示真实模型的内部推理。原始 ReAct 研究强调推理轨迹和行动交替，现代工具调用系统可以采用不同实现。',('react','agents'),cls='react-page')

add('15 / Agent 运行环境','Harness：模型周围的运行与控制系统','较强的 Agent 产品，通常还需要维护状态、提供执行环境并管理每轮输入输出。',
 table(['组成','解决什么问题','差旅任务中的例子'],[
 ('任务状态与进度','知道目标、已做事项与待办','已读制度；汇率已查；还缺审批记录'),('记忆与上下文管理','跨多轮和上下文窗口延续工作','保存事实、检索相关记录、压缩历史'),('工具运行环境','把调用请求变成真实执行','读取文件、调用接口、运行计算'),('执行控制','限制操作范围、管理失败与停止','沙箱、权限、重试、步数和费用上限'),('记录与检查','核对实际动作与最终结果','保存工具响应，检查金额与条款对应'),
 ]),
 '观察 Agent 的实际表现，要同时看模型能力和外围系统。',
 'Harness 可以理解为让模型在任务中运行的整套外部软件。它和上下文工程有交集，但范围更广，还包括执行环境、事件循环、预算和检查。并不是列上这些能力就自动可靠，具体实现是否有效还需要真实任务验证。记忆和压缩是用户特别关心的部分，下一页展开。',('harness','context'))

add('15 / Agent 运行环境','记忆与压缩：长任务怎样接着做？','信息可以存到模型之外，下一次再有选择地带回上下文。',
 cols('<div class="document-paper"><p class="kicker">任务记录</p><h3>保存当前事实与进度</h3><p><b>已确认：</b>住宿 560 元，外币费用 120 SGD，汇率 5.30。</p><p><b>依据：</b>制度 §3.2–3.3 与汇率工具响应。</p><p><b>已完成：</b>合计计算 1,196 元。</p><p><b>待补充：</b>超标住宿是否有事前审批。</p></div>',
 block('下一轮或新上下文怎样恢复？',p('<b>1.</b> 读取目标、进度及相关记忆。')+p('<b>2.</b> 需要细节时重新查原文与工具结果。')+p('<b>3.</b> 把当前所需的信息装入上下文，继续工作。')+p('<b>上下文压缩：</b>把长历史整理成更短的表示，保留关键事实、决定、证据位置和待办。')+p('摘要可能漏细节，保存的记忆也可能过时，需要更新。','small'))),
 '记忆依靠保存和取回；压缩依靠取舍，二者都不会自动保证准确。',
 '任务记录不是把全部对话原样存一遍。关键是下一次能知道哪些事实已确认、哪些来源可复查、哪些动作已执行，避免重复工作或把待办当作完成。普通聊天记录、当前上下文、长期记忆的区别在这里汇合。金额合计是六百三十六加五百六十，得到一千一百九十六。',('harness','context'))

add('15 / Agent 运行环境','工具执行、沙箱与停止条件','让一次长任务能够运行、纠错，并在合适的位置停下来。',
 table(['遇到的情况','Harness 可以提供的机制','对结果有什么影响'],[
 ('需要运行代码处理票据','工作目录、运行时、沙箱和资源限制','规定代码可以在哪里运行、访问什么'),('工具超时或缺少参数','明确错误、有限重试、补充信息','把失败反馈给决策环节，避免无效循环'),('任务有执行边界','权限、必要的人类确认与动作记录','在授权范围内调用工具并保留结果'),('一直查资料却没有结束','完成标准、步数、时限与费用预算','达到条件后交付、停止或报告缺口'),
 ]),
 '用执行结果和交付产物判断任务是否完成。',
 '这页不展开安全架构，只解释常见产品能力的用途。用户问一个复杂问题，背后可能有很多次模型请求和工具执行。预算和停止条件属于运行控制，错误处理把异常变成下一轮决策的信息。动作是否完成，要看真实工具状态和产物，不能只看自然语言的完成声明。',('harness','agents'))

add('16 / 连接与任务方法','Tool、MCP、Skill 的分工','把具体能力、连接协议和任务做法分开，就不容易混淆。',
 table(['概念','回答哪个问题','差旅助手中的例子'],[
 ('Tool<br><span class="term">工具</span>','系统可以调用什么具体能力？','查汇率、读文件、计算金额、导出表格'),('MCP<br><span class="term">Model Context Protocol</span>','应用怎样用标准协议连接外部能力与数据？','接入公司文档服务提供的搜索工具与资源'),('Skill<br><span class="term">任务技能包</span>','这类任务怎样做，有哪些规则与材料？','报销核对步骤、报告模板与配套脚本'),
 ])+note('Tool 可以直接接入，也可以通过 MCP 接入；Skill 可以使用工具，但不要求依赖 MCP。'),
 '三者可以组合，分别处在不同的位置。',
 '可以沿着一个任务描述：Skill 指导按什么步骤做，Agent 选择工具，工具通过直接接口或 MCP 暴露，Harness 负责执行和状态管理。不要说 Skill 天然比 Tool 更强，或者 MCP 自动让工具更聪明。它们解决的问题并不相同。',('mcp','skills','tools'))

add('16 / 连接与任务方法','MCP：应用连接外部系统的标准协议','Host 运行 AI 应用，Client 与 Server 建立连接，Server 暴露相应能力。',
 '<div class="mcp-diagram"><div class="mcp-host"><p class="kicker">AI 应用 / HOST</p><h3>差旅助手</h3><p>模型、对话、工具执行逻辑</p><div class="mcp-client">MCP Client A</div><div class="mcp-client">MCP Client B</div></div><div class="mcp-links"><span>协议连接</span><span>协议连接</span></div><div class="mcp-servers"><div><h3>文档 MCP Server</h3><p>搜索制度、读取文档资源</p></div><div><h3>业务 MCP Server</h3><p>查询审批、读取报销记录</p></div></div></div>'+
 cols(p('<b>不仅能提供工具：</b>协议还定义资源、提示模板等能力。'),p('<b>业务能力仍由系统实现：</b>MCP 规范连接与交互，不替代后端业务规则。')),
 '模型不会因为知道 MCP 名字，就自动获得某个系统的访问能力。',
 '图中客户端处在宿主应用里，并不是语言模型直接运行协议连接。一个服务可以提供多个工具和资源。应用先连接和发现能力，再根据运行方式提供给模型或用户使用。协议支持不意味着所有客户端都实现相同功能或所有服务都提供全部类型。',('mcp','mcp_arch'))

add('16 / 连接与任务方法','Skill：把任务说明和材料打包','以 Agent Skills 格式为例，核心是 SKILL.md，还可包含脚本、参考资料和模板。',
 cols('<div><p class="code-label">一个报销核对 Skill 的目录</p>'+code('''expense-review/
├── SKILL.md
├── references/
│   └── policy-guide.md
├── scripts/
│   └── summarize-expenses.py
└── assets/
    └── report-template.md''')+'</div>',
 block('按需加载，而非全部常驻',p('<b>发现：</b>先了解技能名称和适用场景。')+p('<b>启用：</b>任务匹配时，读取详细说明。')+p('<b>执行：</b>按需加载参考资料，使用工具或配套脚本。')+p('技能内容进入上下文，影响任务做法；加载 Skill 通常不会更新模型权重。')+p('示例步骤：核对条款、查汇率、计算费用、列出缺口、填写报告。','small'))),
 'Skill 封装可复用的任务方法；实际动作仍需要运行环境和工具。',
 'Skill 可以只有说明文件，也可以包含脚本等资料。它不是一种新模型，也不是必须通过微调安装进去。发现、启用和执行的渐进加载减少了不相关说明占用的上下文。具体能加载和执行哪些内容，取决于兼容的 Agent 客户端和环境。',('skills',))

add('17 / 更多模型能力','多模态：输入输出可以超出文字','模型支持哪些模态、哪些方向，要看具体规格。',
 table(['业务步骤','输入 / 输出','可能涉及的能力'],[
 ('读取发票或收据','图片 + 问题 → 字段或解释','视觉语言模型，必要时结合 OCR'),('记录口述差旅说明','音频 → 文字','语音识别或支持音频的多模态模型'),('语音播报报销结果','文字 → 音频','语音合成'),('理解长视频材料','视频帧 / 音频 → 摘要或回答','视频或多模态理解，处理方式依模型而异'),('生成插图或视频','文本 / 图像条件 → 图像或视频','图像、视频生成模型'),
 ]),
 '同一个应用可以组合多个模型和普通程序。',
 '前面一直用文本模型建立基本概念，现在扩展输入输出。图片如何编码到模型内部有不同架构，不要简单说所有内容都用同一种文本 Token。对业务而言先区分接收什么、产生什么，再看需不需要组合 OCR、视觉模型、语音模型和工具。')

add('17 / 更多模型能力','常见 AI 模型，在应用中的位置','有的模型生成内容，有的模型编码特征或判断相关性。',
 table(['模型或程序','常见输入与输出','在差旅应用里做什么'],[
 ('生成式语言模型','上下文 → 文本或结构化输出','解释制度、提出工具调用、撰写报告'),('Embedding 模型','文本等内容 → 向量','为问题和文档建立可比较的表示'),('Reranker','问题 + 候选片段 → 相关性评分','对检索候选重新排序'),('视觉 / 语音模型','图像、音频等 → 理解或生成结果','读取票据、转写说明、播报'),('普通业务程序','确定的参数 → 数据或执行结果','精确求和、查数据库、导出文件'),
 ]),
 '“用了 AI”可以是一条由不同模型和程序组成的处理链。',
 '这页把 RAG 出现过的 Embedding 和 Reranker 放回完整模型地图。它们不需要输出一段回答，任务和输出形式与生成模型不同。计算金额时也可以直接使用普通程序，并不要求每一步都由模型承担。并非所有 AI 模型都符合前面逐个生成文本 Token 的讲法，那个机制明确针对主流自回归文本生成。',('embedding','rag'))

add('回到整项任务','差旅助手的完整组成','用户只看到一次任务，系统内部可能经历多次模型调用、资料检索和工具执行。',
 table(['层次','本例中的组件','负责的事情'],[
 ('交互与任务目标','页面、任务说明、输出约定','收集地点、日期、费用，说明交付要求'),('决策与上下文','LLM、Prompt、会话与进度','依据当前信息选择回答或下一步行动'),('资料与能力','RAG、汇率 / 计算工具、票据识别','提供证据、实时数据和执行结果'),('连接与做法','直接接口 / MCP、Skill','接入能力，复用任务步骤与模板'),('运行与检查','Harness','维护状态、执行边界、预算和结果检查'),
 ])+note('交付示例：费用合计 1,196 元；住宿超标准 60 元；审批记录待补；附计算与制度依据。'),
 '能解释每个组件补了什么能力，就能读懂大多数 Agent 产品架构。',
 '回到开场的问题。一个完整任务并非模型输出一段文字就自然结束，还涉及资料、执行和检查。最终报告要写明一千一百九十六元是教学费用合计，不能直接把它当成已批准报销金额，因为住宿超标的审批还缺失。这也是为什么我们要把总金额、制度结论和业务完成分别判断。',('agents','harness','mcp','skills'))

add('回顾与交流','把名词放回它解决的问题','遇到新概念时，先定位它在模型、输入、资料、行动还是运行环境中。',
 table(['问题','对应概念'],[
 ('模型是什么，文件里装了什么？','AI / ML / DL / LLM；配置、权重、Tokenizer'),('怎样生成与对话？','Token、预训练、后训练、SFT、Chat template'),('怎样把任务与资料交给模型？','Prompt、Few-shot、Context、RAG、Embedding'),('怎样与外部系统交互？','Function Calling、Tool、MCP'),('怎样自主推进并持续工作？','Workflow、Agent、ReAct、Harness、Memory、Skill'),
 ])+note('交流题：如果模型给出了一条不存在的公司制度，应先从哪些环节排查？'),
 '检查信息来源、输入上下文、检索结果和输出依据，再决定怎样改进。',
 '可以用不存在的制度条款这个问题做收尾互动。可能没有提供资料，可能检索漏掉了正确条款，可能文档版本不适用，也可能模型没有正确使用已提供的资料。不要一上来就认定必须换模型、微调或加一个 Agent。请听众用这张表定位问题，再回到具体证据。')

add('附录 / 按需展开','一次用户任务的成本与效果','多次调用、长上下文和工具循环，会影响整项任务的时间与费用。',
 cols(block('时间与用量',p('一次任务可能包括多轮模型请求、检索、重排与工具调用。历史、工具定义和返回结果也会占用输入。')+p('流式输出可以边生成边展示，首个结果的等待时间与完整任务耗时不同。')+p('计费项、缓存和推理用量以具体服务的公开规则为准。','small')),
 block('怎样判断改进有效',p('用有明确判定标准的真实任务，分别检查制度引用、计算结果、工具成功、信息不足时的处理。')+p('同时比较整项任务正确率、延迟和成本；公开基准只能提供一部分参考。')+p('固定输入、模型与配置，再观察改动带来的效果。','small'))),
 '让“更强”对应到具体任务结果，而不是更多调用或更长的回答。',
 '这一页按时间选讲，避免打断主线。没有加入易过期的供应商价格。对于 Agent 应用，单次 Token 价格只是成本的一部分，一项任务有多少次调用、工具多慢、是否反复失败都很重要。评测不要只看语气顺不顺，金额和制度引用要有明确标准。',('agents','context'))

for title, keys in [
 ('参考资料：模型、文件与训练', ['llm','tokens','files','config','weight_index','safetensors','tokenizer','tokenizer_config','qwen','q8','q8awq','q8gguf','q30','q30fp8','q235','quant','awq','gptq','gguf','sft','rlhf','lora','distill','chat']),
 ('参考资料：检索、工具与 Agent',['context','vllm_api','rag','embedding','tools','agents','react','harness','mcp','skills'])
]:
 body='<div class="references">'+''.join(f'<a href="{SOURCES[k][1]}" target="_blank" rel="noopener">{SOURCES[k][0]}<small>{SOURCES[k][1].split("//")[1].split("/")[0]}</small></a>' for k in keys)+'</div>'
 add('附录 / 资料来源',title,'',body,'',
 'HTML 中可直接点击资料链接。各主题页的讲稿也附有对应来源。',keys,cls='reference-page')

add('附录 / 分享说明','资料与演示说明','',
 table(['项目','说明'],[
 ('分享场景','小组内部交流，面向 IT 从业者，无需机器学习背景。'),
 ('差旅案例','制度、金额、汇率、工具响应和 Embedding 示例数值均为教学设定。演示全程离线。'),
 ('分词与互动','Token 页用 tiktoken / cl100k_base，分词器文件页用 Qwen3-8B。逐步生成、聊天模板、工具调用和 ReAct 使用预写内容。'),
 ('模型资料','Qwen3-8B 文件清单摘录自官方仓库并重新排版。规格表选取官方公开版本，资料核对日期为 2026-11-18。'),
 ('两张插图','封面与 Dense/MoE 图由 AI 生成。Dense/MoE 图展示局部前馈层，采用四选二举例。'),
 ],'materials-table'),
 '',
 '本页集中记录内部分享、案例数据、互动和图文的来源。前两页有可点击的参考链接。')
