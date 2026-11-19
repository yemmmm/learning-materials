"""v0.5 slide content, speaker notes, and sources in presentation order."""
import html
from textwrap import indent

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

VLLM_REQUEST = r'''{
  "model": "Qwen/Qwen3-8B",
  "max_completion_tokens": 300,
  "messages": [
    {"role": "system", "content": "按给定差旅制度回答。"},
    {"role": "user", "content": "一晚花了 560 元，能全额报销吗？"},
    {"role": "assistant", "content": "超出 60 元。全额报销要看事前审批记录。"},
    {"role": "user", "content": "§3.2 上限 500 元/晚。§3.3 超标须事前审批。\n问题：两晚各花了 560 元呢？"}
  ]
}'''

def p(t, cls=''): return f'<p class="{cls}">{t}</p>'
def block(title, text, cls=''): return f'<div class="text-block {cls}"><h3>{title}</h3>{text}</div>'
def cols(*items, cls=''): return f'<div class="columns {cls}">' + ''.join(items) + '</div>'
def note(t): return f'<div class="annotation">{t}</div>'
def code(t, cls=''): return f'<pre class="{cls}"><code>{html.escape(t)}</code></pre>'
def table(headers, rows, cls=''): return f'<table class="{cls}"><thead><tr>'+''.join(f'<th>{x}</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{x}</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table>'
def flow(*steps): return '<ol class="flow">'+''.join(f'<li><b>{t}</b><span>{d}</span></li>' for t,d in steps)+'</ol>'
def image(name,alt,cls=''):return f'<figure class="{cls}"><img data-asset="{name}" alt="{html.escape(alt)}"></figure>'
def buttons(attr, labels, cls=''):return f'<div class="choices {cls}">'+''.join(f'<button class="choice {"selected" if i==0 else ""}" data-{attr}="{i}" aria-pressed="{str(i==0).lower()}">{v}</button>' for i,v in enumerate(labels))+'</div>'
def add(chapter,title,lead,body,takeaway,notes,sources=(),cls=''):
 SLIDES.append(dict(chapter=chapter,title=title,lead=lead,body=body,takeaway=takeaway,notes=notes.strip(),sources=list(sources),cls=cls))

add('开场', '大模型常见概念', '以公司差旅助手为例，理解语言模型怎样生成回答，应用怎样把回答变成可核对的结果。',
    cols('<div class="cover-copy cover-agenda">'
         + block('模型怎样运行', p('从模型文件和分词，看到逐步生成与训练。'))
         + block('一次回答需要什么', p('沿一条对话请求查看指令、制度和工具结果。'))
         + block('助手怎样做完一项任务', p('比较固定流程和 Agent，最后核对同一笔报销。'))
         + p('v0.5 · 2026 年 11 月', 'small') + '</div>',
         image('model-workbench.png', '由资料、计算器、终端和模型组成的纸艺插图'),
         cls='cover-columns'),
    '',
    '今天用一笔报销任务理解常见的大模型概念。先看模型的文件怎样支撑生成和部署，再看模型接收到的对话与资料。最后沿着工具执行的结果，看固定流程和 Agent 分别怎样推进任务。整场用同一笔费用收尾。',
    cls='cover')

add('开场', '这笔差旅费可以全额报销吗？', '费用发生于 2026-11-08，包括一晚 560 元住宿和一笔 120 新币费用。',
    cols('<div class="document-paper">'
         + p('助手的初次回答', 'kicker')
         + '<h3>“住宿上限是每晚 600 元，这笔可以全额报销。”</h3>'
         + p('回答只给出了结论。用户看不到制度版本、换算过程或审批记录。')
         + '</div>',
         block('交给财务前，需要回答哪些问题？',
               p('<b>住宿</b>　适用的每晚标准是多少？')
               + p('<b>外币</b>　120 新币按哪一天的汇率折算？')
               + p('<b>审批</b>　如果住宿超出标准，是否有事前审批？')),
         cls='case-comparison'),
    '公司制度、金额与后续工具结果均为离线教学设定。',
    '先请大家找出需要核实的说法。这个回答看起来很顺，但它没有解释 600 元的来源，也没有处理外币和审批。记住 560 元和 120 新币，后面用相同材料交付一份核对说明。现在先定位给出这句回答的模型。')

add('01 / 模型是什么', 'AI、机器学习与大语言模型', '左侧表示常见技术路线，右侧定位我们讨论的文本生成模型。',
    cols('<div class="taxonomy"><div><b>人工智能 AI</b><span>让计算机完成需要智能的任务</span>'
         '<div><b>机器学习 ML</b><span>从数据中学习规律</span>'
         '<div><b>神经网络</b><span>训练相互连接的计算单元</span>'
         '<div><b>深度学习 DL</b><span>用多层神经网络学习表示</span></div></div></div></div></div>',
         '<div>'
         + block('大语言模型 LLM', p('现代大语言模型通常用大规模数据和深度神经网络训练。这里以基于 Transformer 的自回归文本模型为例。'))
         + block('两个观察维度', p('语言模型按建模对象命名，早期也有统计语言模型。深度学习描述实现方法，应用范围还包括图像和语音。'))
         + '</div>'),
    '',
    '左边从大范围到具体技术路线，AI 还包括规则、搜索等方法，机器学习也有其他算法。我们主要讨论现代语言模型的文本生成机制。下一页从技术换到工作对象，看同一个语言模型能处理哪些语言任务。',
    ('llm',))

add('01 / 模型是什么', '语言模型能处理哪些文本任务？', '自然语言处理（NLP）是任务领域。同一个 LLM 可以根据输入要求完成多种任务。',
    table(['任务', '输入示例', '期望输出'], [
        ('分类', '“这张发票什么时候能报？”', '报销咨询'),
        ('信息抽取', '“在上海住了两晚，共 980 元。”', '上海、2 晚、980 元'),
        ('翻译与摘要', '一封英文差旅邮件', '中文译文，或审批要求和截止日期'),
        ('问答与生成', '“按这条规定解释超标原因，并起草说明。”', '带制度依据的书面说明'),
    ]),
    '',
    '横着看信息抽取这一行。程序交给模型一段文字并要求固定字段，处理的结果可以给下一步使用。这和直接问模型一个开放问题是不同的任务形式。开发者要用到这些能力，通常有两种接入路线。',
    ('llm',))

add('02 / 使用方式与模型文件', '托管 API 与自行部署', '应用发送问题与参数。两条路线的区别在于谁运行模型服务。',
    table(['工作', '托管 API', '自行部署'], [
        ('服务在哪里', '供应商运行模型，应用调用其接口', '团队在自管设备或云算力上运行模型'),
        ('模型怎样上线', '供应商选定模型版本并维护服务', '团队取得权重，用推理框架加载并提供 API'),
        ('团队负责什么', '业务逻辑、输入数据与调用用量', '业务逻辑、输入数据，以及算力、并发和运维'),
        ('同一个开放权重模型', '可调用供应商已经托管的服务', '也可以在自己管理的环境中加载'),
    ]),
    '准备自行部署时，先确认权重是否可获得，以及许可证允许怎样使用。',
    '对普通用户，聊天网页是另一种入口。对开发应用的人，重点是责任如何分配。自行部署的设备可以是自己的工作站，也可以是自管的云 GPU。选择自行部署时，接下来要查模型公开了哪些材料。',
    ('qwen',))

add('02 / 使用方式与模型文件', '开放权重、训练资料与使用许可', '拿 Qwen3-8B 仓库举例。下载运行、复现训练、使用和分发需要分别核对。',
    table(['你要做什么', '要看的材料', '怎样判断'], [
        ('运行已有模型', '模型权重、结构配置与分词器', '文件能否下载，推理框架是否支持该结构'),
        ('复现训练过程', '训练代码、训练数据与训练细节', '材料是否完整公开，数据是否可以取得'),
        ('商用或分发', '模型许可证', '确认使用、修改、再分发的具体条款'),
    ]) + note('Qwen3-8B 的仓库提供权重和配置，模型卡标注 Apache 2.0。需要哪些训练材料，应当另查发布说明。'),
    '',
    '口头说“开源模型”时，可能有人专指权重开放。看实际交付会更清楚。权重用于运行，训练信息关系到复现，使用和再分发需要核对许可。本例的模型仓库里已经有运行所需的主要文件，下一页打开看看。',
    ('qwen', 'q8', 'files'))

add('02 / 使用方式与模型文件', '模型仓库的三类文件', '从 Qwen3-8B 官方仓库摘录，按加载模型时的用途分组。',
    table(['类型', '真实仓库中的文件', '加载时的用途'], [
        ('配置', '<code>config.json</code><br><code>generation_config.json</code>',
         '声明模型结构，也可以提供默认生成设置。'),
        ('权重与分片索引', '<code>model-00001-of-00005.safetensors</code><br><code>model.safetensors.index.json</code>',
         '分片保存训练得到的张量。索引记录每个张量所在的分片。'),
        ('分词器', '<code>tokenizer.json</code>、<code>tokenizer_config.json</code><br><code>vocab.json</code>、<code>merges.txt</code>',
         '定义文本与 Token ID 如何转换，以及怎样处理特殊标记。'),
    ], 'file-table'),
    '顺着一次输入往下看，最先需要的是分词器。',
    '这不是仓库的完整列表。权重有五个分片，表里只列一个。配置、权重、分词器是理解加载过程的三个入口，具体文件名和组合会随模型变化。先看分词器怎样给一段文字编码，随后再回头看加载时配置和权重如何配合。',
    ('files', 'safetensors', 'tokenizer_config'))

add('03 / 分词、生成与加载', 'Token 与 Token ID', '分词器先切分文本，再把各片段换成词表中的整数编号。本页使用 cl100k_base。',
    '<div class="screen-only">'
    + buttons('token', ['中文', '英文', '代码'])
    + '<div class="token-demo"><div class="example-head"><b id="tokenText">今天开会。</b>'
      '<span id="tokenCount">__TOKEN_COUNT__ 个 Token</span></div>'
      '<div class="token-list" id="tokenPieces">__TOKENS__</div></div></div>'
    + '<div class="print-only token-print">__TOKEN_PRINT__</div>'
    + cols(block('怎样读分词结果', p('每格显示一个 Token 及其编号。␠ 表示片段里包含空格。')),
           block('模型收到的内容', p('模型按这串编号取得对应的向量表示。字数与 Token 数没有固定换算关系。'))),
    '',
    '【演示】依次切换中文、英文和代码。英文示例中空格跟着 world 进入一个 Token，代码中的标点有自己的切法。Token 可能是词、词的一部分、标点，或字符的部分字节。编号序列交给模型后，就可以演示怎样计算下一步。',
    ('tokens',), cls='token-page')

add('03 / 分词、生成与加载', '逐个 Token 生成文本', '每一步用当前序列和模型参数计算候选概率，再按解码策略选一个 Token。',
    cols('<div><div class="screen-only">'
         '<div class="generation" id="generationText">The hotel bill was</div>'
         + buttons('generate', ['初始输入', '第一个 Token', '第二个 Token'])
         + '<p class="generation-detail" id="generationDetail"></p></div>'
           '<div class="print-only generation-sequence">'
         + p('<b>初始输入</b> The hotel bill was')
         + p('<b>第 1 步</b> The hotel bill was <mark>¥</mark><small>ID 72588，含前导空格</small>')
         + p('<b>第 2 步</b> The hotel bill was ¥<mark>560</mark><small>ID 17698</small>')
         + '</div></div>',
         '<div>'
         + block('下一步能看到什么', p('第二步的输入比起最初多了货币符号。新生成的 560 也会接回序列，作为后续生成的前文。'))
         + block('何时结束', p('模型可以生成结束标记，服务也可以按输出长度等条件停止。'))
         + '</div>',
         cls='generation-columns'),
    '续写结果为教学预设。高亮部分已用 cl100k_base 核对，每步新增一个 Token。',
    '【演示】点第一个 Token，再点第二个。请大家指一下追加 560 时，模型比最初多看到了什么。实际生成时，候选分布由整个当前输入与已加载的权重共同计算。下一页把“权重从哪里来”和“现在怎样用权重”分开。',
    ('llm', 'tokens'), cls='generation-page')

add('03 / 分词、生成与加载', '训练与推理', '以报销问答为例，训练调整参数，推理使用已经加载的参数。',
    table(['', '训练 Training', '推理 Inference'], [
        ('输入', '多条问题与示范回答，配合训练目标', '本次问题、示例、历史和适用制度'),
        ('执行过程', '根据训练信号调整可训练参数', '按输入逐步计算并生成输出'),
        ('结果', '一份模型权重，或可以加载的适配器权重', '一次回答、结构化数据或工具调用请求'),
        ('差旅示例', '让模型学习指出超标金额并询问审批', '带入本次规定，回答一晚 560 元能否全额报销'),
    ]) + note('LoRA 用于参数高效微调。可以冻结原权重，只训练额外的低秩适配参数。'),
    '将本次制度放入消息，是为这次推理提供信息。训练才会调整可训练参数。',
    '模型供应方和应用团队都可能做训练。LoRA 这类方法回答的是微调时更新哪些参数。日常调用 API 时做的是推理，当前输入会影响输出。下一页从推理框架的角度，看配置和权重怎样组成一个可运行的模型。',
    ('llm', 'sft', 'lora'))

add('03 / 分词、生成与加载', '配置和权重怎样装进模型？', '以 Qwen3-8B 为例，模型实现定义计算，配置声明张量形状，索引定位权重分片。',
    cols('<div>' + p('config.json 节选', 'code-label')
         + code('''"model_type": "qwen3",
"num_hidden_layers": 36,
"hidden_size": 4096,
"vocab_size": 151936''')
         + p('框架找到 Qwen3 实现，按配置构建 36 层。输入词嵌入矩阵的形状为 151,936 × 4,096。')
         + '</div>',
         '<div>' + p('model.safetensors.index.json 里的 weight_map', 'code-label')
         + code('''"model.embed_tokens.weight":
  "model-00001-of-00005.safetensors",
"lm_head.weight":
  "model-00005-of-00005.safetensors"''')
         + p('框架按张量名从分片加载权重。这个例子中，输入词嵌入在第 1 片，输出层在第 5 片。')
         + '</div>', cls='loading-columns')
    + note('Safetensors 保存张量值，以及数据类型、形状与字节位置。推理所需的计算逻辑由模型实现提供。'),
    '',
    '先指配置里的类型和两个维度，再指索引里的词嵌入名称。框架用模型类定义计算，按名称从权重文件加载数值。Token ID 恰好对应输入词嵌入矩阵的一行。要让这个匹配成立，应用得使用该模型对应的分词器。',
    ('config', 'weight_index', 'safetensors'))

add('03 / 分词、生成与加载', '同一段文字在不同分词器中的编号', '给两种分词器相同的英文输入。这个例子的切分相同，得到的部分 ID 不同。',
    table(['分词器', '输入 Hello, world! 的切分', 'Token ID 序列'], [
        ('cl100k_base', '<code>["Hello", ",", " world", "!"]</code>', '<code>[9906, 11, 1917, 0]</code>'),
        ('Qwen3-8B', '<code>["Hello", ",", " world", "!"]</code>', '<code>[9707, 11, 1879, 0]</code>'),
    ])
    + cols(block('规则和词表', p('Qwen3-8B 的 <code>tokenizer.json</code> 封装规则和词表。<code>vocab.json</code> 与 <code>merges.txt</code> 分别列出词表映射和 BPE 合并规则。')),
           block('聊天边界也有编号', p('<code>&lt;|im_start|&gt;</code> 是 151644，<code>&lt;|im_end|&gt;</code> 是 151645。特殊 Token 和聊天模板可在 <code>tokenizer_config.json</code> 中查看。'))),
    '输入 ID 要与模型的词嵌入矩阵对应。部署时使用与模型匹配的分词器。',
    '比较 Hello 的 9906 和 9707，即使切分看起来一样，编号也依赖词表。后面讲聊天模板时，这两个对话边界会再次出现。现在输入已经能变成模型所需的编号，接下来读模型规格，关注参与计算的参数规模。',
    ('tokens', 'tokenizer', 'tokenizer_config', 'files'))

add('04 / 模型规格与推理服务', 'Dense 与 MoE 的前馈层', '同样处理一个 Token，两种架构选择前馈层参数的方式不同。',
    cols(image('dense-moe.png', 'Dense 使用共享前馈网络，MoE 的路由从四个专家中选中两个', 'moe-figure'),
         '<div>'
         + block('Dense（稠密模型）', p('每个 Token 经过该层时，都使用同一组前馈参数。'))
         + block('MoE（混合专家模型）', p('路由为当前 Token 选择部分专家参与计算。其他专家的权重仍需保留，以供其他 Token 选择。'))
         + p('图中展示的是局部前馈层。右侧用四选二演示，绿色标出本次参与的专家。', 'small')
         + '</div>', cls='moe-columns'),
    '总参数量关系到要存多少权重，激活参数量描述处理一个 Token 时用到的参数规模。',
    '左图的 FFN 是前馈网络。右图中的专家是子网络，路由按 Token 选中一部分。四选二是教学示意，Qwen3-235B-A22B 的模型卡列的是 128 个专家、每 Token 激活其中 8 个。读模型名时，先分别找总参数量和激活参数量。',
    ('q235', 'qwen'), cls='moe-page')

add('04 / 模型规格与推理服务', '模型名里的参数量与数值格式', '用 Qwen3-30B-A3B-FP8 练习读规格。',
    '<div class="model-name" aria-label="Qwen3-30B-A3B-FP8">'
    '<span>Qwen3<small>模型家族</small></span><i>－</i>'
    '<span>30B<small>约 300 亿总参数</small></span><i>－</i>'
    '<span>A3B<small>每 Token 激活约 30 亿参数</small></span><i>－</i>'
    '<span>FP8<small>8 位浮点权重版本</small></span></div>'
    + cols(block('每个权重值占多少位', p('<b>32 位</b>　FP32，4 字节<br><b>16 位</b>　FP16、BF16，2 字节<br>'
              '<b>8 位</b>　FP8、INT8，1 字节<br><b>4 位</b>　INT4，两个值可打包进 1 字节')),
           block('用位宽估算权重体积', p('按 80 亿个权重值粗算：') +
                 p('<b>16 位</b>　约 16 GB<br><b>4 位</b>　约 4 GB') +
                 p('实际存储还与量化元数据等有关，运行还要给 KV Cache 等留空间。', 'small'))),
    '量化使用较低位宽表示权重，可减少文件体积和权重占用。',
    'B 表示十亿，型号写的是约数。官方模型卡给出总参数 30.5B、激活参数 3.3B。FP16 与 BF16 虽然位宽相同，可表示范围和精度的取舍不同。这页用统一位宽粗估纯权重的十进制 GB。下一页把这个估算与具体发布文件对照。',
    ('q30', 'q30fp8', 'quant'))

add('04 / 模型规格与推理服务', '同一模型的原始权重与量化版本', '先按同一模型横向比较，再看它以什么格式发布。',
    table(['官方发布', '总参数 / 激活参数', '主要权重表示', '存储格式'], [
        ('Qwen3-8B', '8.2B（Dense）', 'BF16（16 位）', 'Safetensors'),
        ('Qwen3-8B-AWQ', '8.2B（Dense）', 'AWQ（4 位）', 'Safetensors'),
        ('Qwen3-8B-GGUF', '8.2B（Dense）', 'Q4_K_M（以 4 位为主）', 'GGUF'),
        ('Qwen3-30B-A3B', '30.5B / 3.3B（MoE）', 'BF16（16 位）', 'Safetensors'),
        ('Qwen3-30B-A3B-FP8', '30.5B / 3.3B（MoE）', 'FP8（8 位）', 'Safetensors'),
    ], 'model-table')
    + note('AWQ、GPTQ 是量化方法。GGUF 是文件格式，Q4_K_M 是其中的一种量化规格。本例的 Q4_K_M 文件为 5.03 GB。'),
    '选择权重文件时，还要确认推理框架支持对应架构、量化方法和文件格式。',
    '指前两行的参数规模。量化改变数值表示，同一发布系列的参数规模保持一致。AWQ 借助激活统计保护重要权重，GPTQ 用校准数据逐层减小误差。实际部署可以先看框架是否支持模型和文件，再用业务样例核对量化效果。',
    ('q8', 'q8awq', 'q8gguf', 'q30', 'q30fp8', 'awq', 'gptq', 'gguf'))

add('04 / 模型规格与推理服务', '推理框架与服务接口', '服务启动时加载模型。每次调用时，接口接收应用请求并返回推理结果。',
    '<div class="pipeline-row"><b class="lane-label">启动服务</b>'
    + flow(('准备文件', '配置、权重与分词器'), ('框架加载', '构建模型并装入权重'), ('开放接口', '应用可以调用本服务')) + '</div>'
    + '<div class="pipeline-row"><b class="lane-label">处理请求</b>'
    + flow(('接收消息', '例如一条住宿核对问题'), ('执行推理', '编码输入，生成并解码'), ('返回输出', '由应用解析和展示')) + '</div>'
    + note('<b>常见框架</b>　Transformers 提供模型实现、加载和生成接口。vLLM、SGLang 可提供并发推理服务。llama.cpp 常用于本地运行 GGUF 模型。'),
    '',
    '第一条是启动服务时做的事，第二条随请求反复发生。自部署应用照样可以用 API 请求模型服务。到这里模型能运行了，接下来看训练怎样让续写模型按用户要求回答。',
    ('files', 'qwen', 'vllm_api'))

add('05 / 训练与对话', '预训练与监督微调', '预训练学习续写。后训练中的监督微调（SFT）用任务输入和示范回答塑造作答方式。',
    cols(block('预训练看什么', p('大规模文本中的前文与后续 Token。')
               + '<div class="document-paper">' + p('教学片段', 'kicker') +
               p('前文　员工在适用城市出差，住宿标准为每人每晚') +
               p('<b>训练目标</b>　预测后续 Token，例如组成“500 元”的片段。') + '</div>'),
         block('SFT 看什么', p('成对的任务指令、问题和示范答案。')
               + '<div class="document-paper">' + p('教学样本', 'kicker') +
               p('问题　按给定制度，一晚 560 元能全额报销吗？') +
               p('<b>示范回复</b>　超出 60 元。需提供事前审批记录。') + '</div>'),
         cls='training-examples')
    + note('示范可以由人编写。蒸馏的一种做法，是用教师模型的输出来训练学生模型。'),
    '',
    '左侧演示“继续写”，右侧演示“按任务要求回答”。两边都在训练，训练目标和给定的样本不同。后训练还包括基于偏好的方法。下一页保留同一个报销问题，请人比较两个候选回答。',
    ('llm', 'sft', 'distill'), cls='training-page')

add('05 / 训练与对话', 'RLHF 怎样使用人类偏好？', '人类反馈强化学习（RLHF）的 InstructGPT 示例。问题仍是“一晚花了 560 元，能全额报销吗？”',
    table(['候选回答', '人工排序', '理由'], [
        ('A　超出 60 元。全额报销要看事前审批记录。', '第 1', '算出超额，并指出审批条件'),
        ('B　可以全额报销。', '第 2', '缺少支持全额报销的依据'),
    ])
    + flow(('收集偏好', '让标注者在同一问题下对候选回答排序。'),
           ('训练奖励模型', '用排序教奖励模型给 A 这样的回答打更高分。'),
           ('更新助手', '经 SFT 的助手生成新回答，依据奖励分数用强化学习更新。')),
    '这条路线先训练评分模型，再用评分调整生成回答的模型。',
    '这里示范的是 InstructGPT 的做法。监督微调先给出一个能按指令作答的助手。人工排序得到偏好数据，奖励模型学习打分，接着给助手的新回答评分，并用 PPO 等强化学习步骤更新助手。线上使用时输入的消息怎样对应训练时见过的角色和回复？接下来打开一个对话请求。',
    ('sft', 'rlhf'))

add('05 / 训练与对话', '聊天模板与多轮对话', '用同一段差旅问答对照 SFT 样本和在线请求。训练样本带示范回复，推理从 assistant 起始标记继续生成。',
    buttons('chat', ['第一轮推理', '加入第二轮'], cls='screen-only')
    + p('右侧展示第二轮。高亮标出带回的上一轮回复与本轮生成起点。', 'print-only small')
    + cols('<div>' + p('训练 · 带示范回复的 messages', 'code-label')
           + '<pre class="chat-code" id="chatMessages"></pre>'
           + p('样本里的 assistant 消息提供示范。') + '</div>',
           '<div>' + p('推理 · 编码为 ChatML 风格序列', 'code-label')
           + '<pre class="chat-code screen-only" id="chatRaw"></pre>'
             '<pre class="chat-code print-only" id="chatRawPrint"></pre>'
           + p('角色和边界标记帮助模型辨认各段消息。') + '</div>'),
    '第二轮把相关历史带回模型，“两晚各花了 560 元”仍沿用上一轮的话题。',
    '【演示】先指左侧 assistant 的示范回复，再指右侧第一轮推理的生成起点。点“加入第二轮”，观察原来的回复怎样进入历史。边界符号与前面分词器页相呼应。这是简化的 ChatML 风格示例，实际服务使用部署模型匹配的模板。现在回到开场，看看一次自然的对话仍可能漏掉哪些核对依据。',
    ('sft', 'chat', 'tokenizer_config'), cls='chat-page')

add('06 / 模型到应用', '差旅回答中的三个核对缺口', '回看开场的初次回答。模型能写出流畅结论，这笔报销仍需要外部证据和计算结果。',
    table(['要核对的事实', '仅凭已有输入的风险', '应补充的依据'], [
        ('适用的住宿标准', '编造 600 元上限（幻觉），或沿用过期规定', '当前有效的条款、版本与适用范围'),
        ('120 新币的折算结果', '凭印象给出汇率，或在乘法中算错', '指定日期的汇率记录和程序计算结果'),
        ('本次是否有事前审批', '根据一般规则猜测本次已经批准', '可核验的审批记录，或明确标为待补'),
    ]),
    '带入正确资料后，还需要检查答案是否真的用了适用依据。',
    '编造制度上限是幻觉的一种表现。训练知识过时、模型看不到内部材料、算错金额，都是实际使用时要区分的问题。后续出现的检索和工具会补齐这些信息。先画出最小应用，确认问题和已提供的材料怎样到达模型。',
    ('rag', 'context'))

add('06 / 模型到应用', '一个最小的差旅问答应用', '假设用户已粘贴住宿条款。沿同一次请求，区分应用和模型各负责什么。',
    flow(('用户输入', '“一晚 560 元能全额报吗？”并粘贴条款。'),
         ('应用组装请求', '写入任务规则、当前问题和用户给出的条款。'),
         ('模型生成', '从条款得出超标金额，并说明审批条件。'),
         ('应用处理输出', '检查字段和依据，把答复交给用户。'))
    + cols(block('模型提供的能力', p('使用本次收到的消息生成答复。')),
           block('应用保存和管理的内容', p('保存会话，准备下一轮输入，并按业务要求校验输出。'))),
    '',
    '这个最小版本没有自动查制度，用户把条款给了应用。界面、会话、资料和校验由应用管理，模型处理的是实际发送给它的输入。在第二步，任务要求怎样写，决定了回答能否被程序直接检查。',
    ())

add('06 / 模型到应用', '提示词里的目标、约束与示例', '把一段报销描述变成应用可读取的字段。先规定提取什么，再用示例说明输出。',
    cols('<div>' + p('模糊要求', 'code-label') + code('帮我看一下这些费用，整理好。')
         + p('城市、晚数和金额是否都要提取？原文没写晚数时应该怎么填？')
         + p('按右侧的要求，本次应得到', 'code-label special-token-label')
         + code('{"city":"北京","nights":null,"amount":450}') + '</div>',
         '<div>' + p('清楚的任务要求与 Few-shot 示例', 'code-label')
         + code('''目标：提取城市、晚数、金额（人民币元）。
约束：只用原文。缺失字段填 null。
格式：返回 JSON，字段见示例。

示例输入：上海住两晚，共 980 元。
示例输出：
{"city":"上海","nights":2,"amount":980}

本次输入：北京住宿花了 450 元。''') + '</div>'),
    'Few-shot 把少量示例放进本次输入，说明输出长什么样。',
    '请大家先说左边的“整理好”可能有几种理解，再看右边怎样指定缺失值和输出字段。Few-shot 这些示例会和指令一起进入本次上下文。SFT 则以样本为训练输入，调整参数。应用要回答整个报销问题，还需要挑选历史和证据。',
    ('context', 'sft'))

add('06 / 模型到应用', '上下文工程要选择哪些信息？', '应用可能持有完整会话和文档。上下文工程决定每一次实际送入模型的内容。',
    table(['信息', '本轮应当带什么', '选择规则'], [
        ('任务指令', '按给定制度核对，明确列出缺件', '保留任务约束和当前输出要求'),
        ('会话历史', '上一轮是一晚 560 元的住宿问题', '追问依赖的事实和回复应当带回'),
        ('外部资料', '适用住宿标准和超标审批条款', '选相关段落，保留版本与出处'),
        ('工具说明与返回', '查汇率工具；执行后带回汇率、日期和状态', '按任务阶段提供可用工具和实际结果'),
    ]),
    '',
    '上一页的提示词仍是这里的任务指令。除此之外，应用要决定什么时候带历史、条款或者工具结果。比如本轮只讨论住宿，可以舍去无关的机票记录。下一页把这些选择放进一条具体请求，并看看窗口大小的影响。',
    ('context',))

add('06 / 模型到应用', '一次对话请求的上下文窗口', '第二轮追问“两晚各花了 560 元呢？” 应用带上相关历史和两条住宿规定。',
    '<div>' + p('vLLM · POST /v1/chat/completions', 'code-label')
    + '<div class="context-strip">'
      '<div><b>任务指令</b><span>按给定差旅制度回答</span></div>'
      '<div><b>相关历史</b><span>上一轮一晚 560 元<br>已算出超标 60 元</span></div>'
      '<div><b>条款和本轮问题</b><span>每晚 500 元，超标须事前审批<br>两晚各花 560 元</span></div>'
      '<div><b>生成上限</b><span>最多 300 个 Token</span></div></div>'
    + p('前三格是本次 messages 的内容。模板编码后的输入与输出共用窗口，分块宽度仅为示意。') + '</div>'
    + note('如果输入太长，可以筛掉无关历史，保留原始条款和本轮任务所需事实。完整请求体见本页讲稿。'),
    '按给定的每晚标准，住宿两晚共花 1,120 元，超标 120 元。审批仍需核验。',
    '沿图从左到右看，前三块编码为输入 Token。请求参数 max_completion_tokens 为 300，这是本次生成的上限。窗口内既要留出输入，也要有生成空间。这里明确两晚各花了 560 元，才可以逐晚核对标准。请求中的原始条款从哪里找？下一节介绍检索。\n\n完整请求体\n\n' + indent(VLLM_REQUEST, '    '),
    ('context', 'vllm_api', 'chat'))

add('07 / RAG 与检索', 'RAG 的资料准备和回答流程', '检索增强生成（Retrieval-Augmented Generation）在回答前查找相关资料，并把片段交给模型。',
    '<div class="pipeline-row"><b class="lane-label">准备资料</b>'
    + flow(('解析与切分', '把制度按章节或条款切成片段。'),
           ('建立索引', '用关键词、向量或两种方式索引片段。'),
           ('保留出处', '让每个片段能追到原文、版本与位置。')) + '</div>'
    + '<div class="pipeline-row"><b class="lane-label">回答问题</b>'
    + flow(('找候选条款', '从住宿问题召回相关片段，筛选和排序。'),
           ('组装上下文', '把适用条款与用户问题放进请求。'),
           ('生成并引用', '根据摘录回答，标出支持结论的出处。')) + '</div>'
    + note('制度更新时，可以更新索引和资料。把片段带进本次回答通常无需修改生成模型权重。'),
    '',
    '顺序是先备好可检索的资料，再在收到住宿问题时选择适用片段。索引支持的检索方式可以不同，向量数据库只是可能的实现之一。下一页先区分前面看到的 Token ID 和这里用于检索的向量。',
    ('rag', 'embedding'))

add('07 / RAG 与检索', 'Token ID 与 Embedding 向量', 'Token ID 标识词表中的一个片段。Embedding 用一组数表示内容特征。',
    table(['', 'Token ID', 'Embedding 向量'], [
        ('形式', '一个整数，例如 cl100k_base 中 Hello 的 9906', '一组数，例如 [0.12, −0.34, …]（示意）'),
        ('编号或数值接近', '9906 和 9907 的编号相邻，仅表示词表位置相邻', '用同一模型和合适度量时，可以比较表示的相似性'),
        ('在应用中的用法', '用编号查语言模型内部的 Token 向量', '用检索模型生成问题和段落的向量，以召回相似文段'),
    ], 'embedding-page')
    + note('查词嵌入矩阵的一行，是语言模型的内部步骤。为检索整段制度生成向量，是另一项任务。'),
    '把“住酒店”和“住宿标准”分别编码成检索向量，可以按语义相关性召回候选。',
    '前面同一个 Hello 在两套词表里的整数不同，这里利用它说明 ID 的作用。整数大小和语义远近没有对应关系。检索模型的输出通常有很多维，按模型支持的方式比较问题与文档向量。下一页让召回和重排各做一步。',
    ('tokens', 'embedding'))

add('07 / RAG 与检索', '检索候选与重排', '查询“2026 年 11 月出差住酒店，最多能报多少？” 看两份候选怎样进入下一步。',
    cols('<div class="retrieval-example">'
         + block('召回：先找到可能相关的片段',
                 p('<b>向量</b>　“住酒店”与“住宿标准”措辞不同，可以按语义召回。')
                 + p('<b>关键词</b>　查“§3.2”等明确编号时，直接匹配文字。')
                 + p('<b>混合</b>　可合并两类结果，再送入下一步。'))
         + '</div>',
         '<div><h3>重排：再看哪条最能回答问题</h3>'
         + '<div class="document-hit"><b>优先　《差旅费用管理办法》§3.2</b>'
           '<p>直接给出住宿标准，仍要确认 v2026.11 是否适用。</p></div>'
           '<div class="document-hit muted-hit"><b>靠后　《市内交通报销指南》</b>'
           '<p>同样谈差旅报销，内容针对交通费。</p></div>'
         + '</div>', cls='retrieval-columns'),
    'Reranker 按相关性调整候选顺序。条款版本和适用范围还需要核对。',
    '召回适合在大量文档中找一批候选，重排再逐个比较问题与候选片段。这里没有实时评分，排序是为了讲清过程。找到住宿条款后，先看原文是否支持要写入回答的事实。',
    ('embedding', 'rag'))

add('07 / RAG 与检索', '制度条款怎样支持报销结论？', '找到两段适用条款后，将规则、计算和还缺的材料逐项对应。',
    cols('<div class="document-paper">'
         + p('差旅费用管理办法 · v2026.11', 'kicker')
         + '<h3>适用条款摘录</h3>'
         + p('<b>§ 3.2 住宿标准</b><br>员工在适用城市出差，住宿标准为每人每晚 500 元。')
         + p('<b>§ 3.3 例外情况</b><br>超标准费用须提供事前审批记录。')
         + p('教学制度 POLICY-DEMO', 'small') + '</div>',
         '<div>'
         + block('§ 3.2 支持金额结论', p('一晚 560 元减去标准 500 元，<b>超标 60 元</b>。'))
         + block('§ 3.3 给出例外条件', p('要确认是否可以全额报销，还需要核验事前审批记录。当前材料未提供。'))
         + '</div>', cls='case-comparison'),
    '核对引用时，应能从条款原文找到支持该项结论的规则。',
    '请大家指一下这两个结论分别来自哪条规定。模型拿到相关片段后仍可能解释错误，引用链接也要与具体主张相对应。住宿能核对到这个程度，还有一笔 120 新币，需要查本次适用的汇率并计算。',
    ('rag',))

add('08 / 工具与自主决策', 'Function Calling 的调用请求', 'Tool 是应用可调用的能力。应用提供工具说明，模型按说明生成名称和参数。',
    cols('<div>' + p('应用提供的工具说明', 'code-label')
         + code('''name: get_exchange_rate
description: 查询指定日期的币种换算率。
parameters:
  base: string   # 原币种
  quote: string  # 目标币种
  date: string   # YYYY-MM-DD''') + '</div>',
         '<div>' + p('模型为这笔费用提出的调用', 'code-label')
         + code('''{
  "name": "get_exchange_rate",
  "arguments": {
    "base": "SGD",
    "quote": "CNY",
    "date": "2026-11-08"
  }
}''') + '</div>')
    + note('参数里的日期来自本例的费用日期。实际使用哪一天的汇率，由适用制度决定。'),
    '运行环境接到调用请求后执行工具，再把成功结果或错误返回给模型。',
    '指一下左边的参数定义，再看右边的参数是怎样从一笔外币费用得到的。此时只看到模型提出的请求。查询和计算是后面由应用完成的两次往返，下一页沿着调用结果看下去。',
    ('tools',))

add('08 / 工具与自主决策', '两次工具调用完成一次换算', '按 2026-11-08 的教学汇率，把 120 SGD 换算为人民币。',
    buttons('tool', ['提出查询', '得到汇率', '请求并执行计算', '生成答复'], cls='screen-only')
    + '<div class="screen-only">'
    + cols('<div class="tool-demo"><div><h3 id="toolTitle">模型提出查询</h3><pre id="toolResult"></pre></div></div>',
           block('回执里需要核对什么',
                 p('<b>查汇率</b>　确认返回的日期、币种和换算率。')
                 + p('<b>算金额</b>　结合请求参数，核对乘积和成功状态。')),
           cls='tool-columns') + '</div>'
    + '<div class="print-only">'
    + table(['步骤', '模型与应用怎样交接', '这一步得到什么'], [
        ('查询请求', '模型生成币种和日期，由应用接收', 'SGD / CNY，2026-11-08'),
        ('查询返回', '应用执行并把工具结果送回模型', '1 SGD = 5.30 CNY，status: ok'),
        ('计算请求和返回', '模型请求乘法，应用执行并返回数值', '120 × 5.30 = 636 CNY，status: ok'),
        ('答复', '模型根据两个工具结果组织文字', '120 新币折合 636 元，附汇率日期'),
    ], 'print-steps')
    + note('应当能从日志找到两次实际返回，核对汇率日期、币种、计算结果，以及工具是否执行成功。')
    + '</div>',
    '',
    '【演示】依次点击四步。请大家指出谁提出查询、谁实际执行，以及输出中的 636 来自哪里。教学数据已预写。应用可以把这个顺序固定下来，也可以在完成换算后，根据已经取得的结果选择要查的下一项。',
    ('tools',), cls='tool-page')

add('08 / 工具与自主决策', 'Workflow 与 Agent 的决策分工', '同一笔报销，需要查规定、换算金额、判断是否还要核验审批。',
    cols(block('Workflow · 程序预先编排',
               p('开发者规定主要步骤和分支。运行时按已写好的条件走。')
               + flow(('查制度', '取得条款'),
                      ('做换算', '按指定日期查询'),
                      ('检查审批', '按规则出说明'))
               + p('例如程序写明：住宿超标且没有审批记录，就在说明里标记待补。', 'small')),
         block('Agent · 模型根据执行反馈选择',
               p('模型根据目标和当前状态，在允许的工具与动作中选下一步。')
               + flow(('判断缺口', '已算出超标额'),
                      ('选取动作', '例如核验审批'),
                      ('观察结果', '再判断是否继续'))
               + '<div class="loop-return">← 工具结果回到下一次决策</div>')),
    '固定流程可以在某个环节让模型动态选择动作。',
    '两边都能处理这笔费用，差别是主要路径由谁决定。左侧由程序定义审批条件与分支。右侧先看结果再判断缺什么，应用按授权执行它选的动作。下一页只改变最后一份材料，看选择怎样改变。',
    ('agents',), cls='workflow-page')

add('08 / 工具与自主决策', 'ReAct 的行动与观察', 'Reasoning + Acting 交替进行。查完资料和金额后，审批材料决定接下来做什么。',
    '<div class="react-task"><b>任务</b><span>核对 120 新币和一晚 560 元住宿，交付报销说明。</span></div>'
    + buttons('react', ['找制度', '查汇率', '做计算', '检查审批'], cls='screen-only')
    + '<div class="approval-options screen-only" id="approvalChoices" hidden><b>审批材料</b>'
    + buttons('approval', ['未提供记录', '已提供记录']) + '</div>'
    + '<div class="react-demo screen-only">'
      '<div class="react-row"><b>当前判断</b><span id="reactReason"></span></div>'
      '<div class="react-row"><b>行动 Action</b><span id="reactAction"></span></div>'
      '<div class="react-row"><b>观察 Observation</b><span id="reactObservation"></span></div>'
      '<div class="react-row"><b>下一步</b><span id="reactNext"></span></div></div>'
    + '<div class="print-only">'
    + flow(('找制度', '每晚 500 元，超标须事前审批'),
           ('查汇率', '1 SGD = 5.30 CNY'),
           ('算金额', '合计 1,196 元，住宿超标 60 元'),
           ('检查审批', '材料决定下一步'))
    + cols(block('未提供审批记录', p('把审批标为待补，交付已有核对结果。')),
           block('已提供审批记录', p('查询审批系统，核验是否适用于本次行程和费用。'))) + '</div>',
    '离线预写演示。观察变化时，下一步动作也会变化。',
    '【演示】先走完前三步，第四步切换有无审批记录。材料缺失时，今天的范围内可以给出待补说明。用户已提供记录时，还要去审批系统核验。当前判断是教学用的状态摘要。ReAct 是交替使用推理与动作的一种模式。接下来把模型之外负责执行、保存状态和停止的东西画出来。',
    ('react', 'agents'), cls='react-page')

add('09 / Agent 运行环境', 'Harness 怎样运行 Agent？', 'Harness 是围绕模型的运行与控制系统。它组织每轮调用，管理执行和任务状态。',
    flow(('读取任务状态', '已查到制度，外币金额待换算。'),
         ('准备本轮调用', '选出问题、条款和获准工具。'),
         ('执行与记录', '校验工具请求，保留结果和状态。'),
         ('检查是否继续', '还有授权范围内的待办，就继续一轮。'))
    + table(['应用维护的内容', '本例记录什么'], [
        ('状态和证据', '目标、已核对金额、条款原文位置、审批待补'),
        ('运行约束', '可访问的系统、工具权限、重试与费用上限'),
    ], 'compact-table'),
    '',
    'ReAct 页展示模型根据观察选了哪个动作，这里换成运行软件的视角。Harness 管每轮模型请求、执行环境和结果记录，具体边界随实现变化。工具结果到手后，先保存再检查是否需要继续。长任务换到新上下文时，要知道从哪里接起。',
    ('harness', 'context'))

add('09 / Agent 运行环境', '长任务的记忆与上下文压缩', '任务中断或窗口变紧时，保留可恢复的状态，再按当前步骤取回需要的细节。',
    cols('<div class="document-paper">'
         + p('模型外保存的任务记录', 'kicker')
         + '<h3>核对进度</h3>'
         + p('<b>已完成</b>　外币折合 636 元，费用合计 1,196 元。')
         + p('<b>可复查</b>　制度 §3.2–3.3、11 月 8 日的汇率工具回执。')
         + p('<b>待办</b>　查验超标住宿的事前审批。') + '</div>',
         '<div>'
         + block('记忆：下次能找到这些状态', p('保存记录与出处。恢复时取回待办、已核对数字和可复查的引用。'))
         + block('压缩：本轮只带必要信息', p('把长会话缩为事实、决定和待办。查询审批时，可以按需取回原条款。'))
         + '</div>', cls='case-comparison'),
    '摘要可能遗漏细节，保存的资料也可能过期。出处要能重新查到。',
    '先请大家指出下一轮还要做哪一件事。每次恢复不必逐字带回所有历史，也不能把已确认和待办混淆。这里的记忆依赖模型外的存储和取回，压缩是管理窗口中的信息量。恢复之后，如果仍没有审批，运行环境还要决定这轮在哪里停。',
    ('harness', 'context'))

add('09 / Agent 运行环境', '工具执行与停止条件', '根据实际返回状态处理失败，在权限、时限和预算范围内推进任务。',
    table(['运行中遇到什么', '运行环境怎样处理', '交付时怎么写'], [
        ('汇率接口超时', '按规则有限重试，记录失败状态', '仍超时时说明汇率待核对'),
        ('审批材料缺失', '保存已核对的条款和金额，停止本轮', '保留已确认结果，将审批标为待补'),
        ('票据脚本访问越界', '沙箱限制文件与资源访问，记录拦截', '说明字段未获验证，按流程补材料'),
        ('达到时限或费用上限', '停止继续调用，保留可恢复的进度', '列出已完成事项与剩余工作'),
    ]),
    '工具执行成功看回执。整项任务能否结案，还要看交付要求和缺项。',
    '汇率超时属于运行错误，可以按规则重试。没提供审批是业务缺件，重复问同一个工具不一定有用。沙箱限制执行位置和资源，避免程序越过被允许的范围。工具如何接到应用、做事方法如何复用，就是下一组概念。',
    ('harness', 'agents'))

add('10 / 连接与任务方法', 'Tool、MCP 与 Skill 的分工', '以核验审批为例，分别看要执行的动作、应用的连接和报销核对的做法。',
    table(['要解决的问题', '对应概念', '差旅助手中的例子'], [
        ('这次具体执行什么？', 'Tool（工具）', '按审批编号查询，返回记录状态及适用行程。'),
        ('应用怎样接上审批系统？', 'MCP（Model Context Protocol）', '应用使用约定的协议发现并调用审批系统暴露的查询工具。'),
        ('报销核对按什么做法？', 'Skill（任务技能包）', '说明何时要核验审批，提供核对报告模板。'),
    ]) + note('工具可以直接接入，也可以通过 MCP 接入。Skill 的说明可以引用工具，具体接入方式由应用决定。'),
    '',
    '这三个词描述的是不同问题。在这笔报销里，Skill 的规则帮助决定什么时候要看审批。应用可以通过 MCP 接到审批系统，真正执行查询的是一个工具。先从连接关系看 MCP 的几个参与者。',
    ('mcp', 'skills', 'tools'))

add('10 / 连接与任务方法', 'MCP 的 Host、Client 与 Server', '差旅助手是 Host，其中的 Client 分别连接文档和审批 Server。',
    '<div class="mcp-diagram">'
    '<div class="mcp-host"><div class="mcp-host-summary"><p class="kicker">HOST · AI 应用</p><h3>差旅助手</h3>'
    '<p>管理会话与工具执行</p></div><div class="mcp-client">文档 MCP Client</div><div class="mcp-client">业务 MCP Client</div></div>'
    '<div class="mcp-links"><span>文档连接</span><span>业务连接</span></div>'
    '<div class="mcp-servers"><div><h3>文档 MCP Server</h3><p>提供制度搜索工具与文档资源</p></div>'
    '<div><h3>业务 MCP Server</h3><p>提供审批查询工具</p></div></div></div>'
    + note('MCP 约定应用怎样发现并使用外部能力。Server 可以提供工具、资源或提示模板。业务规则和数据权限仍由相关系统管理。'),
    '',
    '沿上面一条连接看。宿主应用内的文档客户端发现服务端的制度搜索工具，应用可以把工具说明提供给模型。业务客户端另连一个 Server。具体能用哪些能力，取决于服务提供的能力和应用权限。连通系统后，还要决定报销核对按哪套步骤做。',
    ('mcp', 'mcp_arch'))

add('10 / 连接与任务方法', 'Skill 的任务说明与按需加载', 'Agent Skills 以 SKILL.md 保存任务说明，可以附带参考内容、脚本与模板。',
    cols('<div>' + p('报销核对 Skill 的示例目录', 'code-label')
         + code('''expense-review/
├── SKILL.md
├── references/
│   └── policy-guide.md
├── scripts/
│   └── summarize-expenses.py
└── assets/
    └── report-template.md''') + '</div>',
         block('收到报销核对任务时',
               p('<b>发现</b>　用名称和描述判断是否适用。')
               + p('<b>启用</b>　读取 SKILL.md，了解核对顺序和缺件规则。')
               + p('<b>使用</b>　有华东差旅时查相应制度，交付时读取报告模板。'))),
    '加载的说明会成为本轮可用的信息。工具和脚本仍由运行环境执行。',
    '这个示例的 Skill 只要求在交付阶段读模板，到核对具体地区时才看对应资料。按需加载可以减少无关说明占用上下文。它与前面训练更新参数是不同的操作。说到开始核对，有时用户提供的金额在票据图片上，接下来看应用怎样取得原始字段。',
    ('skills',))

add('11 / 多模态与交付', '多模态怎样读出票据字段？', '如果 560 元在照片里，应用可以用支持图像输入的模型，或先做 OCR，再提取所需字段。',
    cols('<div class="document-paper receipt-demo">'
         + p('教学票据 · 示意', 'kicker')
         + '<h3>住宿费用凭据</h3>'
         + '<dl><dt>费用日期</dt><dd>2026-11-08</dd><dt>住宿晚数</dt><dd>1 晚</dd>'
           '<dt>费用币种</dt><dd>人民币</dd><dt>合计金额</dt><dd><b>¥560.00</b></dd></dl></div>',
         '<div>' + p('应用需要的结构化字段', 'code-label')
         + code('''{
  "date": "2026-11-08",
  "nights": 1,
  "currency": "CNY",
  "amount": 560
}''')
         + p('逐项核对票据上的日期、晚数和金额，确认后交给查制度和算账环节。')
         + '</div>', cls='case-comparison'),
    '模型支持的模态和方向依规格而异。票据提取属于图像输入、结构化信息输出。',
    '左边是示意票据，右边是后续程序要用的四个字段。本页没有在线识别。可以用视觉语言模型直接读取，也可以由 OCR 技术识别文字再解析。语音转写或播报会用到其他能力。下一页把这些模型放回完整应用。',
    ())

add('11 / 多模态与交付', '差旅任务中各类模型的分工', '一张票据进入应用后，从提取输入到写说明，各环节需要的结果不同。',
    table(['任务环节', '处理组件', '交给下一步的内容'], [
        ('读取原始材料', '视觉模型或 OCR；语音识别可处理口述', '日期、金额等字段，或转写文本'),
        ('找制度证据', 'Embedding 模型与 Reranker', '问题和文段的向量表示，再选出排序靠前的条款'),
        ('计算与核验', '计算函数、汇率和审批查询等业务程序', '金额、接口响应和可核验的审批状态'),
        ('写说明', '生成式语言模型', '按要求组织成书面报告，可由语音合成播报'),
    ]),
    '生成模型依赖前面返回的事实和证据，应用再核对报告是否与这些结果一致。',
    '沿着这条链路看输入和输出。Embedding 与重排是生成前的检索环节。计算和系统查询交给程序。文本生成模型擅长把这些内容组织成一份说明。图片和视频生成也可以用各自的模型，需看输入输出能力。最后展示这笔费用实际交出的一页说明。',
    ('embedding', 'rag', 'tools'))

add('11 / 多模态与交付', '差旅助手交付的核对说明', '对应开场 2026-11-08 的差旅费用，供报销申请人核对。',
    '<div class="document-paper report-paper">'
    + '<div class="report-head"><p class="report-total">¥1,196 <small>费用合计</small></p>'
      '<div class="report-status"><b>全额报销待确认</b><p>补件后核验记录是否适用于本次行程。</p></div></div>'
    + table(['项目', '核对结果', '可复查依据'], [
        ('住宿', '1 晚 560 元，超出标准 60 元', '制度 v2026.11 §3.2，每晚限额 500 元'),
        ('外币费用', '120 SGD 折合 636 元', '2026-11-08 教学汇率 5.30，计算回执为 636 元'),
        ('审批', '待补本次住宿的事前审批记录', '制度 §3.3 要求超标费用提供事前审批'),
    ], 'report-table') + '</div>',
    '',
    '对照开场那句“可以全额报销”。现在已经核对金额、换算和适用条款。这里的一千一百九十六是费用合计，是否能全额报销仍须核验审批。让大家指出每一项数字的出处。下一页把同样的核对做成应用评测标准。',
    ())

add('回顾与交流', '整项任务的效果与成本', '用同一批报销任务比较不同版本。每个样例先规定怎样才算核对通过。',
    cols(block('这笔费用怎样判定通过',
               p('<b>金额</b>　换算为 636 元，费用合计 1,196 元，住宿超标 60 元。')
               + p('<b>依据</b>　条款、制度版本和汇率日期可追溯。')
               + p('<b>缺件</b>　审批记录待补，结论保留待确认状态。')),
         block('一批任务怎样比较改动',
               p('<b>效果</b>　比较金额、引用与缺件状态的正确率。')
               + p('<b>时延</b>　记录整项任务耗时。流式输出的首段等待时间可另记。')
               + p('<b>成本</b>　汇总各轮模型用量、检索和工具调用。计费以服务规则为准。')),
         cls='evaluation-columns'),
    '用相同任务和判定规则比较，才能观察改动是否值得额外时间和调用。',
    '把开场的初答与最终说明放进同一套检查。换算错、条款找不到、审批被当作完成，都要分别计入。带工具的 Agent 经常执行多次模型请求，评估整项任务比只比较一轮 Token 价格更接近真实使用。最后用一条找不到的制度规定练习定位问题。',
    ('agents', 'context'))

add('回顾与交流', '助手引用了不存在的条款，怎么排查？', '它声称“§5.4 允许报销”，但财务在适用制度中找不到。你会先看哪份记录？',
    table(['检查对象', '要确认什么', '发现问题时改哪里'], [
        ('制度原文', '§5.4 是否存在，当前版本是否适用', '检查源文件版本、适用范围和索引更新'),
        ('检索日志', '有没有召回正确的住宿和审批条款', '检查分段、召回、筛选及重排'),
        ('实际模型请求与输出', '正确条款有没有送到模型，结论能否由条款推出', '检查上下文组装、提示词与引用校验'),
    ]),
    '任选一处，说出你要查的证据，以及查到怎样的结果会改变下一步。',
    '先独立查看适用的制度原文，再沿检索记录和请求定位丢失或错误使用的证据。任务要求不清时可以改提示词，缺外部资料时可以改检索或接口，计算缺口交给工具。如果携带正确依据后仍反复出现稳定的任务行为问题，再评估是否需要训练。到这里结束主讲，余下两页供会后查阅。')

REFERENCE_GROUPS = [
    ('模型与部署', ['llm', 'tokens', 'files', 'qwen', 'quant']),
    ('训练与对话', ['sft', 'rlhf', 'chat', 'vllm_api']),
    ('检索与 Agent', ['rag', 'context', 'tools', 'react', 'harness', 'mcp', 'skills']),
]
reference_groups = []
for heading, keys in REFERENCE_GROUPS:
    links = ''.join(
        f'<a href="{SOURCES[k][1]}" target="_blank" rel="noopener">{SOURCES[k][0]}</a>'
        for k in keys
    )
    reference_groups.append(f'<div class="reference-group"><h3>{heading}</h3>{links}</div>')

add('附录 / 参考资料', '参考资料', '',
    '<div class="references">' + ''.join(reference_groups) + '</div>',
    '离线 HTML 中按 N 查看本页讲稿与来源。完整清单见随附的资料说明和逐页讲稿。',
    '本页供会后找资料。按主题跳到相应页可查看该页的模型配置、论文或协议说明。',
    [key for _, keys in REFERENCE_GROUPS for key in keys], cls='reference-page')

add('附录 / 参考资料', '案例数据与演示口径', '区分真实分词和仓库资料、预写的业务数据，以及教学插图。',
    table(['内容', '口径'], [
        ('差旅案例', '公司制度、审批场景、金额和汇率为教学设定。'),
        ('分词与生成', 'cl100k_base 的分词、ID 和新增 Token 边界经分词器核对。续写内容本身为预写。'),
        ('离线交互', '聊天模板使用简化示例。汇率查询、计算回执和 ReAct 分支按预设展示。'),
        ('公开模型资料', '仓库文件、配置与规格沿用 2026-11-18 核对的官方资料。'),
        ('图与票据', '封面和 Dense/MoE 示意图为 AI 生成。票据为模拟材料，用于解释字段提取。'),
    ], 'materials-table'),
    '',
    '整场交互在本地运行。公开的模型规格、代码和物料出处可在逐页讲稿或同版资料说明中查到。')
