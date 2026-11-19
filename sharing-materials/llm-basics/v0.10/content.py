"""v0.10 slide content, speaker notes, and sources in presentation order."""
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
 'vllm_serving': ('vLLM · 用 API 提供模型服务', 'https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/'),
 'vllm_api': ('vLLM · Chat Completions 请求结构', 'https://docs.vllm.ai/en/latest/api/vllm/entrypoints/openai/chat_completion/protocol/#vllm.entrypoints.openai.chat_completion.protocol.ChatCompletionRequest'),
 'vllm_benchmark': ('vLLM · 压测时延与吞吐量', 'https://docs.vllm.ai/en/v0.33.0/benchmarking/cli/#understanding-the-latency-metrics'),
 'vllm_metrics': ('vLLM · 生产指标与缓存计数', 'https://docs.vllm.ai/en/latest/usage/metrics/'),
 'vllm_features': ('vLLM · 推理服务功能', 'https://docs.vllm.ai/en/latest/features/'),
 'ragas_metrics': ('Ragas · RAG 与工具调用指标', 'https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/'),
 'adk_evals': ('Google ADK · Agent 质量、安全与任务完成', 'https://adk.dev/evaluate/criteria/'),
 'otel_genai': ('OpenTelemetry · 大模型用量和调用链', 'https://opentelemetry.io/blog/2026/genai-observability/'),
 'rag': ('Lewis 等 · RAG', 'https://arxiv.org/abs/2005.11401'),
 'embedding': ('Sentence Transformers · 语义相似性', 'https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html'),
 'rerank': ('Sentence Transformers · 召回与重排', 'https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html'),
 'bge_m3': ('BAAI · BGE-M3 模型卡', 'https://huggingface.co/BAAI/bge-m3'),
 'bge_reranker': ('BAAI · bge-reranker-v2-m3 模型卡', 'https://huggingface.co/BAAI/bge-reranker-v2-m3'),
 'pp_ocr': ('PaddleOCR · PP-OCRv5', 'https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html'),
 'whisper': ('OpenAI · Whisper 语音识别', 'https://github.com/openai/whisper'),
 'vits': ('Kim 等 · VITS 语音合成', 'https://arxiv.org/abs/2106.06103'),
 'yolo11': ('Ultralytics · YOLO11 视觉模型', 'https://docs.ultralytics.com/models/yolo11/'),
 'stable_diffusion': ('Stability AI · Stable Diffusion 3.5', 'https://stability.ai/news-updates/introducing-stable-diffusion-3-5'),
 'seedance': ('ByteDance Seed · Seedance 2.5', 'https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5'),
 'tools': ('Claude · 工具调用', 'https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview'),
 'agents': ('Anthropic · Workflow 与 Agent', 'https://www.anthropic.com/research/building-effective-agents'),
 'react': ('Yao 等 · ReAct', 'https://arxiv.org/abs/2210.03629'),
 'harness': ('Anthropic · 长任务 Harness', 'https://www.anthropic.com/research/effective-harnesses-for-long-running-agents'),
 'harness_definition': ('Google Cloud · Agent Harness 定义', 'https://cloud.google.com/discover/agent-harness'),
 'deep_agents': ('LangChain · Deep Agents 运行能力', 'https://docs.langchain.com/oss/python/deepagents/overview'),
 'agent_evals': ('Anthropic · Agent 与 Harness 评测', 'https://www.anthropic.com/research/demystifying-evals-for-ai-agents'),
 'agent_memory': ('Anthropic · Agent 记忆的组成', 'https://www.anthropic.com/research/components-of-agent-memory'),
 'langgraph_memory': ('LangGraph · 会话内与跨会话记忆', 'https://docs.langchain.com/oss/python/concepts/memory'),
 'adk_compaction': ('Google ADK · 上下文压缩', 'https://adk.dev/context/compaction/'),
 'mcp': ('MCP · 官方介绍', 'https://modelcontextprotocol.io/docs/getting-started/intro'),
 'skills': ('Agent Skills · 官方格式', 'https://agentskills.io/home'),
 'graphrag': ('Microsoft · GraphRAG 项目', 'https://github.com/microsoft/graphrag'),
 'a2a': ('A2A · Agent 间通信协议', 'https://a2a-protocol.org/latest/'),
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

add('开场', '大模型常见概念', '认识大模型怎样运行，应用怎样使用模型，以及 Agent 怎样调用工具完成任务。',
    cols('<div class="cover-copy cover-agenda">'
         + block('模型怎样运行', p('从模型文件和分词，看到逐步生成与训练。'))
         + block('应用怎样使用模型', p('从多轮对话、提示词和上下文进入检索与工具调用。'))
         + block('Agent 怎样完成任务', p('比较固定流程与自主决策，再看模型和运行程序的分工。'))
         + p('v0.10 · 2026 年 11 月', 'small') + '</div>',
         image('model-workbench.png', '由资料、计算器、终端和模型组成的纸艺插图'),
         cls='cover-columns'),
    '',
    '先看真实模型仓库里的文件和分词，再用翻译、会议通知等短例子解释训练、对话和提示词。后面沿一笔报销申请看检索和工具怎样帮助 Agent 做事。最后比较专用模型，讨论应用怎样评测，再根据大家的兴趣补讲。',
    cls='cover')

add('01 / 模型是什么', '人工智能、深度学习与自然语言处理', '',
    cols('<div class="taxonomy"><div><b>人工智能 AI</b><span>让计算机完成需要智能的任务</span>'
         '<div><b>机器学习 ML</b><span>从数据中学习规律</span>'
         '<div><b>神经网络</b><span>训练相互连接的计算单元</span>'
         '<div><b>深度学习 DL</b><span>用多层神经网络学习表示</span></div></div></div></div></div>',
         block('自然语言处理（NLP）', p('让计算机理解或生成人使用的语言。')
               + '<ul class="nlp-examples">'
                 '<li><b>文本分类</b><span>把「无法登录」归到账号故障</span></li>'
                 '<li><b>信息抽取</b><span>从会议通知提取时间和地点</span></li>'
                 '<li><b>翻译与摘要</b><span>翻译英文邮件或提炼会议要点</span></li>'
                 '<li><b>问答与生成</b><span>根据软件文档回答配置问题</span></li>'
                 '</ul>'),
         cls='nlp-columns'),
    '',
    '先从 AI 缩到机器学习，再看到神经网络和多层网络。左边是技术路线，右边是典型语言任务。比如系统读到「周五上午十点在 A305 开会」，可以提取日期、时间和地点。现代大语言模型常用同一个模型处理多类语言任务。',
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
               + p('例如让教师为文章生成摘要，用这些示范训练较小的学生模型。')),
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

add('04 / 模型规格与推理服务', '模型的训练和推理', '以翻译为例，训练让模型从样本中学习，推理用学到的权重处理新输入。',
    '<div class="model-phases">'
    '<section class="phase-panel phase-training">'
    '<h2>训练 <small>更新权重</small></h2>'
    '<div class="phase-sample"><b>训练样本</b>'
    '<p>输入　Good morning.</p><p>参考译文　早上好。</p></div>'
    '<ol class="phase-steps">'
    '<li>预测译文的下一个 Token</li>'
    '<li>与参考译文比较，计算损失</li>'
    '<li>据此更新权重，继续训练</li>'
    '</ol></section>'
    '<div class="weight-handoff">'
    '<div><b>已训练权重</b><code>.safetensors</code></div>'
    '<p>训练后保存<br>服务启动时加载</p>'
    '</div>'
    '<section class="phase-panel phase-inference">'
    '<h2>推理 <small>使用权重</small></h2>'
    '<div class="phase-sample"><b>新的请求</b>'
    '<p>把「Good evening.」翻成中文。</p></div>'
    '<ol class="phase-steps">'
    '<li>把输入转换成 Token</li>'
    '<li>用已加载的权重逐个生成 Token</li>'
    '<li>返回译文 <b>晚上好。</b></li>'
    '</ol></section></div>',
    'vLLM 等推理框架加载模型配置、权重和分词器，通过 API 接收请求并返回生成结果。',
    '左边是监督微调的一条教学样本。训练时，根据输入和参考译文的已知前缀预测下一个 Token，比较预测与目标 Token 计算损失。'
    '优化器据此更新权重。重复这个过程后保存权重，微调也可以保存 LoRA 适配器。'
    '右边收到一条新的翻译请求。vLLM 等推理框架在启动时加载所需文件，通过 API 接收输入，'
    '组织分词、模型计算和逐步生成，再返回译文。服务可以复用已加载的权重处理后续请求。下一页分别看预训练、监督微调与对齐的训练目标。',
    ('sft', 'lora', 'files', 'generation', 'vllm_serving'))

add('05 / 训练与对话', '预训练、监督微调与对齐', '从学习续写，到按指令作答，再到按偏好改进回答。对齐以 InstructGPT 的人工偏好训练为例。',
    cols(block('预训练', p('从大量文本学习预测下一个 Token。')
               + '<div class="document-paper">'
               + p('前文', 'kicker') + p('项目例会定于周五上午……')
               + p('<b>训练目标</b>　预测接下来的「10 点」。') + '</div>'),
         block('监督微调（SFT）', p('给出任务和示范回复，让模型练习按指令作答。')
               + '<div class="document-paper">'
               + p('任务', 'kicker') + p('转述「周五上午 10 点召开项目例会」，保留时间。')
               + p('<b>示范回复</b>　项目例会在周五上午 10 点。') + '</div>'),
         block('偏好对齐', p('让人比较同一问题的多个回答，再用偏好改进模型。')
               + '<div class="document-paper">'
               + p('人工排序', 'kicker')
               + p('<b>更好</b>　项目例会在周五上午 10 点。')
               + p('<b>较差</b>　项目例会在周五。') + '</div>'),
         cls='three-columns training-examples'),
    '',
    '左侧的信号来自原始文本的后续内容。中间的信号来自示范答案，帮助模型学会按任务要求作答。右侧是在学哪种回答更好：标注者给同一问题的候选回答排序，InstructGPT 用排序训练奖励模型，再用评分和 PPO 更新助手。这是偏好对齐的一种做法。对齐是更广的训练目标，监督微调也可以用于对齐。下一页单看对话样本如何教模型扮演助手。',
    ('llm', 'sft', 'rlhf'), cls='training-page')

def dialogue_turn(role, message, cls=''):
    return f'<div class="dialogue-turn {cls}"><b>{role}</b>{p(message)}</div>'

translation_request = '把「上线前请先备份」翻成英文。'
reference_translation = 'Please back up before deployment.'
first_question = dialogue_turn('用户', translation_request)
first_answer = dialogue_turn('助手', reference_translation)
reply_start = dialogue_turn('助手', '从这里续写', 'reply-start')
second_prompt = first_question + first_answer + dialogue_turn('用户', '语气再正式一点。') + reply_start

add('05 / 训练与对话', '续写模型怎样成为对话助手', '监督微调让模型练习在「助手」的位置，按示范回答用户的问题。',
    cols(block('监督微调（SFT）的样本',
               '<div class="document-paper sft-example">'
               + p('输入', 'kicker')
               + '<div class="sft-input">'
               + p('用户：' + translation_request) + p('助手：', 'reply-start') + '</div>'
               + p('参考答案', 'kicker') + p(reference_translation, 'sft-reference')
               + '</div>'
               + p('用参考答案计算损失，更新模型权重。', 'dialogue-caption')),
         block('推理时，从助手的位置开始续写',
               buttons('chat', ['第一轮', '第二轮（带历史）'], cls='screen-only')
               + '<div class="screen-only">'
               + '<div class="document-paper dialogue" data-chat-prompt>' + first_question + reply_start + '</div>'
               + '<div class="document-paper dialogue" data-chat-prompt hidden>' + second_prompt + '</div></div>'
               + '<div class="document-paper dialogue print-only">' + second_prompt + '</div>'
               + p('应用用聊天模板标记角色和轮次，模型续写的内容成为助手的回复。', 'dialogue-caption')),
         cls='dialogue-columns'),
    '下一轮，同一套模板把相关历史和新问题一起送回模型。',
    '【演示】指左边的输入，读出用户要翻译的句子和后面的「助手：」。接下来用下方的参考译文当作训练目标。'
    '监督微调用目标回复的 Token 计算损失，更新权重，让模型更能在助手轮次按指令回答。演示用简化角色标记表示输入和参考答案。'
    '推理时，聊天模板在用户问题后添加助手的起始标记，模型从那里逐个生成 Token。点第二轮。'
    '「语气再正式一点」依赖上一轮译文，因此应用把历史一起传回。Qwen3 的模板用 <|im_start|>assistant 标记开始，用 <|im_end|> 标记结束。',
    ('sft', 'chat', 'tokenizer_config'), cls='dialogue-page')

add('06 / 模型到应用', '提示词是什么，怎样写清楚？', '提示词（Prompt）是给模型的输入。它可以是一句提问，也可以是一份任务说明，附带原文或示例。',
    cols('<div><h3>一份清楚的提示词写明</h3>'
         + '<ol class="prompt-guide">'
           '<li><b>目标</b>　从会议通知提取星期、时间和地点。</li>'
           '<li><b>约束</b>　只用原文。缺失字段填 <code>null</code>。</li>'
           '<li><b>输出格式</b>　用 JSON，时间采用 24 小时制。</li>'
           '</ol>'
         + p('本次输入应得到', 'code-label special-token-label')
         + code('{"day":"周四","time":"15:00","location":null}') + '</div>',
         '<div>' + p('可直接发给模型的提示词', 'code-label')
         + code('''从会议通知里提取星期、时间和地点。
只用原文。缺失字段填 null。
返回 JSON，时间用 24 小时制，字段见示例。

示例输入  周五上午十点在 A305 开项目例会。
示例输出  {"day":"周五","time":"10:00","location":"A305"}

本次输入  周四下午三点开评审会。''') + '</div>',
         cls='prompt-columns'),
    '任务有固定的输出要求时，可以放入少量输入和输出示例（Few-shot）。',
    '「帮我整理好」就是一条提示词，但它没说要什么字段，也没交代缺项怎么处理。右边把字段、约束和格式写清楚，示例说明了 JSON 怎么写。本次输入没有地点，用 null 表示。Few-shot 示例随本次请求送入模型。接下来用一次制度问答，看任务指令之外还需要带哪些上下文。',
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
    '<div><p>「电脑连不上网」</p><p>「网络连接故障排查」</p></div>'
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
    '用户说电脑连不上网，帮助文档的标题是网络连接故障排查。两段文字分别进同一个检索模型，应用可以用余弦相似度一类的度量找相关文档。例子省略了多数维度，数值为教学示意。前面词表里 Hello 的 9707 是定位词嵌入矩阵的一行所用的编号。接下来用汇率换算看工具调用。',
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
         '<div>' + p('模型提出的一次换算调用', 'code-label')
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
    '【演示】用户目标是提交申请。先走完前三步，第四步切换审批记录，再点提交结果。缺记录时保存草稿并向用户要补件。有记录的分支预设审批系统核验通过，应用调用提交工具，收到教学申请单号 DEMO-018 后才报告已提交。整页为离线模拟，判断栏是讲述用的状态摘要。下一页看看是谁把模型调用、工具执行和回执连成循环。',
    ('react', 'agents'), cls='react-page')

add('09 / Agent 运行环境', '什么是 Agent Harness？',
    'Agent Harness 是模型外围的应用运行层。它组织模型调用，接入工具和执行环境，让多步任务能持续运行。',
    '<p class="agent-equation">Agent <span>=</span> LLM <span>+</span> Harness</p>'
    + '<div class="harness-loop">'
    + flow(('Harness 组装输入', '带上目标、相关历史和可用工具，再调用模型。'),
           ('LLM 决定怎么回应', '生成回复，或提出工具名称和参数。'),
           ('Harness 处理输出', '返回回复，或校验请求并实际执行工具。'))
    + '<div class="loop-return">← 继续时，把工具的实际返回结果带回模型</div></div>'
    + '<div><h2 class="harness-capability-title">常见运行能力</h2><div class="harness-capabilities">'
    + block('上下文与记忆', p('检索相关历史，按需压缩上下文。'))
    + block('权限与人工确认', p('按权限和沙箱限制操作，必要时等人确认。'))
    + block('计划与协作', p('调度任务步骤，也可委派给子 Agent。'))
    + block('异常与预算', p('有限重试、暂停或按时限和费用上限停止。'))
    + block('状态与恢复', p('留住会话和执行状态，从中断处继续。'))
    + block('可观测性', p('跟踪各步调用、耗时、用量和错误。'))
    + '</div></div>',
    '',
    'Anthropic 把 Agent Harness 也叫 scaffold，指让模型能够作为 Agent 工作的系统。Google Cloud 强调它处在运行时，负责控制执行循环。'
    '用公式提示分工。模型根据输入给出回复或提出动作。Harness 整理输入、接收输出，在授权范围内执行动作，把实际回执带入下一次调用，并按运行规则继续、暂停或停止。'
    'vLLM 等推理框架运行模型并提供推理接口，应用侧的 Harness 可以把这个接口与工具和执行环境连起来。'
    '上一页的申请提交可以说明闭环。模型提出调用，程序通过外部系统执行，回执确认成功后才报告申请单号。\n\n'
    '下方是典型职责。能力随场景选择。例如高影响操作可以停下来等人工确认，遇到临时故障可以有限重试，长任务可以保存检查点或拆分给子 Agent。'
    '可观测性通过调用链串起模型调用和工具执行，帮助定位慢在哪一步、哪里报错、花了多少用量。接下来展开记忆和上下文压缩。',
    ('agent_evals', 'harness_definition', 'harness', 'deep_agents', 'otel_genai'), cls='harness-page')

add('09 / Agent 运行环境', 'Agent 的记忆怎样起作用？',
    '记忆让 Agent 在后续交互中取用过去的信息。应用把相关内容放入本轮上下文，供模型使用。',
    cols(block('会话内延续',
               p('在同一个会话中，取用相关的历史消息和工具结果。')
               + '<div class="memory-example">'
               + p('「这段翻译保留产品英文名。」')
               + p('接着说「下一段也翻一下」，应用把前面的要求带进来。')
               + '</div>'),
         block('跨会话记忆',
               p('把经确认的偏好、事实或做事方法留给以后的会话。')
               + '<div class="memory-example">'
               + p('「以后翻译技术文档，都保留产品英文名。」')
               + p('另开会话翻译技术文档时，应用查找并带入这条偏好。')
               + '</div>'),
         cls='memory-columns')
    + '<div class="memory-recall"><h2>跨会话记忆的使用过程</h2>'
    + flow(('选择写入', '按设置保存用户确认的长期偏好。'),
           ('按范围检索', '找出与当前用户或项目相关的记忆。'),
           ('放入上下文', '把选中的内容和当前请求一起交给模型。'))
    + '</div>',
    '偏好可能改变。应用可以更正或清除已保存的记忆，并在授权范围内检索。',
    '左侧是会话内连续性，框架也常称它为短期记忆。应用保存或取用同一个会话的历史，挑选本轮需要的部分。'
    '右侧是跨会话的长期记忆，Anthropic 的 Agent 记忆文章用这个较窄的含义。新会话可按用户、项目范围和当前任务检索保存的信息。'
    '举例时强调「这段」与「以后」的适用范围。可以把用户明确要求保留的偏好写入记忆。若用户后来要求中文优先，应以本次要求为准，并可按用户意愿更新长期偏好。'
    '两种做法都依赖应用把信息提供给模型。接下来看看同一个会话越来越长时，应用如何调整每次请求的内容。',
    ('agent_memory', 'langgraph_memory'), cls='memory-page')

compaction_instruction = block('系统指令', p('按已确认的信息写项目例会通知。'))
compaction_latest = block('最新消息', p('「标题再短一点，时间地点保留。」'))

add('09 / Agent 运行环境', '上下文压缩怎样腾出空间？',
    '接近 Token 预算时，可以用较短的摘要替换部分旧消息，让下一轮有空间继续输入和生成。',
    '<div class="compaction-columns">'
    '<section class="compaction-window"><h2>压缩前</h2>'
    + compaction_instruction
    + block('旧历史原文节选', p('最早考虑周四下午，最后确认周五 10:00。<br>会议室先选 B101，后来确认 A305。<br>用户要求通知不超过 100 字。<br>中间还产生了多版措辞不同的草稿。'),
            cls='compaction-history')
    + compaction_latest
    + '</section>'
    + '<span class="serving-arrow" aria-hidden="true">→</span>'
    + '<section class="compaction-window compressed-window"><h2>压缩后</h2>'
    + compaction_instruction
    + block('旧历史摘要', p('例会定于周五 10:00，地点 A305。<br>通知不超过 100 字。'),
            cls='compaction-history')
    + compaction_latest
    + p('留给后续输入和生成的空间', 'compaction-budget')
    + '</section></div>',
    '摘要保留已确认的事实和约束，近期消息保留原文。需要精确信息时回查原始出处。',
    '以项目例会通知为例。在多轮讨论和改稿后，应用可按 Token 阈值或历史长度触发压缩。'
    '这里选出一批旧消息，归纳出仍有效的时间、地点和字数要求，用摘要代替旧消息进入下一轮。系统指令和最新消息保留原文。'
    '运行中还可以裁剪已用过的大段工具结果。重要数字、权限约束和待解问题值得保留。对摘要可能遗漏的内容，可以按需找回原文。'
    '记忆面向后续交互的信息复用，上下文压缩面向每次请求的空间。两种机制可以配合使用。下一页看看工具失败、缺输入或预算耗尽时怎么处理。',
    ('context', 'adk_compaction'), cls='compaction-page')

add('09 / Agent 运行环境', '工具执行与停止条件', '根据实际返回状态处理失败，在权限、时限和预算范围内推进任务。',
    table(['运行中遇到什么', '运行环境怎样处理', '交付时怎么写'], [
        ('文档搜索超时', '按规则有限重试，记录失败状态', '说明检索未完成'),
        ('缺少必要输入', '保存进度，等待用户补充', '说明缺少哪些材料'),
        ('脚本访问未授权目录', '沙箱拦截并记下失败原因', '说明哪些文件待检查'),
        ('达到时限或费用上限', '停止继续调用，保留可恢复的进度', '列出已完成事项与剩余工作'),
    ]),
    '工具执行成功看回执。整项任务能否结案，还要看交付要求和缺项。',
    '文档搜索超时属于运行错误，可以按规则重试。缺输入时，助手列明缺项并等待补充。脚本的资源访问受沙箱约束。接下来看看应用怎样接入工具，以及怎样给 Agent 提供可复用的任务方法。',
    ('harness', 'agents'))

add('10 / 连接与任务方法', 'Tool、MCP 与 Skill 的分工', '以排查构建失败为例，分别看要执行的动作、怎样接入工具，以及排查步骤。',
    cols(block('Tool（工具）', p('<b>执行什么</b>') + p('按构建编号查询日志，返回失败阶段和日志内容。')),
         block('MCP（协议）', p('<b>怎样接入</b>') + p('MCP 全称 Model Context Protocol。应用通过它发现并调用构建平台提供的工具。')),
         block('Skill（任务技能包）', p('<b>按什么方法排查</b>') + p('先定位失败阶段，再对照上次成功构建，按模板记录证据。')),
         cls='three-columns')
    + note('工具可以直接接入，也可以通过 MCP 接入。Skill 的说明可以引用工具，具体接入方式由应用决定。'),
    '',
    '这里的工具负责读构建日志，MCP 是应用接入这项能力时可以使用的协议。Skill 给出排查顺序和报告要求，也可以说明何时调用日志查询工具。下一页看同一个 Skill 怎样按需读入。',
    ('mcp', 'skills', 'tools'))

add('10 / 连接与任务方法', 'Skill 的任务说明与按需加载', 'Agent Skills 以 SKILL.md 保存任务说明，可以附带参考内容、脚本与模板。',
    cols('<div>' + p('构建排查 Skill 的示例目录', 'code-label')
         + code('''build-triage/
├── SKILL.md
├── references/
│   └── failure-types.md
├── scripts/
│   └── extract-errors.py
└── assets/
    └── report-template.md''') + '</div>',
         block('收到构建排查任务时',
               p('<b>发现</b>　用名称和描述判断是否适用。')
               + p('<b>启用</b>　读取 SKILL.md，找到排查顺序。')
               + p('<b>使用</b>　按失败类型查看参考资料，写报告时再读取模板。'))),
    '加载的说明会成为本轮可用的信息。工具和脚本仍由运行环境执行。',
    '先用名称和描述选择排查 Skill，再读说明。碰到不熟悉的错误类型才打开参考文件，写结论时再读报告模板。接下来看看哪些应用能力可以交给专用模型。',
    ('skills',))

add('11 / 其他模型', 'LLM 之外的常见模型', '从任务需要的输入与输出，判断该用哪类模型。',
    table(['模型类型', '输入', '输出', '代表模型或系列'], [
        ('文本向量（Embedding）', '文本', '用于检索的向量', 'BGE-M3'),
        ('重排序（Reranker）', '查询和候选片段', '相关性分数', 'bge-reranker-v2-m3'),
        ('文字识别（OCR）', '扫描件或照片', '识别出的文字与位置', 'PP-OCRv5'),
        ('目标检测', '图像', '目标类别和位置框', 'YOLO11'),
        ('语音识别（ASR）', '语音', '转写文本', 'Whisper'),
        ('语音合成（TTS）', '文本', '合成语音', 'VITS'),
        ('图像生成', '文字提示', '生成图像', 'Stable Diffusion 3.5'),
        ('视频生成', '文字提示，可加图像、音频或视频参考', '生成带声音的视频', 'Seedance 2.5'),
    ], 'other-models-table'),
    '',
    '先从前面见过的 Embedding 和 Reranker 开始，前者给文本算向量，后者给查询和候选打相关性分。OCR 是从图里认字，目标检测是找图里的对象和位置。语音识别与合成的输入输出方向相反。图像生成的输出可以是一张图，Seedance 2.5 则能根据文字和参考素材生成带声音的视频。右边是各任务的代表模型。',
    ('bge_m3', 'bge_reranker', 'pp_ocr', 'yolo11', 'whisper', 'vits', 'stable_diffusion', 'seedance'))

add('12 / 评价指标', '大模型应用的常见评价指标', '用业务样题评价结果，用监控和压测衡量服务。',
    cols(
        '<section><h2>质量与安全</h2>'
        + block('答案质量', p('<b>正确率</b>　按参考答案或评分规则判定。<br><b>有据性</b>　结论是否有检索到的资料支持。'))
        + block('任务完成', p('<b>任务成功率</b>　按实际结果核对任务是否达标。<br><b>工具调用正确率</b>　核对工具和参数。'))
        + block('安全', p('<b>越权拦截率</b>　应拦截的测试中成功拦截的比例。<br><b>误拦率</b>　合法任务被错误拦截的比例。'))
        + '</section>',
        '<section><h2>服务与成本</h2>'
        + block('响应时延', p('<b>首 Token 时延（TTFT）</b>　等待首个输出 Token。<br><b>每 Token 耗时（TPOT）</b>　首 Token 后平均每个 Token 的耗时。<br><b>端到端时延</b>　等待完整响应，可看 P50、P95。'))
        + block('容量与稳定性', p('<b>吞吐量</b>　服务每秒输出的 Token 数。<br><b>前缀缓存命中率</b>　查询缓存的 Token 中命中的比例。<br><b>错误率、超时率</b>　按总请求数统计。'))
        + block('使用成本', p('记录输入与输出用量、API 费用或自部署资源成本。<br><b>每个成功任务的成本</b> = 总成本 ÷ 成功任务数。'))
        + '</section>',
        cls='evaluation-columns'),
    '100 道问答题中，98 次正常返回，87 道题答对。请求完成率 98%，任务成功率 87%。',
    '按实际任务定义达标条件。知识问答可以分别测是否检索到所需证据、结论是否有证据支持，以及答案是否符合参考答案。'
    '工具型 Agent 可以核对工具与参数，并用数据库记录或操作结果验证任务终态。重复运行同一批任务还能观察结果的一致性。'
    '评估安全时分别准备应拦截的任务和合法任务，统计越权拦截率与误拦率。\n\n'
    '以 vLLM 客户端压测为例，首 Token 时延 TTFT 从发出请求计到收到首个输出 Token。'
    '输出超过一个 Token 时，TPOT 等于端到端时延减去 TTFT，再除以输出 Token 数减一。'
    '输出吞吐量按观测期的输出 Token 总数除以观测时长。前缀缓存命中率按同一观测期的命中 Token 增量除以查询 Token 增量。'
    'P50 是中位数，P95 表示约 95% 的请求在该时延以内。比较时固定并发、输入输出长度分布和缓存冷热。'
    '应用层的端到端耗时还包括检索、工具和多次模型请求。\n\n'
    '用页上的教学数字说明计量口径。一次问答对应一次请求，100 次中有 98 次正常返回，最终有 87 道题答对。'
    '如果这一批总共花了 8.70 元，每个成功任务成本为 0.10 元。总成本包括失败和重试的开销，比较时用同一批任务和一致的计费范围。',
    ('vllm_benchmark', 'vllm_metrics', 'ragas_metrics', 'agent_evals', 'adk_evals', 'otel_genai'))

add('回顾与交流', '概念回顾与可选补讲', '',
    '<div class="recap-layout">'
    '<section class="reviewed-topics"><h2>本次已讲</h2><div class="concept-grid">'
    + block('AI 与语言模型', p('AI、机器学习、神经网络、深度学习、NLP、LLM<br>RNN / LSTM、Transformer、BERT、GPT‑3.5、ChatGPT'))
    + block('模型文件与运行', p('配置、权重、Safetensors、GGUF、分词器、词表、Token ID<br>自回归、结束符、托管 API、自行部署、推理框架'))
    + block('架构与训练', p('Dense / MoE、总参数与激活参数、低精度、量化、蒸馏<br>AWQ、GPTQ、预训练、SFT、偏好对齐'))
    + block('对话与检索', p('聊天模板、多轮对话、提示词、Few-shot、上下文窗口<br>上下文工程、RAG、召回、重排、Embedding'))
    + block('工具与 Agent', p('Function Calling、Workflow、Agent、ReAct、Harness<br>记忆、上下文压缩、沙箱、停止条件、MCP、Skill'))
    + block('专用模型与指标', p('OCR、目标检测、ASR、TTS、图像与视频生成、任务成功率<br>TTFT、TPOT、端到端时延、吞吐量、前缀缓存命中率、成本'))
    + '</div></section>'
    + '<section class="followup-topics"><h2>可选补讲</h2><div class="concept-grid">'
    + block('模型与模态', p('VLM、VLA、全模态、世界模型<br>Encoder / Decoder、ViT、Diffusion、DiT'))
    + block('训练与对齐', p('PEFT、LoRA、QLoRA、持续预训练<br>RLHF、RLAIF、DPO、GRPO、合成数据'))
    + block('生成与推理', p('Temperature、Top‑p、Top‑k、CoT<br>推理模型、Test-time Scaling<br>结构化输出（JSON Schema）'))
    + block('推理加速', p('Prefill / Decode、KV Cache、PD 分离<br>FlashAttention、PagedAttention<br>连续批处理、投机解码'))
    + block('知识检索', p('向量数据库、ANN / HNSW、BM25<br>混合检索、查询改写、GraphRAG<br>Agentic RAG、多模态 RAG'))
    + block('Agent 编排', p('模型路由、Plan-and-Execute、A2A<br>多 Agent 协作、Subagent、HITL<br>Coding Agent、Computer Use'))
    + block('评测与观测', p('Benchmark、Golden Dataset<br>LLM-as-a-Judge、Pass@k、Trace、Span'))
    + block('安全与治理', p('Guardrails、提示注入、越狱、红队测试<br>最小权限、敏感信息脱敏、审计日志'))
    + '</div></section>'
    + '</div>',
    '',
    '先顺着模型、应用和 Agent 快速回顾，再请听众从右侧选感兴趣的词。\n\n'
    'VLM 怎样理解图片？Diffusion 和 DiT 是怎样的关系？\n'
    '为什么微调时可以只训练 LoRA 适配器？DPO、GRPO 分别利用什么训练信号？\n'
    'Temperature 和 Top-p 怎样影响采样？怎样约束模型返回符合 JSON Schema 的结果？\n'
    'Prefill 处理输入，Decode 逐步生成。KV Cache 保存了什么？投机解码怎样减少生成时的等待？\n'
    '什么时候把向量检索与关键词检索结合？GraphRAG 如何用图表示实体及其关系？\n'
    '怎样按任务选模型？多个 Agent 如何协作，什么情况下该请人确认？\n'
    '怎样用一套固定样题比较两版应用？能否用 Trace 追到其中哪一步出错？\n'
    '系统怎样识别来源不可信的指令？何处检查身份和工具权限？',
    ('vllm_features', 'lora', 'generation', 'graphrag', 'a2a', 'agent_evals', 'otel_genai'),
    cls='recap-page')

REFERENCE_GROUPS = [
    ('模型与部署', ['llm', 'transformer', 'bert', 'chatgpt', 'files', 'vocab', 'quant', 'distill', 'seedance']),
    ('训练、服务与评测', ['sft', 'rlhf', 'chat', 'vllm_api', 'vllm_benchmark', 'vllm_metrics', 'ragas_metrics', 'agent_evals']),
    ('检索与 Agent', ['rag', 'rerank', 'context', 'tools', 'react', 'harness_definition', 'harness', 'mcp', 'skills']),
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

add('附录 / 参考资料', '案例数据与演示口径', '分词和模型文件来自真实仓库，业务输入和交互结果用于教学。',
    table(['内容', '口径'], [
        ('教学示例', '会议通知、构建日志、差旅制度、金额及汇率为教学设定。'),
        ('分词与生成', '分词和 Token ID 经 Qwen3-8B 的分词器核对。逐步续写是预写演示。'),
        ('离线交互', '聊天模板使用简化示例。换算、审批、申请提交和回执按预设展示。'),
        ('公开模型资料', '仓库文件、词表、配置和规格依据讲稿所列的官方资料。'),
        ('示意图', '封面、Dense/MoE 与 RAG 图为 AI 生成。前馈网络图来自 Michael Clark。'),
    ], 'materials-table'),
    '',
    '整场交互在本地运行。公开的模型规格、代码和物料出处可在逐页讲稿或同版资料说明中查到。')
