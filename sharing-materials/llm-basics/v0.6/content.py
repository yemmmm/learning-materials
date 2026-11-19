"""v0.6 slide content, speaker notes, and sources in presentation order."""
import html
from textwrap import indent

SOURCES = {
 'llm': ('Hugging Face · 语言模型与 Transformer', 'https://huggingface.co/learn/llm-course/chapter1/4'),
 'nlp': ('Hugging Face · 自然语言处理的常见任务', 'https://huggingface.co/learn/llm-course/chapter1/2'),
 'lstm': ('Hochreiter 与 Schmidhuber · LSTM（1997）', 'https://doi.org/10.1162/neco.1997.9.8.1735'),
 'transformer': ('Vaswani 等 · Transformer（2017）', 'https://arxiv.org/abs/1706.03762'),
 'bert': ('Devlin 等 · BERT（2018）', 'https://arxiv.org/abs/1810.04805'),
 'chatgpt': ('OpenAI · 首次发布 ChatGPT（2022）', 'https://openai.com/index/chatgpt/'),
 'files': ('Qwen3-8B · 官方文件列表', 'https://huggingface.co/Qwen/Qwen3-8B/tree/main'),
 'config': ('Qwen3-8B · config.json', 'https://huggingface.co/Qwen/Qwen3-8B/blob/main/config.json'),
 'weight_index': ('Qwen3-8B · 权重分片索引', 'https://huggingface.co/Qwen/Qwen3-8B/blob/main/model.safetensors.index.json'),
 'tokenizer': ('Qwen3-8B · tokenizer.json', 'https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json'),
 'vocab': ('Qwen3-8B · vocab.json', 'https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/vocab.json'),
 'tokenizer_config': ('Qwen3-8B · tokenizer_config.json', 'https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json'),
 'generation_config': ('Qwen3-8B · 生成与停止设置', 'https://huggingface.co/Qwen/Qwen3-8B/blob/main/generation_config.json'),
 'network_diagram': ('Michael Clark · 前馈神经网络示意图', 'https://m-clark.github.io/img/nnet.png'),
 'safetensors': ('Safetensors · 张量存储格式', 'https://huggingface.co/docs/safetensors/index'),
 'qwen': ('Qwen3 · 官方发布说明', 'https://qwenlm.github.io/blog/qwen3/'),
 'q8': ('Qwen3-8B · 模型卡', 'https://huggingface.co/Qwen/Qwen3-8B'),
 'q8awq': ('Qwen3-8B-AWQ · 量化配置', 'https://huggingface.co/Qwen/Qwen3-8B-AWQ/blob/main/config.json'),
 'q8gguf': ('Qwen3-8B-GGUF · 权重文件', 'https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main'),
 'q30': ('Qwen3-30B-A3B · 模型卡', 'https://huggingface.co/Qwen/Qwen3-30B-A3B'),
 'q30fp8': ('Qwen3-30B-A3B-FP8 · 量化配置', 'https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8/blob/main/config.json'),
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
         + p('v0.6 · 2026 年 11 月', 'small') + '</div>',
         image('model-workbench.png', '由资料、计算器、终端和模型组成的纸艺插图'),
         cls='cover-columns'),
    '',
    '今天用一笔报销任务理解常见的大模型概念。案例包含一晚 560 元的住宿和一笔 120 新币的费用。先看模型的文件怎样支撑生成和部署，再看模型接收到的对话与资料。最后沿着工具执行的结果，看固定流程和 Agent 分别怎样推进任务。整场用同一笔费用收尾。',
    cls='cover')

add('01 / 模型是什么', '人工智能、深度学习与自然语言处理', '',
    cols('<div class="taxonomy"><div><b>人工智能 AI</b><span>让计算机完成需要智能的任务</span>'
         '<div><b>机器学习 ML</b><span>从数据中学习规律</span>'
         '<div><b>神经网络</b><span>训练相互连接的计算单元</span>'
         '<div><b>深度学习 DL</b><span>用多层神经网络学习表示</span></div></div></div></div></div>',
         block('自然语言处理（NLP）', p('让计算机理解或生成人使用的语言。')
               + '<ul class="nlp-examples">'
                 '<li><b>文本分类</b><span>把发票问题归为「报销咨询」</span></li>'
                 '<li><b>信息抽取</b><span>从描述里提取城市、晚数和金额</span></li>'
                 '<li><b>翻译与摘要</b><span>把差旅邮件译成中文，或提炼要点</span></li>'
                 '<li><b>问答与生成</b><span>按制度解释超标原因，起草说明</span></li>'
                 '</ul>'),
         cls='nlp-columns'),
    '',
    '先从 AI 缩到机器学习，再看到神经网络和多层网络。左边说的是技术，右边说的是用这些技术能做的语言任务。比如系统读到「在上海住了两晚，共 980 元」，可以抓取城市、晚数和金额，也可以按别的指令归类或回答问题。现代大语言模型让多种语言任务可以用同一个模型处理。',
    ('nlp',))

add('01 / 模型是什么', '大语言模型与 NLP 的发展', '在聊天和文本生成场景里，「大模型」通常指大语言模型（LLM，Large Language Model）。',
    p('大语言模型用大规模数据训练，学习语言规律。生成式 LLM 根据已有文本预测下一个片段（Token），逐步写出回答。', 'llm-definition')
    + '<ol class="history-line">'
      '<li><small>早期</small><h3>RNN / LSTM</h3><p>按顺序处理文本。LSTM 改善了跨较长距离保留信息的能力。</p></li>'
      '<li><small>2017</small><h3>Transformer</h3><p>用注意力处理序列，在机器翻译中展示了效果。</p></li>'
      '<li><small>2018</small><h3>BERT</h3><p>通过双向上下文做预训练，支持多种语言理解任务。</p></li>'
      '<li><small>2022</small><h3>ChatGPT</h3><p>基于 GPT‑3.5 开放对话，让生成式大语言模型走向大众。</p></li>'
      '</ol>',
    '',
    '这是神经网络在 NLP 中的几个节点。RNN 逐步读入序列，LSTM 是其中一种改进。Transformer 引入以注意力为基础的架构。BERT 和 GPT 都基于 Transformer，BERT 侧重语言理解，GPT 系列沿逐步生成的路线发展。2022 年的 ChatGPT 从 GPT‑3.5 系列模型微调而来，公众可以用聊天界面直接体验。',
    ('llm', 'lstm', 'transformer', 'bert', 'chatgpt'))

add('02 / 使用方式与模型文件', '托管 API 与自行部署', '两种方式都能让应用用 API 调用模型，区别在于谁运行模型服务。',
    cols(block('托管 API', p('供应商选定模型版本，运行和维护服务。')
               + p('团队编写业务逻辑，准备输入数据，管理调用用量。')),
         block('自行部署', p('团队在自管机器或云 GPU 上，用推理框架加载权重并提供接口。')
               + p('团队也负责算力、并发和服务运维。')),
         cls='deployment-columns'),
    '同一个开放权重模型，也可能同时提供托管服务和可下载的权重。',
    '先问谁负责让模型上线。团队用托管服务时主要关心业务输入和用量。团队自行部署时，需要取得权重并核对发布许可。接下来看一个公开的模型仓库里可以下载哪些文件。',
    ('qwen',))

add('02 / 使用方式与模型文件', '模型仓库的三类文件', '在 Hugging Face 打开 Qwen3-8B 仓库，找到配置、权重和分词器。',
    cols('<div class="repo-list"><div class="repo-heading"><h3>Qwen / Qwen3-8B</h3><p>Files and versions · main</p></div><div class="repo-file"><b>config.json</b><span>728 B</span></div><div class="repo-file"><b>generation_config.json</b><span>239 B</span></div><div class="repo-file weights"><b>model-00001-of-00005.safetensors</b><span>4 GB</span></div><div class="repo-file weights"><b>model-00002-of-00005.safetensors</b><span>3.99 GB</span></div><div class="repo-file weights"><b>… 另有 3 个权重分片</b></div><div class="repo-file"><b>model.safetensors.index.json</b><span>32.9 kB</span></div><div class="repo-file tokenizer"><b>tokenizer.json</b><span>11.4 MB</span></div><div class="repo-file tokenizer"><b>tokenizer_config.json</b><span>9.73 kB</span></div><div class="repo-file tokenizer"><b>vocab.json / merges.txt</b><span>词表 / 合并规则</span></div></div>',
 '<div class="file-explain">'+block('① 配置',p('<code>config.json</code><br>声明模型类型、层数、隐藏维度等，供对应实现读取。'))+block('② 权重',p('<code>model-*.safetensors</code><br>训练得到的张量。多个文件通常是分片，索引文件记录位置。'))+block('③ 分词器',p('<code>tokenizer.json</code>、<code>vocab.json</code>、<code>merges.txt</code> 等<br>保存文本与 Token ID 之间的转换规则。'))+'</div>',cls='media-left'),
    '配置说明模型怎么构建，权重提供数值，分词器约定文字怎样转成编号。',
    '左边是官方文件列表的节选，颜色对应三类文件。权重有五个分片，索引记录每个张量放在哪一片。分词器也有几个文件，词表里的编号要和切分规则一起使用。下一页打开 vocab.json 看一段实际记录。',
    ('files', 'safetensors', 'vocab', 'tokenizer_config'), cls='file-page')

add('03 / 分词、生成与加载', 'Token 与 Token ID', '分词器把文本切成片段，再用对应词表里的整数编号表示这些片段。',
    cols('<div><div class="screen-only">'
         + buttons('token', ['英文', '中文', '代码'])
         + '<div class="token-demo"><div class="example-head"><b id="tokenText">Hello, world!</b>'
           '<span id="tokenCount">__TOKEN_COUNT__ 个 Token</span></div>'
           '<div class="token-list" id="tokenPieces">__TOKENS__</div></div></div>'
         + '<div class="print-only token-print">__TOKEN_PRINT__</div></div>',
         '<div>' + p('Qwen3-8B 的 vocab.json 节选', 'code-label')
         + '<pre><code>__VOCAB__</code></pre>'
         + p('这四条对应英文样例。词表中 <code>Ġ</code> 表示前导空格，左侧用 <b>␠</b> 显示。')
         + '</div>',
         cls='token-vocab'),
    '模型根据 Token ID 找到各片段的向量表示。',
    '【演示】先从 Hello, world! 找到词表的四条记录，再切换中文和代码。前导空格随 world 进入同一个 Token。Token 可能是词、词的一部分、标点或字符的部分字节。这里的分词和词表都来自 Qwen3-8B。',
    ('tokenizer', 'vocab'), cls='token-page')

add('03 / 分词、生成与加载', '逐个 Token 生成文本', '模型用当前序列计算下一个 Token 的概率。每次选中的 Token 都会接回序列。',
    cols('<div><div class="screen-only">'
         '<div class="generation" id="generationText">The claim is</div>'
         + buttons('generate', ['初始输入', '追加 pending', '追加句号', '输出结束符'])
         + '<p class="generation-detail" id="generationDetail"></p></div>'
           '<div class="print-only generation-sequence">'
         + p('<b>初始输入</b> The claim is')
         + p('<b>第 1 步</b> The claim is <mark>pending</mark><small>ID 15280，含前导空格</small>')
         + p('<b>第 2 步</b> The claim is pending<mark>.</mark><small>ID 13</small>')
         + p('<b>第 3 步</b> The claim is pending. <mark><code>&lt;|im_end|&gt;</code></mark><small>ID 151645，结束生成</small>')
         + '</div></div>',
         '<div>'
         + block('新内容成为下一步的前文', p('生成句号时，模型已经看到了上一步追加的 pending。'))
         + block('模型输出结束符', p('当模型预测并选中结束 Token，推理服务识别它并停止生成。用户通常只看到「The claim is pending.」。'))
         + '</div>',
         cls='generation-columns'),
    '这里用 Qwen3-8B 的真实 Token ID 演示预设的续写过程。',
    '【演示】依次点 pending、句号和结束符。注意句号本身只是一个普通 Token，例子最后选中 <|im_end|> 才触发停止。这是 Qwen3-8B 配置的结束标记之一。服务也可以按最大输出长度等限制停下。生成依赖加载好的网络和权重，接下来拆开看。',
    ('llm', 'tokenizer', 'tokenizer_config', 'generation_config'), cls='generation-page')

add('03 / 分词、生成与加载', '网络结构与模型权重', '模型实现定义计算，配置给出层数和维度，权重文件提供训练得到的数值。',
    cols('<div class="network-figure">'
         + '<div class="network-art">' + image('neural-network.png', '简化的前馈神经网络，包含输入层、隐藏层、输出层和连接。粗线是示例连接。')
         + '<span class="network-weight">w = 0.8</span></div>'
         + '<div class="network-labels"><b>输入层</b><b>隐藏层</b><b>输出层</b></div>'
         + p('层和连接的排列是结构。粗线旁的数字是权重示例。', 'small')
         + '</div>',
         '<div>'
         + p('Qwen3-8B / config.json 节选', 'code-label')
         + code('''"model_type": "qwen3",
"num_hidden_layers": 36,
"hidden_size": 4096''')
         + p('框架按 Qwen3 的实现和配置构建 36 层，再从 Safetensors 分片装入相应的权重张量。')
         + p('<code>model.safetensors.index.json</code> 记录各张量在哪个分片。', 'small')
         + '</div>',
         cls='network-columns'),
    '',
    '先指着图看哪些节点相连，再看一条粗线上的示例权重。结构定了以后，换一组权重数值，就可能算出不同结果。图是一张抽象的前馈网络。真正的 Qwen3 使用 Transformer，层内计算由模型实现定义。读取分片索引可以找到张量，例如词嵌入在第 1 片，输出层权重在第 5 片。输入 Token ID 对应词嵌入矩阵的一行。',
    ('network_diagram', 'config', 'weight_index', 'safetensors'))

def name_parts(*parts):
    return '<div class="model-name" aria-label="' + '-'.join(label for label, _ in parts) + '">' + (
        '<i>−</i>'.join(f'<span>{label}<small>{description}</small></span>' for label, description in parts)
    ) + '</div>'

add('04 / 模型规格与推理服务', '模型名称里的参数量和量化规格', 'B 表示十亿个参数。用同一家族的两个发布版本对照。',
    name_parts(('Qwen3', '模型家族'), ('8B', '约 80 亿总参数'), ('AWQ', '本版为 4 位权重量化'))
    + name_parts(('Qwen3', '模型家族'), ('30B', '约 300 亿总参数'),
                 ('A3B', '每 Token 激活约 30 亿参数'), ('FP8', '8 位浮点量化版本')),
    '型号中的参数量是约数。具体参数量和量化方式以模型卡与配置为准。',
    '第一行的模型是 Dense，官方模型卡的总参数是 8.2B，AWQ 配置为 4 位。第二行是 MoE，官方给出 30.5B 总参数和 3.3B 激活参数。FP8 指这个发布版本主要权重采用 8 位浮点量化。先用下一页解释为什么会有 A3B，再估算较低位宽对权重大小的影响。',
    ('q8', 'q8awq', 'q30', 'q30fp8'), cls='model-names-page')

add('04 / 模型规格与推理服务', 'Dense 与 MoE 的前馈层', '同样处理一个 Token，两种架构选择前馈层参数的方式不同。',
    cols(image('dense-moe.png', 'Dense 使用共享前馈网络，MoE 的路由从四个专家中选中两个', 'moe-figure'),
         '<div>'
         + block('Dense（稠密模型）', p('Qwen3-8B 的每个 Token 经过该层时，都使用同一组前馈参数。'))
         + block('MoE（混合专家模型）', p('Qwen3-30B-A3B 的路由为当前 Token 选择部分专家。其他专家的权重仍会为后续 Token 保留。'))
         + p('前馈层示意图以四选二说明路由。绿色标出本次参与的专家。', 'small')
         + '</div>', cls='moe-columns'),
    '总参数量关系到要存多少权重，激活参数量描述处理一个 Token 时用到的参数规模。',
    '左图的 FFN 是前馈网络。右图中的专家是子网络，路由按 Token 选中一部分。四选二是教学示意，Qwen3-30B-A3B 的模型卡列出 128 个专家，每个 Token 选 8 个。A3B 加上了共享部分所用的参数，描述每个 Token 激活的总规模。',
    ('q8', 'q30', 'qwen'), cls='moe-page')

add('04 / 模型规格与推理服务', '低精度、量化与蒸馏', '量化用较低位宽近似表示已有权重。蒸馏让学生模型学习教师模型的输出。',
    cols(block('量化减少每个权重占的空间',
               p('例如把 16 位 BF16 权重近似表示为 4 位值。这里以 80 亿个权重粗算。')
               + '<div class="quant-sizes"><div><b>16 GB</b><span>16 位，每个值 2 字节</span></div>'
                 '<div><b>4 GB</b><span>4 位，两个值可打包进 1 字节</span></div></div>'
               + p('实测体积还要计入缩放因子等数据。近似会带来误差，效果要用样例核对。', 'small')),
         block('蒸馏把教师的能力传给学生',
               flow(('教师模型', '给出预测概率或示范答案'), ('学生模型', '用这些信号训练，通常更小'))
               + p('例如用教师给出的报销回答训练学生，练习算出超标金额并说明审批条件。')),
         cls='quant-columns'),
    '低精度描述数值格式。量化是转换数值表示的过程。训练好的学生模型也可以再量化。',
    '低精度格式例如 FP8 和 INT4。量化可以在训练后进行，也可以在训练中考虑量化误差。左侧假设所有权重用同一位宽，只计算十进制 GB；部署还需给其他数据和运行状态留空间。蒸馏的关键是来自教师的训练信号，例如用教师的预测概率或输出答案训练学生。两种方法可以组合。',
    ('quant', 'awq', 'distill'), cls='quant-page')

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

add('04 / 模型规格与推理服务', '训练、部署与推理框架', '训练产出权重。部署把权重加载进服务，应用随后用 API 发送一次次推理请求。',
    flow(('训练更新参数', '用样本和训练目标调整参数，保存训练好的权重。'),
         ('框架加载模型', '启动时读取配置，加载权重与分词器，提供 API。'),
         ('推理生成答复', '应用传入「一晚 560 元能全额报吗」和适用条款。框架用已加载的参数生成并返回答复。'))
    + note('<b>工具举例</b>　Transformers 提供模型实现、加载和生成接口。vLLM、SGLang 可提供并发推理服务。llama.cpp 常用于本地运行 GGUF 模型。'),
    '把制度放进本次请求，会改变这次推理的输入。训练才会更新可训练参数。',
    '第一步产出权重，微调也可能只产出适配器，例如冻结原权重的 LoRA。部署时启动框架加载这些文件，后面每次调用走第三步。应用负责提供本次所需信息，推理框架用已加载的模型计算回答。接下来看看训练中的不同阶段分别让模型学到什么。',
    ('files', 'qwen', 'vllm_api', 'lora'))

add('05 / 训练与对话', '预训练、监督微调与对齐', '从学习续写，到按指令作答，再到按偏好改进回答。对齐以 InstructGPT 的人工偏好训练为例。',
    cols(block('预训练', p('从大量文本学习预测下一个 Token。')
               + '<div class="document-paper">'
               + p('前文', 'kicker') + p('住宿标准为每人每晚……')
               + p('<b>训练目标</b>　预测组成「500 元」的后续片段。') + '</div>'),
         block('监督微调（SFT）', p('给出任务和示范回复，让模型练习按指令作答。')
               + '<div class="document-paper">'
               + p('问题', 'kicker') + p('一晚 560 元能全额报销吗？')
               + p('<b>示范回复</b>　超出 60 元，需核对事前审批。') + '</div>'),
         block('偏好对齐', p('让人比较同一问题的多个回答，再用偏好改进模型。')
               + '<div class="document-paper">'
               + p('人工排序', 'kicker')
               + p('<b>更好</b>　超出 60 元，需核对审批。')
               + p('<b>较差</b>　这笔可以全额报销。') + '</div>'),
         cls='three-columns training-examples'),
    '',
    '左侧的信号来自原始文本的后续内容。中间的信号来自示范答案，帮助模型学会按任务要求作答。右侧是在学哪种回答更好：标注者给同一问题的候选回答排序，InstructGPT 用排序训练奖励模型，再用评分和 PPO 更新助手。这是偏好对齐的一种做法。对齐是更广的训练目标，监督微调也可以用于对齐。下一页单看对话样本如何教模型扮演助手。',
    ('llm', 'sft', 'rlhf'), cls='training-page')

def dialogue_turn(role, message, cls=''):
    return f'<div class="dialogue-turn {cls}"><b>{role}</b>{p(message)}</div>'

first_question = dialogue_turn('用户', '一晚花了 560 元，能全额报销吗？')
first_answer = dialogue_turn('助手', '超出 60 元。全额报销要看事前审批记录。')
training_dialogue = first_question + first_answer
reply_start = dialogue_turn('助手', '从这里续写', 'reply-start')
second_prompt = training_dialogue + dialogue_turn('用户', '两晚各花了 560 元呢？') + reply_start

add('05 / 训练与对话', '续写模型怎样成为对话助手', '预训练教模型预测下一个 Token。监督微调用带角色的示范对话，教它在助手轮次回答用户。',
    p('给定制度　住宿上限每晚 500 元，超标须事前审批。', 'dialogue-policy')
    + cols(block('训练时，给出助手的示范回复',
               '<div class="document-paper dialogue">' + training_dialogue + '</div>'
               + p('模型练习根据用户问题续写示范回复，训练会更新参数。', 'dialogue-caption')),
         block('使用时，在助手的位置开始续写',
               buttons('chat', ['第一轮', '第二轮（带历史）'], cls='screen-only')
               + '<div class="screen-only">'
               + '<div class="document-paper dialogue" data-chat-prompt>' + first_question + reply_start + '</div>'
               + '<div class="document-paper dialogue" data-chat-prompt hidden>' + second_prompt + '</div></div>'
               + '<div class="document-paper dialogue print-only">' + second_prompt + '</div>'
               + p('应用用聊天模板标记角色和轮次，模型续写的内容成为助手的回复。', 'dialogue-caption')),
         cls='dialogue-columns'),
    '下一轮，同一套模板把相关历史和新问题一起送回模型。',
    '【演示】两侧都已提供每晚 500 元、超标须事前审批的制度。训练时给出用户和助手的完整对话，示范一个合适的回答。使用时，应用提供用户问题，模板在末尾加上助手的起始标记。模型仍然预测下一个 Token，续写的这段话就是回复。点第二轮，指一下上一轮的回复和新的起始位置。比如 Qwen3 的模板用 <|im_start|>assistant 标记开始，用 <|im_end|> 标记结束。更流畅的作答仍依赖这次请求确实带上了正确的依据。',
    ('sft', 'chat', 'tokenizer_config'), cls='dialogue-page')

add('06 / 模型到应用', '提示词是什么，怎样写清楚？', '提示词（Prompt）是给模型的输入。它可以是一句提问，也可以是一份任务说明，附带原文或示例。',
    cols('<div><h3>一份清楚的提示词写明</h3>'
         + '<ol class="prompt-guide">'
           '<li><b>目标</b>　要从报销描述提取哪些字段？</li>'
           '<li><b>约束</b>　只用原文。缺失字段填 <code>null</code>。</li>'
           '<li><b>输出格式</b>　指定 JSON 字段与金额单位。</li>'
           '</ol>'
         + p('本次输入应得到', 'code-label special-token-label')
         + code('{"city":"北京","nights":null,"amount":450}') + '</div>',
         '<div>' + p('可直接发给模型的提示词', 'code-label')
         + code('''从报销描述里提取城市、住宿晚数和金额。
只用原文。缺失字段填 null。
返回 JSON，金额用人民币元，字段见示例。

示例输入  上海住两晚，共 980 元。
示例输出  {"city":"上海","nights":2,"amount":980}

本次输入  北京住宿花了 450 元。''') + '</div>',
         cls='prompt-columns'),
    '任务有固定的输出要求时，可以放入少量输入和输出示例（Few-shot）。',
    '「帮我整理好」就是一条提示词，但它没说要什么字段，也没交代缺项怎么处理。右边把结果、取值范围和格式写清楚，示例又说明了 JSON 怎么写。本次输入没有晚数，用 null 表示。Few-shot 示例随本次请求送入模型。接下来从一段任务指令扩展到整次请求，看还需要带哪些信息。',
    ('context',))

def context_item(messages, label, explanation, cls=''):
    return (
        f'<div class="context-item {cls}"><div class="request-snippet">{messages}</div>'
        f'<div class="context-meaning"><h3>{label}</h3>{p(explanation)}</div></div>'
    )

add('06 / 模型到应用', '一次请求里的上下文与窗口', '上下文工程决定这一次实际送入模型的信息。下面是「两晚各花了 560 元呢？」的请求。',
    '<div class="context-request-stack">'
    + p('vLLM · POST /v1/chat/completions <small>完整请求体见讲稿</small>', 'code-label')
    + context_item(p('<code>system</code>　按给定差旅制度回答。'),
                   '任务指令', '告诉模型按什么规则作答。')
    + context_item(p('<code>user</code>　一晚花了 560 元，能全额报销吗？')
                   + p('<code>assistant</code>　超出 60 元。全额报销要看事前审批记录。'),
                   '相关历史', '保留本轮追问依赖的问题和回答。')
    + context_item(p('<code>user</code>　§3.2 上限 500 元/晚。§3.3 超标须事前审批。'),
                   '外部资料', '带入相关制度条款和编号。')
    + context_item(p('<code>user</code>　两晚各花了 560 元呢？'),
                   '本轮问题', '和上面的制度放在同一条 user 消息。')
    + context_item(p('<code>max_completion_tokens = 300</code>'),
                   '生成上限', '最多生成 300 个 Token。输入和输出共用窗口。', cls='context-output')
    + '</div>',
    '这次把条款直接写进了请求。换个问题，怎样自动找到相关条款？',
    '沿左侧从上到下看。这条请求有四条消息，最后一条 user 消息含制度与问题，图里把它拆开说明用途。应用留住了必要历史和条款，可以舍去无关机票记录。如果这轮涉及工具，还可按需提供工具说明和实际回执。300 是这次请求的生成上限，仍需在模型窗口里留出空间。按给定规则，两晚共花 1,120 元，超标 120 元，审批仍待核验。接下来讲这些原始条款怎样找出来。\n\n完整请求体\n\n' + indent(VLLM_REQUEST, '    '),
    ('context', 'vllm_api', 'chat'), cls='context-stack-page')

add('07 / RAG 与检索', 'RAG 怎样把相关条款带进回答？', '检索增强生成（RAG）在回答前按问题找资料，再把找到的文本和问题一起交给模型。',
    '<div class="rag-figure" role="group" aria-label="差旅制度切片入库，住宿问题检索相关条款并将其填入模型上下文">'
    '<div class="rag-inputs">'
    '<div class="document-paper rag-source"><h3>差旅制度</h3><p>住宿标准与超标审批<br>机票舱位规定</p></div>'
    '<div class="rag-question"><h3>本轮问题</h3><p>两晚各花了 560 元呢？</p></div>'
    '</div>'
    '<div class="rag-incoming"><p class="rag-arrow">切片并建索引</p><p class="rag-arrow">按问题匹配</p></div>'
    '<div class="rag-index"><h3>制度片段库</h3>'
    '<div class="rag-match"><b>§3.2 住宿标准</b><p>上限 500 元/晚。</p></div>'
    '<div class="rag-match"><b>§3.3 超标审批</b><p>超标须事前审批。</p></div>'
    '<div class="rag-other"><b>机票舱位规定</b></div>'
    '</div>'
    '<p class="rag-arrow rag-outgoing">取回匹配片段</p>'
    '<div class="rag-model"><h3>送给模型的上下文</h3>'
    '<p><b>外部资料</b>　§3.2 和 §3.3 的原文</p>'
    '<p><b>本轮问题</b>　两晚各花了 560 元呢？</p>'
    '<div class="rag-answer"><b>模型回答</b><p>两晚共 1,120 元，超标 120 元。能否全额报销要核验审批。</p></div>'
    '</div></div>',
    '换一个问题，应用就重新检索，并更新请求中的「外部资料」。',
    '上一页直接写入了住宿条款。如果改问机票，应用得找到另一段制度。先把差旅制度按条款切成片段，保存文本、条款号和原文出处，再建索引。收到这次住宿问题后，检索匹配 §3.2 和 §3.3，把两段原文填到请求的外部资料位置。任务指令和相关历史仍可按需带上。制度更新时也可以更新文档和索引。RAG 全称 Retrieval-Augmented Generation。下一页区分 Token ID 和检索常用的向量。',
    ('rag', 'embedding'), cls='rag-page')

add('07 / RAG 与检索', 'Token ID 与 Embedding 向量', 'Token ID 标识词表中的一个片段。Embedding 用一组数表示内容特征。',
    cols(block('Token ID', code('9707')
               + p('这是 Qwen3-8B 词表中 Hello 的编号。语言模型用它查词嵌入矩阵的一行。')
               + p('编号接近只表示词表位置相邻。')),
         block('Embedding 向量', code('[0.12, −0.34, …]')
               + p('这是检索模型为一段文字生成的向量示意。可以用同一个模型编码问题和条款，再比较相似度。'))),
    '把“住酒店”和“住宿标准”分别编码成检索向量，可以按语义相关性召回候选。',
    '回到前面词表里的 Hello，9707 是用来查找对应向量的索引。编号的差值没有语义意义。右边的向量对应整段文字，检索模型的输出通常有很多维，应用按模型支持的方式比较问题与文档向量。下一页让召回和重排各做一步。',
    ('vocab', 'embedding'))

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
    + flow(('模型提出查询', '查询 SGD/CNY 与 2026-11-08 的汇率。'),
           ('应用返回汇率', '1 SGD = 5.30 CNY，status: ok。'),
           ('模型请求乘法', '计算工具回执 120 × 5.30 = 636 CNY，status: ok。'),
           ('模型组织答复', '120 新币折合 636 元，附汇率日期。'))
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
    + cols(block('状态和证据', p('目标、已核对金额、条款原文位置、审批待补。')),
           block('运行约束', p('可访问的系统、工具权限、重试与费用上限。'))),
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
    cols(block('Tool（工具）', p('<b>执行什么</b>') + p('按审批编号查询，返回记录状态及适用行程。')),
         block('MCP（协议）', p('<b>怎样接入</b>') + p('MCP 全称 Model Context Protocol。应用按协议发现并调用审批查询工具。')),
         block('Skill（任务技能包）', p('<b>按什么方法核对</b>') + p('说明何时要核验审批，提供核对报告模板。')),
         cls='three-columns')
    + note('工具可以直接接入，也可以通过 MCP 接入。Skill 的说明可以引用工具，具体接入方式由应用决定。'),
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

add('11 / 多模态与交付', '差旅助手交付的核对说明', '供报销申请人核对 2026-11-08 的住宿与外币费用。',
    '<div class="document-paper report-paper">'
    + '<div class="report-head"><p class="report-total">¥1,196 <small>费用合计</small></p>'
      '<div class="report-status"><b>全额报销待确认</b><p>补件后核验记录是否适用于本次行程。</p></div></div>'
    + '<dl class="report-items">'
      '<div><dt>住宿</dt><dd><b>1 晚 560 元，超出标准 60 元</b><br>制度 v2026.11 §3.2 的每晚限额为 500 元。</dd></div>'
      '<div><dt>外币费用</dt><dd><b>120 SGD 折合 636 元</b><br>2026-11-08 教学汇率为 5.30，计算回执为 636 元。</dd></div>'
      '<div><dt>审批</dt><dd><b>待补本次住宿的事前审批记录</b><br>制度 §3.3 要求超标费用提供事前审批。</dd></div>'
      '</dl></div>',
    '',
    '一千一百九十六是这笔差旅的费用合计，是否能全额报销仍须核验审批。请大家指出每一项数字的出处。下一页把同样的核对做成应用评测标准。',
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
    '按同一套标准核对不同应用版本的结果。换算错、条款找不到、审批被当作完成，都要分别计入。带工具的 Agent 经常执行多次模型请求，评估整项任务比只比较一轮 Token 价格更接近真实使用。最后用一条找不到的制度规定练习定位问题。',
    ('agents', 'context'))

add('回顾与交流', '助手引用了不存在的条款，怎么排查？', '它声称“§5.4 允许报销”，但财务在适用制度中找不到。你会先看哪份记录？',
    flow(('制度原文', '§5.4 存在吗？先核对源文件、版本和适用范围。'),
         ('检索日志', '召回了适用的住宿和审批条款吗？检查分段、筛选及重排。'),
         ('模型请求与输出', '请求带上了正确条款吗？看结论能否由它推出，再查提示词与引用校验。')),
    '任选一处，说出你要查的证据，以及查到怎样的结果会改变下一步。',
    '先独立查看适用的制度原文，再沿检索记录和请求定位丢失或错误使用的证据。任务要求不清时可以改提示词，缺外部资料时可以改检索或接口，计算缺口交给工具。如果携带正确依据后仍反复出现稳定的任务行为问题，再评估是否需要训练。到这里结束主讲，余下两页供会后查阅。')

REFERENCE_GROUPS = [
    ('模型与部署', ['llm', 'transformer', 'bert', 'chatgpt', 'files', 'vocab', 'quant', 'distill']),
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
        ('分词与生成', '分词和 Token ID 经 Qwen3-8B 的分词器核对。逐步续写是预写演示。'),
        ('离线交互', '聊天模板使用简化示例。汇率查询、计算回执和 ReAct 分支按预设展示。'),
        ('公开模型资料', '仓库文件、词表、配置和规格依据讲稿所列的官方资料。'),
        ('图与票据', '封面和 Dense/MoE 图为 AI 生成，前馈网络图来自 Michael Clark。票据为模拟材料。'),
    ], 'materials-table'),
    '',
    '整场交互在本地运行。公开的模型规格、代码和物料出处可在逐页讲稿或同版资料说明中查到。')
