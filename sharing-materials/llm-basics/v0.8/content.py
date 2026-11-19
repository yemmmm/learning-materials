"""v0.8 slide content, speaker notes, and sources in presentation order."""
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
 'generation': ('Transformers · 文本生成策略', 'https://huggingface.co/docs/transformers/generation_strategies'),
 'weight_shard': ('Qwen3-8B · 第 1 个 Safetensors 权重分片', 'https://modelscope.cn/models/Qwen/Qwen3-8B/file/view/master/model-00001-of-00005.safetensors'),
 'safetensors_header': ('Safetensors · 分片元数据读取说明', 'https://huggingface.co/docs/safetensors/metadata_parsing'),
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
 'vllm_benchmark': ('vLLM · 压测时延与吞吐量', 'https://docs.vllm.ai/en/v0.33.0/benchmarking/cli/#understanding-the-latency-metrics'),
 'vllm_metrics': ('vLLM · 生产指标与缓存计数', 'https://docs.vllm.ai/en/latest/usage/metrics/'),
 'rag': ('Lewis 等 · RAG', 'https://arxiv.org/abs/2005.11401'),
 'embedding': ('Sentence Transformers · 语义相似性', 'https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html'),
 'rerank': ('Sentence Transformers · 召回与重排', 'https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html'),
 'tools': ('Claude · 工具调用', 'https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview'),
 'agents': ('Anthropic · Workflow 与 Agent', 'https://www.anthropic.com/research/building-effective-agents'),
 'react': ('Yao 等 · ReAct', 'https://arxiv.org/abs/2210.03629'),
 'harness': ('Anthropic · 长任务 Harness', 'https://www.anthropic.com/research/effective-harnesses-for-long-running-agents'),
 'agent_evals': ('Anthropic · Agent 与 Harness 评测', 'https://www.anthropic.com/research/demystifying-evals-for-ai-agents'),
 'mcp': ('MCP · 官方介绍', 'https://modelcontextprotocol.io/docs/getting-started/intro'),
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
         + p('v0.8 · 2026 年 11 月', 'small') + '</div>',
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

add('03 / 分词、生成与加载', '逐个 Token 生成文本', '自回归生成每次预测一个 Token，再把选中的 Token 接回序列，作为下一步的输入。',
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
         + block('自回归（Autoregressive）', p('第一次根据原始输入预测 pending。预测句号时，模型的前文已经包含了 pending。'))
         + block('模型输出结束符', p('当模型预测并选中结束 Token，推理服务识别它并停止生成。用户通常只看到「The claim is pending.」。'))
         + '</div>',
         cls='generation-columns'),
    '这里用 Qwen3-8B 的真实 Token ID 演示预设的续写过程。',
    '【演示】依次点 pending、句号和结束符。自回归指每一步都以当前序列为条件，这个序列包含提示词和此前已生成的 Token。句号是普通 Token，例子最后选中 <|im_end|> 才触发停止。这是 Qwen3-8B 配置的结束标记之一。服务也可以按最大输出长度等限制停下。生成依赖加载好的网络和权重，接下来拆开看。',
    ('generation', 'tokenizer', 'tokenizer_config', 'generation_config'), cls='generation-page')

add('03 / 分词、生成与加载', '网络结构与模型权重', 'Qwen3-8B 的配置文件描述层数和维度，权重文件保存训练得到的参数值。',
    cols('<div class="network-figure">'
         + '<div class="network-art">' + image('neural-network.png', '简化的前馈神经网络，包含输入层、隐藏层、输出层和连接。粗线是示例连接。')
         + '<span class="network-weight">w = 0.8</span></div>'
         + '<div class="network-labels"><b>输入层</b><b>隐藏层</b><b>输出层</b></div>'
         + p('层和连接的排列是结构。粗线旁的数字是权重示例。', 'small')
         + '</div>',
         '<div class="network-files">'
         + '<h3>config.json <small>结构配置节选</small></h3>'
         + code('''"model_type": "qwen3",
"num_hidden_layers": 36,
"hidden_size": 4096,
"vocab_size": 151936''')
         + '<h3>model-00001-of-00005.safetensors <small>解码节选</small></h3>'
         + code('''model.embed_tokens.weight
BF16 · 形状 [151936, 4096]
第 0 行起始值 [0.04956, 0.03711, 0.02917, …]''')
         + '</div>',
         cls='network-columns'),
    '推理框架按配置构建网络，再从分片装入该网络所需的权重。',
    '左图是简化的前馈网络，粗线上的 0.8 是教学示意。右上看配置的 36 层和 4,096 维。右下是从真实二进制分片读出的输入词嵌入张量，形状和 BF16 来自文件头，三个数值从二进制参数区解码并四舍五入。Token ID 对应词嵌入矩阵的一行。框架用 Qwen3 的 Transformer 实现构建各层，读取索引定位权重，例如输入词嵌入在第 1 片、输出层在第 5 片。',
    ('network_diagram', 'config', 'weight_index', 'weight_shard', 'safetensors_header'))

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

add('04 / 模型规格与推理服务', '训练后的模型怎样提供推理服务？', '模型权重是训练交给推理服务的文件。服务启动时加载权重，之后可以接收多次请求。',
    '<div class="serving-setup">'
    '<div><h3>训练</h3><p>根据样本和训练目标更新参数。</p></div>'
    '<span class="serving-arrow"><small>保存</small>→</span>'
    '<div class="serving-weights"><b>模型权重</b><small>.safetensors</small></div>'
    '<span class="serving-arrow"><small>加载</small>→</span>'
    '<div><h3>服务启动</h3><p>以 vLLM 为例。<br>读取配置，加载权重和分词器，开放 API。</p></div>'
    '</div>'
    '<div class="serving-request"><h3>一次推理请求</h3>'
    '<div class="serving-path">'
    '<div><b>应用发送问题和条款</b><p>一晚 560 元，能全额报销吗？<br>每晚限额 500 元，超标须事前审批。</p></div>'
    '<span class="serving-arrow" aria-hidden="true">→</span>'
    '<div><b>已加载的模型</b><p>依据这次输入生成回复</p></div>'
    '<span class="serving-arrow" aria-hidden="true">→</span>'
    '<div><b>服务返回答复</b><p>超标 60 元，需核验事前审批。</p></div>'
    '</div></div>',
    '换一份制度会改变这次推理的输入。服务继续使用同一份模型权重。',
    '上面只在训练产出和服务启动时发生。微调也可能只产出适配器，例如 LoRA。下面是 API 上的一次往返，应用给问题和资料，推理框架组织生成并返回答复。vLLM 和 SGLang 可提供并发推理服务，Transformers 提供模型实现和生成接口，llama.cpp 常用于本地运行 GGUF 模型。接下来看看训练中的不同阶段让模型学到什么。',
    ('files', 'qwen', 'vllm_api', 'lora'), cls='serving-page')

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

add('07 / RAG 与检索', 'RAG 怎样查到条款并回答？', 'RAG（检索增强生成）先按问题找资料，再让模型根据资料作答。差旅制度已提前切片入库并建立索引。',
    '<figure class="rag-journey">'
    '<img data-asset="rag-retrieve-rerank.png" alt="从住宿问题出发，经过查找制度片段、重排序和组装上下文，最终生成回复的五步插图。">'
    '<figcaption><ol class="rag-stages">'
    '<li><h3>提问</h3><p>两晚各花了 560 元呢？</p></li>'
    '<li><h3>召回候选</h3><p>找到住宿标准、机票舱位、超标审批。</p></li>'
    '<li><h3>重排序</h3><p>逐条比较相关性。住宿 §3.2、审批 §3.3 排到前面，机票靠后。</p></li>'
    '<li><h3>组装上下文</h3><p>把「每晚限额 500 元」「超标须事前审批」及问题交给模型。</p></li>'
    '<li><h3>输出回答</h3><p>两晚共 1,120 元，超标 120 元。全额报销要核验审批。</p></li>'
    '</ol></figcaption></figure>',
    '',
    '上一页把两段条款手动写进请求。实际用 RAG 时，先准备可检索的制度片段，保留编号和出处。收到问题后，用向量、关键词或混合检索找一批候选。这里召回同时命中住宿、审批和机票，重排序再逐一比较每段与本轮问题的相关性，把住宿和审批推到前面。应用取前两段交给模型。§3.2 给出每晚 500 元，§3.3 给出审批条件，回答可据此算出两晚超标 120 元。重排序是这个示例中的一步，结果仍要核对版本和适用范围。下一页看语义召回如何用文本向量。',
    ('rag', 'rerank'), cls='rag-page')

add('07 / RAG 与检索', '文本 Embedding 与 Token ID', 'Embedding（嵌入）是用一组数字表示内容特征。语义检索可把问题与资料片段转成向量，再比较相似度。',
    '<div class="embedding-example">'
    '<div><p>「住酒店」</p><p>「住宿标准」</p></div>'
    '<span class="serving-arrow" aria-hidden="true">→</span>'
    '<div class="embedding-model"><b>同一个 Embedding 模型</b></div>'
    '<span class="serving-arrow" aria-hidden="true">→</span>'
    '<div><code>[0.12, −0.34, …]</code><code>[0.10, −0.32, …]</code></div>'
    '</div>'
    + p('两段文字分别得到一个向量。这里的数字为教学示意。', 'small')
    + cols(block('Token ID 是编号', p('例如 Qwen3-8B 词表中 Hello 的编号是 <b>9707</b>。编号接近只表示词表位置接近。')),
           block('Embedding 是向量', p('例如 <b>[0.12, −0.34, …]</b>。在同一个向量空间里，可以按相似度判断哪些内容更相关。')),
           cls='embedding-compare'),
    '',
    '先看住酒店和住宿标准。这两段文字分别进同一个检索模型，得到两组数，应用可以用余弦相似度一类的度量找相关篇章。例子里省略了多数维度，数值是预写的。再想起前面词表中的 Hello，9707 只是查词表或词嵌入矩阵的索引。差旅制度可以走检索，另外一笔 120 新币需要查指定日期的汇率，接下来用工具调用完成。',
    ('embedding', 'vocab'), cls='embedding-page')

add('08 / 工具与自主决策', 'Function Calling 的调用请求', 'Tool 是应用可调用的能力。应用提供工具说明，模型按说明生成名称和参数。',
    cols('<div>' + p('应用提供的工具说明', 'code-label')
         + code('''name: convert_currency
description: 按指定日期的汇率换算金额。
parameters:
  amount: number # 待换算金额
  base: string   # 原币种
  quote: string  # 目标币种
  date: string   # YYYY-MM-DD''') + '</div>',
         '<div>' + p('模型为这笔费用提出的调用', 'code-label')
         + code('''{
  "name": "convert_currency",
  "arguments": {
    "amount": 120,
    "base": "SGD",
    "quote": "CNY",
    "date": "2026-11-08"
  }
}''') + '</div>'),
    '运行环境接到调用请求后执行工具，再把成功结果或错误返回给模型。',
    '指一下左边工具说明中的金额、币种和日期，再看右边由模型填出的参数。此时是模型提出调用。下一页看应用怎样执行这一次换算，并把结果交还模型。',
    ('tools',))

add('08 / 工具与自主决策', '一次工具调用完成换算', '用户询问「按照今天的汇率，120 SGD 能换多少人民币？」',
    buttons('tool', ['提出调用', '收到结果', '回复用户'], cls='screen-only')
    + '<div class="screen-only">'
    + cols('<div class="tool-demo"><div><h3 id="toolTitle">模型提出调用</h3><pre id="toolResult"></pre></div></div>',
           block('回执里需要核对什么',
                 p('<b>汇率</b>　检查币种、日期和换算率。')
                 + p('<b>结果</b>　换算工具计算并返回 636 CNY，模型据此作答。')),
           cls='tool-columns') + '</div>'
    + '<div class="print-only">'
    + flow(('模型提出调用', '把 120 SGD、目标币种 CNY 和日期交给换算工具。'),
           ('应用执行并回传', '工具查到汇率 5.30，计算并返回 636 CNY。'),
           ('模型组织答复', '120 新币折合 636 元，附汇率日期。'))
    + '</div>',
    '',
    '【演示】本例把「今天」设为 2026-11-08。先看模型给出的一次工具请求。应用执行 convert_currency，在一次调用中查询汇率并换算，把汇率和金额一起回传。模型随后依据回执写出 636 元。现在把目标换成提交整笔差旅报销申请，助手还要处理制度和审批。',
    ('tools',), cls='tool-page')

add('08 / 工具与自主决策', 'Workflow 与 Agent 的决策分工', '提交一笔差旅报销申请，需要查制度、换算金额、核验审批。',
    cols(block('Workflow · 程序预先编排',
               p('开发者规定主要步骤和分支。运行时按已写好的条件走。')
               + flow(('查制度', '取得条款'),
                      ('做换算', '按指定日期折算'),
                      ('检查审批', '满足条件后提交'))
               + p('例如程序预设一条分支，缺事前审批时保存草稿并等待补件。', 'small')),
         block('Agent · 模型根据执行反馈选择',
               p('模型根据目标和当前状态，在允许的工具与动作中选下一步。')
               + flow(('判断缺口', '已算出超标额'),
                      ('选取动作', '例如核验审批'),
                      ('观察结果', '再判断是否继续'))
               + '<div class="loop-return">← 工具结果回到下一次决策</div>')),
    '固定流程可以在某个环节让模型动态选择动作。',
    '两边都能处理这笔费用，差别是主要路径由谁决定。左侧由程序定义审批条件与分支。右侧先看结果再判断缺什么，应用按授权执行它选的动作。下一页只改变最后一份材料，看选择怎样改变。',
    ('agents',), cls='workflow-page')

add('08 / 工具与自主决策', 'ReAct 的行动与观察', 'Reasoning + Acting 交替进行。每次工具回执都可能改变下一步行动。',
    '<div class="react-task"><b>任务</b><span>「帮我提交差旅报销申请」</span>'
    '<small>一晚住宿 560 元，另有 120 SGD 外币费用</small></div>'
    + buttons('react', ['找制度', '换外币', '核算', '检查审批', '提交结果'], cls='screen-only')
    + '<div class="approval-options screen-only" id="approvalChoices" hidden><b>审批材料</b>'
    + buttons('approval', ['未提供记录', '已提供记录']) + '</div>'
    + '<div class="react-demo screen-only">'
      '<div class="react-row"><b>当前判断</b><span id="reactReason"></span></div>'
      '<div class="react-row"><b>行动 Action</b><span id="reactAction"></span></div>'
      '<div class="react-row"><b>观察 Observation</b><span id="reactObservation"></span></div>'
      '<div class="react-row"><b>下一步</b><span id="reactNext"></span></div></div>'
    + '<div class="print-only">'
    + flow(('找制度', '每晚 500 元，超标须事前审批'),
           ('换外币', '120 SGD 折合 636 CNY'),
           ('算金额', '合计 1,196 元，住宿超标 60 元'),
           ('检查审批', '材料决定下一步'))
    + cols(block('缺事前审批', p('保存草稿，请用户补件。申请处于待补状态。')),
           block('审批核验通过', p('调用提交工具，按回执确认已提交，返回教学申请单号 DEMO-018。'))) + '</div>',
    '检查结果决定接下来是等待补件，还是提交并返回申请单号。',
    '【演示】用户目标是提交申请。先走完前三步，第四步切换审批记录，再点提交结果。缺记录时保存草稿并向用户要补件。有记录的分支预设审批系统核验通过，应用调用提交工具，收到教学申请单号 DEMO-018 后才报告已提交。整页为离线模拟，判断栏是讲述用的状态摘要。下一页讲模型提出动作后，由谁执行和记住进度。',
    ('react', 'agents'), cls='react-page')

add('09 / Agent 运行环境', '什么是 Harness？', 'Harness 是围绕模型的运行程序。它组织模型调用、执行工具，并管理任务状态和停止条件。',
    '<p class="agent-equation">Agent <span>=</span> LLM <span>+</span> Harness</p>'
    + cols(block('LLM 提出下一步', p('模型根据当前目标和工具返回，判断接下来是核验审批、申请提交，还是向用户索取材料。')),
           block('Harness 运行这一步', p('准备上下文，检查调用权限并执行工具。保存回执，再决定把结果带进下一轮，还是结束本轮。')),
           cls='harness-columns'),
    '例如提交工具返回申请单号，Harness 保存回执，模型据此向用户报告结果。',
    '用这个式子帮助理解分工。上一页 LLM 提出调用提交工具，Harness 检查可执行条件并代为调用，再把真实回执送回模型。它可以记录制度、费用、待补审批和申请单号，也管理权限、重试和费用上限。不同实现会拆成不同模块。下一页看任务中断后怎样恢复这些状态。',
    ('harness', 'agent_evals'), cls='harness-page')

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
        ('审批材料缺失', '保存申请草稿，等待补件', '保留已核对结果，报告申请待补'),
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
    '在这笔报销里，Skill 的说明帮助决定什么时候要看审批。应用可以通过 MCP 接到审批系统，真正查记录的是一个工具。下一页看报销核对的做法怎样写进 Skill。',
    ('mcp', 'skills', 'tools'))

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

add('11 / 多模态与交付', '差旅助手交付的核对说明', '缺少事前审批时，助手保留金额、依据和待补项。',
    '<div class="document-paper report-paper">'
    + '<div class="report-head"><p class="report-total">¥1,196 <small>费用合计</small></p>'
      '<div class="report-status"><b>申请待补，尚未提交</b><p>补件后核验记录是否适用于本次行程。</p></div></div>'
    + '<dl class="report-items">'
      '<div><dt>住宿</dt><dd><b>1 晚 560 元，超出标准 60 元</b><br>制度 v2026.11 §3.2 的每晚限额为 500 元。</dd></div>'
      '<div><dt>外币费用</dt><dd><b>120 SGD 折合 636 元</b><br>2026-11-08 教学汇率为 5.30，计算回执为 636 元。</dd></div>'
      '<div><dt>审批</dt><dd><b>待补本次住宿的事前审批记录</b><br>制度 §3.3 要求超标费用提供事前审批。</dd></div>'
      '</dl></div>',
    '',
    '这页对应 ReAct 演示的缺件分支。一千一百九十六是差旅费用合计。事前审批待补，申请停在草稿状态。请大家指出金额和当前状态的依据。下一页把同样的核对做成应用评测标准。',
    ())

add('回顾与交流', '整项任务的效果与成本', '用同一批报销任务比较不同版本。每个样例先定义正确的业务结果。',
    cols(block('这笔费用怎样判定通过',
               p('<b>金额</b>　换算为 636 元，费用合计 1,196 元，住宿超标 60 元。')
               + p('<b>依据</b>　条款、制度版本和汇率日期可追溯。')
               + p('<b>申请状态</b>　缺件时等待补件，已提交时能查到申请单号。')),
         block('一批任务怎样比较改动',
               p('<b>效果</b>　比较金额、引用与缺件状态的正确率。')
               + p('<b>时延</b>　记录整项任务耗时，包括模型、检索和工具。')
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
    '先独立查看适用的制度原文，再沿检索记录和请求定位丢失或错误使用的证据。任务要求不清时可以改提示词，缺外部资料时可以改检索或接口，计算缺口交给工具。如果携带正确依据后仍反复出现稳定的任务行为问题，再评估是否需要训练。最后补看推理服务的常见指标。')

add('回顾与交流', '推理服务的常见评价指标', '时延按一次模型请求计量。吞吐量和前缀缓存命中率按观测时间段汇总。',
    table(['指标', '怎么量', '看什么'], [
        ('首 Token 时延（TTFT）', '从发出请求到收到首个输出 Token', '开始输出前要等多久'),
        ('每输出 Token 耗时（TPOT）', '首个 Token 之后，平均每个输出 Token 的耗时', '开始后输出得有多快'),
        ('端到端时延（E2E）', '从发出请求到收到完整响应', '这次模型请求多久完成'),
        ('输出吞吐量（Token/s）', '观测期的输出 Token 总数 ÷ 观测时长', '服务每秒输出多少 Token'),
        ('前缀缓存命中率', '命中的前缀 Token 数 ÷ 查询缓存的 Token 数', '输入前缀的计算有多少可复用'),
    ], 'metrics-table'),
    '比较时记录并发量、输入输出长度和缓存冷热。时延可同时看 P50 和 P95。',
    '以 vLLM 客户端压测为例，TTFT 从发出请求量到首个流式输出。输出超过一个 Token 时，TPOT 以端到端时延减去 TTFT，再除以输出 Token 数减一。输出吞吐量按整个服务汇总。前缀缓存复用相同输入前缀的计算，命中率按同一观测期的命中 Token 增量除以查询 Token 增量。P50 是中位数，P95 表示约 95% 的请求在该时延以内。这里量的是模型请求，整笔报销任务还包含检索、工具和申请结果的评测。',
    ('vllm_benchmark', 'vllm_metrics'))

REFERENCE_GROUPS = [
    ('模型与部署', ['llm', 'transformer', 'bert', 'chatgpt', 'files', 'vocab', 'quant', 'distill']),
    ('训练与服务', ['sft', 'rlhf', 'chat', 'vllm_api', 'vllm_benchmark', 'vllm_metrics']),
    ('检索与 Agent', ['rag', 'rerank', 'context', 'tools', 'react', 'harness', 'mcp', 'skills']),
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
        ('离线交互', '聊天模板使用简化示例。换算、审批、申请提交和回执按预设展示。'),
        ('公开模型资料', '仓库文件、词表、配置和规格依据讲稿所列的官方资料。'),
        ('图与票据', '封面、Dense/MoE 与 RAG 图为 AI 生成。前馈网络图来自 Michael Clark。票据为模拟材料。'),
    ], 'materials-table'),
    '',
    '整场交互在本地运行。公开的模型规格、代码和物料出处可在逐页讲稿或同版资料说明中查到。')
