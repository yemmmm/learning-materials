"""Build the v3.6 release as one offline HTML deck; source text, CSS and JS remain editable."""
from pathlib import Path
import base64, html, json, re
from fontTools import subset
from fontTools.ttLib import TTFont
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SLIDES=[]
def esc(s):return html.escape(str(s),quote=True)
def panel(title,body,cls=''):
 return f'<section class="panel {cls}"><h3>{title}</h3>{body}</section>'
def p(s,cls=''):return f'<p class="{cls}">{s}</p>'
def bullets(items):return '<ul>'+''.join(f'<li>{s}</li>' for s in items)+'</ul>'
def row(k,v):return f'<div class="row"><b>{k}</b><span>{v}</span></div>'
def tag(s):return f'<span class="tag">{s}</span>'
def call(s,cls=''):return f'<div class="callout {cls}">{s}</div>'
def grid(*items,cls='two'):return f'<div class="grid {cls}">'+''.join(items)+'</div>'
def flow(items,labels=None):
 labels=labels or ['→']*(len(items)-1)
 return '<div class="flow">'+''.join(f'<div class="flow-node">{x}</div>'+ (f'<div class="flow-link">{labels[i]}</div>' if i<len(items)-1 else '') for i,x in enumerate(items))+'</div>'
def btn(label,action,extra='',active=False):return f'<button class="choice {"selected" if active else ""}" data-action="{action}" {extra}>{label}</button>'
def add(title,lead,body,take,note='',notes='',sources=(),cls=''):
 SLIDES.append(dict(title=title,lead=lead,body=body,take=take,note=note,notes=notes,sources=list(sources),cls=cls))
def snode(x,y,w,h,t,sub='',kind='',attrs=''):
 return f'<g {attrs}><rect class="model-node {kind}" x="{x}" y="{y}" width="{w}" height="{h}"/><text class="node-title {kind}" x="{x+w/2}" y="{y+(43 if sub else h/2+11)}" text-anchor="middle">{t}</text>'+ (f'<text class="node-sub {kind}" x="{x+w/2}" y="{y+79}" text-anchor="middle">{sub}</text>' if sub else '')+'</g>'
def sedge(d,label='',x=0,y=0,kind='',attrs=''):
 return f'<g {attrs}><path d="{d}" class="model-edge {kind}" marker-end="url(#arrow)"/>'+ (f'<text class="edge-text" x="{x}" y="{y}" text-anchor="middle">{label}</text>' if label else '')+'</g>'
def svg(s,view='0 0 1000 550'):return f'<svg class="model" viewBox="{view}" role="img" aria-label="业务概念及关系示意">{s}</svg>'
S={'gruber':('本体定义 · Tom Gruber','https://tomgruber.org/writing/definition-of-ontology/'),'rdf':('RDF 1.1 Primer · W3C','https://www.w3.org/TR/rdf11-primer/'),'owl':('OWL 2 Primer · W3C','https://www.w3.org/TR/owl2-primer/'),'kg':('Knowledge Graphs · Hogan 等','https://arxiv.org/abs/2003.02320'),'project':('OntoWeave · 项目与版本需求','https://github.com/yemmmm/ontology-platform')}
S.update({
 'expert':('MYCIN 原著 · 系统结构与规则推理','https://people.dbmi.columbia.edu/~ehs7001/Buchanan-Shortliffe-1984/Chapter-04.pdf'),
 'deep':('Deep Learning · LeCun、Bengio、Hinton','https://www.nature.com/articles/nature14539'),
 'transformer':('Attention Is All You Need · Vaswani 等','https://arxiv.org/abs/1706.03762'),
 'nesy':('Neurosymbolic AI — Why, What, and How · Sheth 等','https://arxiv.org/abs/2305.00813'),
 'ibm':('神经符号 AI · IBM Research','https://research.ibm.com/topics/neuro-symbolic-ai'),
 'skos':('SKOS Primer · W3C','https://www.w3.org/TR/skos-primer/'),
 'swrl':('SWRL · W3C Member Submission','https://www.w3.org/submissions/SWRL/'),
 'owls':('OWL-S · W3C Member Submission','https://www.w3.org/submissions/OWL-S/'),
 'sparql':('SPARQL 1.1 Overview · W3C','https://www.w3.org/TR/sparql11-overview/'),
})

S.update({
 'ontology101':('Ontology Development 101 · Noy 与 McGuinness','https://protege.stanford.edu/publications/ontology_development/ontology101-noy-mcguinness.html'),
 'ontologyChallenges':('本体工程挑战 · Tudorache (2020)','https://journals.sagepub.com/doi/pdf/10.3233/SW-190382'),
 'ontologyDebug':('本体补全与纠错 · Lambrix','https://arxiv.org/abs/1908.03171'),
 'go':('Gene Ontology · 已有应用与领域背景','https://geneontology.org/docs/introduction-to-go'),
})

# === 01 · A concrete business object opens the story ===
add('本体论思想在agent中的应用','业务含义怎样成为 Agent 可用的知识',grid(
 '<div class="cover-copy"><p class="eyebrow">从一张差旅申请出发</p><h2>找到一个人，<br>先理解一组关系。</h2><p>一张申请、一条制度、几种组织关系。<br>如何把“找领导”变成明确可核对的判断？</p>'+call('今天串起三个问题：<br><b>本体是什么？Agent 怎样使用？平台承担什么？</b>')+'</div>',
 '<div class="cover-visual"><img class="cover-art" src="__COVER__" alt="关系网络装饰"><section class="application"><div class="application-top"><h3>差旅申请</h3><span>T-101</span></div>'+row('对象','一张差旅申请')+row('问题','该找谁审批？')+row('难点','“领导”指哪一种角色？')+row('线索','政策与当前组织事实')+'<p class="policy-line">下一页：用一张关系图拆开这个问题。</p></section></div>')+'<div class="chapter-road"><span>01 认识本体</span><i>→</i><span>02 两条 AI 路线</span><i>→</i><span>03 Agent 协作</span><i>→</i><span>04 OntoWeave</span></div>',
 '把业务里默认理解的含义，变成能够查询、共享和核对的知识。','虚构差旅案例，用于概念教学。',
 '大家好，今天分享的主题是“本体论思想在 agent 中的应用”。我们主要讨论知识工程里的本体，以及它怎样帮助 Agent 理解和处理业务。\n\n我们先从一张差旅申请开始。员工提交了申请，问助手：“这张单应该找谁审批？”看起来只要找出一个名字就行。但真正往下做，就会遇到几个问题：这里说的“领导”，是直属主管，还是部门负责人？应该按哪条政策找？这个人现在还是负责人吗？\n\n我们平时能顺利处理这些问题，是因为脑子里已经有了一套对业务的理解。今天我们要讨论的，就是怎样把这种理解明确下来，让软件和不同的 Agent 也能共同使用。\n\n接下来，我们先看什么是本体，再看看它与大模型怎样配合，最后介绍 OntoWeave 怎样支持这份业务知识的构建和使用。我们就沿着这张申请，一步一步往下走。',cls='cover')

# === 02 · Different relationships lead to different people ===
casegraph=svg(snode(30,145,210,110,'张三','申请人','dark')+snode(425,40,230,110,'研发部','当前所属部门')+snode(755,40,210,110,'李敏','部门负责人','soft','data-person="head"')+snode(425,330,230,110,'王强','直属主管','','data-person="manager"')+sedge('M240 180 H330 V95 H425','所属部门',325,60,attrs='data-route="head"')+sedge('M655 95 H755','负责人',705,65,attrs='data-route="head"')+sedge('M135 255 V385 H425','直属主管',290,355,attrs='data-route="manager"'), '0 0 1000 480')
add('张三的差旅申请，该由谁审批？','同一个人关联着多种业务角色；政策决定本次沿哪一条关系寻找。',
 '<div class="policy-banner"><b>审批政策</b><span id="policyText">由申请人当前所属部门的负责人审批</span></div>'+grid(panel('先看事实',casegraph,'graph-panel'),panel('再把政策中的词对应到关系',row('所属部门','张三当前归属的组织单元：研发部。')+row('部门负责人','负责这个部门的人：李敏。')+row('直属主管','直接管理张三的人：王强。')+call('<b id="policyAnswer">本例应由李敏审批。</b><span id="policyReason">“部门负责人”与“直属主管”是两种关系。</span>','answer')+'<div class="choices">'+btn('本例：部门负责人','policy','data-value="head"',True)+btn('对照：若改为直属主管','policy','data-value="manager"')+'</div>','compact')),
 '选中正确的人，依赖政策含义、关系路径与当前事实三者配合。','切换仅用于比较政策含义，不改变后续贯穿案例。',
 '这张申请的申请人是张三。张三属于研发部，研发部的负责人是李敏，张三的直属主管则是王强。这几条信息都成立，但它们代表的关系不同。\n\n我们再看政策：这类申请，由申请人当前所属部门的负责人审批。这里已经告诉我们应该怎么找：先找到张三所属的部门，再找到这个部门的负责人。所以，这次应当由李敏审批。\n\n王强虽然也是张三的领导，但“直属主管”这条关系并不符合本次政策。假如政策改成“由直属主管审批”，答案就会变成王强。人员没变，组织信息也没变，改变的是政策指定的关系。\n\n这个例子说明，我们要交给 Agent 的，除了几个名字，还包括这些名字之间到底是什么关系，以及当前问题应该使用哪一种关系。把这些含义说清楚，就走到了本体所关心的问题上。')

# === 03 · Definition with operational examples ===
add('本体：对领域语义的明确建模','把“大家大概知道”的词语和联系，整理为可以共同引用的定义。',
 '<blockquote>本体是对一个领域中概念、关系<br>及其语义约定的明确建模。</blockquote>'+grid(
 panel('概念：我们在说什么',p('员工、部门、差旅申请，各自代表什么？')+row('员工','组织中的人员类别。')+row('差旅申请','提出出差安排与审批请求的业务对象。')),
 panel('关系：对象怎样关联',p('把“有关”改成含义明确的关系。')+flow(['申请','员工','部门'],['申请人','所属部门'])+p('负责人关系说明：谁负责哪个部门。','small')),
 panel('语义约定：哪些含义成立',p('经理是一类员工；部门负责人是员工。')+p('本例审批政策使用申请人<strong>当前所属部门</strong>的负责人。')+p('分类、适用范围和未知，都需要明确说明。','small')),cls='three')+
 call('<b>明确建模带来的变化：</b>“找领导审批” → 明确是哪一种领导、沿什么关系找、适用于什么申请。'),
 '核心是表达当前用途需要的业务含义，让不同使用者能引用同一份知识。','此处讨论知识工程中的本体（Ontology）。',
 '在知识工程里，我们可以把本体理解为：对一个领域中的概念、关系，以及它们的语义约定，进行明确的建模。\n\n这句话稍微展开一下。先说概念。员工、部门、差旅申请，这些词分别指什么？再说关系。谁提交了申请，谁属于哪个部门，谁负责这个部门？最后是语义约定，比如经理是一类员工，部门负责人应该是员工，本次审批要使用当前所属部门的负责人。\n\n大家可能会说，这些东西我们本来就知道。对，但不同的人未必知道得一样。有的人一听到“领导”就想到直属主管，有的人想到部门负责人。只要这份含义没有明确下来，信息即使查得很全，也可能用错。\n\n本体的价值，就是让这些理解有一个可以共同引用的表达。我们不必一开始就描述整个企业，只需要先把当前问题依赖的概念、关系和条件讲清楚。\n\n理解到这里，还需要分清一件事：业务本身、我们建立的模型，以及保存模型的技术，是三个不同层次。',sources=['gruber'])

# === 04 · Three levels, one continuous example ===
add('现实世界、本体、形式表达','先分清“所描述的对象”“对领域的理解”和“记录这些含义的方式”。',
 grid(panel('01 现实世界',p('实际发生了什么？','question')+'<div class="specimen"><b>张三 · 研发部</b><p>张三提交申请 T-101。<br>李敏担任研发部负责人。</p><hr><p>组织、人员和业务事件持续变化。</p></div>'+p('从业务材料、访谈与系统中获得证据。','small')),
 panel('02 本体',p('我们怎样理解这个领域？','question')+flow(['差旅申请','员工','部门'],['申请人','所属部门'])+row('概念','员工、部门、申请')+row('关系','申请人、所属部门、负责人')+row('约定','审批政策使用当前部门负责人'),'accent'),
 panel('03 形式表达',p('怎样让软件处理这些含义？','question')+'<div class="specimen"><b>RDF / OWL 等</b><p>把已确认的领域含义<br>编码为软件可处理的声明。</p></div>'+p('下一页看：图表达与逻辑语义<br>各自承担什么作用。')+p('技术表达应忠实承载已经确认的业务含义。','small')),cls='three')+
 '<div class="bridge"><span>观察、访谈与抽象</span><span>编码、保存与交换</span></div>'+call('<b>本体 ≠ RDF/OWL。</b>前者关注领域语义；后者是表达这些语义的相关技术。'),
 '先明确表达什么，再选择适合的表达技术。','实际保存的本体当然有具体形式；三层区分用于澄清各自关注点。',
 '请大家从左往右看。\n\n左边是现实世界。张三确实提交了一张申请，李敏在某个时间担任研发部负责人。这些是业务中发生的事情，它们会随着人员调动和组织变化而改变。\n\n中间是本体。我们从现实中选出与任务有关的内容，明确什么是员工，什么是部门，什么叫所属部门，什么叫负责人，以及审批政策怎样使用这些关系。这里做的是对业务的理解和抽象。\n\n右边是形式表达。前面确认的含义，需要用软件能够处理的方式记录下来，才方便保存、交换、查询和计算。RDF、OWL 就属于这一层相关的技术。\n\n比如，“经理是一类员工”这条含义，我们可以先用自然语言讨论清楚，再用形式语言表达。业务含义与它的编码方式有关联，但不能直接画等号。因此，理解本体时，我们首先关注的是要表达什么，然后才选择用什么技术表达。\n\n顺着这个区分，下一页我们就来看看 RDF 和 OWL 各自做了什么。',sources=['gruber','rdf','owl'])

# === 05 · Technology with legible examples ===
add('RDF 与 OWL 分别做什么','RDF 提供可连接的图表达，OWL 为本体声明提供形式语义。',
 grid(panel('RDF：把知识写成图',flow(['张三','研发部'],['所属部门'])+'<div class="triple-labels"><span>主体 Subject</span><span>谓词 Predicate</span><span>对象 Object</span></div><pre>:ZhangSan :memberOf :Research .\n:Research :head :LiMin .</pre>'+bullets(['一条陈述连接两个对象；共享对象让陈述连接成图。','通过明确标识区分同名对象，通过谓词表达关系。','既可以陈述具体事实，也可以承载定义。'])),
 panel('OWL：让声明有明确逻辑含义',row('分类','经理是一类员工。')+row('互斥','员工与部门是互斥类别。')+'<pre>SubClassOf(:Manager :Employee)\nDisjointClasses(:Employee :Department)</pre>'+bullets(['软件依据形式语义计算逻辑后果。','能够做何种推理，取决于表达范围和所用工具。','OWL 可与 RDF 一起使用。']),'accent'))+
 call('<b>读懂示例：</b>RDF 片段连接具体对象；OWL 声明说明分类与互斥。前者组织陈述，后者让软件按逻辑处理声明。'),
 'RDF 把陈述连接成图；OWL 为本体声明赋予形式语义。','代码省略前缀声明，仅展示结构；RDFS 也提供基础分类词汇。',
 '先看 RDF。它用一种很简单的结构记录陈述：谁，通过什么关系，连接到谁或者什么值。比如，“张三，所属部门，研发部”，就是一条陈述。“研发部，负责人，李敏”，又是一条陈述。\n\n这两条陈述共享了“研发部”这个对象，于是就连成了一条路径。很多这样的陈述连接起来，就形成了图。屏幕左边的代码，只是把这两句话写成一种具体格式，今天不用记语法，理解这个结构就够了。\n\n再看 OWL。它可以为本体声明赋予明确的逻辑含义。例如，我们声明“经理是一类员工”，或者声明“员工和部门是互斥的类别”。支持这些语义的工具，就能进一步计算哪些结论成立，哪些陈述存在矛盾。\n\n所以，RDF 帮我们把陈述连接起来，OWL 帮我们表达更明确的逻辑语义。它们可以配合使用。具体能推导到什么程度，还取决于模型表达了什么，以及采用了什么工具。\n\n围绕 RDF 和 OWL，还有一些经常一起出现的技术。我们先用一页认识它们各自解决什么问题，再回到本体模型本身。',sources=['rdf','owl'])

# === 06 · A brief map of related semantic-web technologies ===
technologies=[
 ('SKOS','概念词表','组织概念的规范名称、别名、上下位与关联关系，便于统一术语。','本例词表：“差旅”的别名为“出差”，下位概念为“国内差旅”。'),
 ('SWRL','条件规则','将“如果……那么……”规则与 OWL 本体结合，供规则推理工具使用。','适用本例政策 + 员工所属部门 + 部门负责人 → 对应审批人。'),
 ('OWL-S','服务描述','用本体描述 Web 服务能做什么、输入输出及调用方式，辅助发现与组合。','“查询审批人”服务：输入申请编号，输出审批人，并描述调用信息。'),
 ('SPARQL','RDF 图查询','按关系模式查询 RDF 图，可查找、筛选和汇总已表达的知识。','图中已有相关事实时，沿“申请 → 申请人 → 部门 → 负责人”查到李敏。'),
]
add('相关技术速览：词表、规则、服务与查询','围绕 RDF / OWL，按任务选用不同技术；先知道它们各自解决什么问题。',
 '<table class="ai-comparison tech-table"><thead><tr><th scope="col">技术</th><th scope="col">主要用途</th><th scope="col">差旅场景中的例子</th></tr></thead><tbody>'+''.join(f'<tr><th scope="row"><b>{name}</b><small>{role}</small></th><td>{use}</td><td>{example}</td></tr>' for name,role,use,example in technologies)+'</tbody></table>'+
 call('<b>技术之间的关系：</b>RDF 提供图表达基础，OWL 表达逻辑语义；词表、规则、服务描述与查询可在此基础上按需配合。'),
 '按用途记忆：SKOS 管词表，SWRL 写规则，OWL-S 描述服务，SPARQL 查图。','教学示例；SWRL、OWL-S 为 W3C 成员提交方案，不代表 OntoWeave 已支持本页全部能力。',
 '除了刚才的 RDF 和 OWL，还有这四个常见名字。大家先按用途记就可以。\n\nSKOS 用来组织概念词表。比如，我们把“差旅”作为规范名称，把“出差”记作别名，再关联“国内差旅”这样的下位概念。这样，不同说法就有了统一的参照。\n\nSWRL 用来把“如果……那么……”的规则与 OWL 本体结合。例如，在条件齐全时，根据所属部门和部门负责人关系，表达对应的审批人规则。真正执行时，需要支持这类规则的工具。\n\nOWL-S 用本体描述服务。比如一个“查询审批人”的服务，需要什么输入，会给出什么输出，以及怎样调用。这些描述可以帮助服务的发现与组合。\n\nSPARQL 用来查询 RDF 图。如果图里已经有相关事实，就可以按关系模式沿着申请、申请人、部门、负责人去查找答案。\n\n简单记就是：词表、规则、服务描述和图查询。实际项目按需要选择。现在对这些表达技术有了一个整体印象，我们回到本体模型，看看它通常包含哪些内容。',sources=['skos','swrl','owls','sparql'],cls='semantic-technologies')

# === 07 · Selectable ontology ingredients ===
model5=svg(snode(45,35,230,90,'经理','','','data-kind="class axiom"')+snode(45,230,230,90,'员工','','','data-kind="class"')+snode(585,230,250,90,'部门','','','data-kind="class"')+snode(45,445,230,90,'张三','','dark','data-kind="individual"')+snode(585,445,250,90,'研发部','','dark','data-kind="individual"')+sedge('M160 125 V230','是一种',233,185,'dashed','data-kind="axiom"')+sedge('M275 275 H585','隶属于',430,255,attrs='data-kind="relation"')+sedge('M160 445 V320','属于这个类',258,394,'dashed','data-kind="individual"')+sedge('M710 445 V320','属于这个类',805,394,'dashed','data-kind="individual"')+sedge('M275 490 H585','隶属于',430,470,attrs='data-kind="relation"')+'<g data-kind="property"><rect x="385" y="40" width="470" height="110" class="property-box"/><text x="410" y="82" class="node-sub">员工的属性：姓名、入职时间</text><text x="410" y="123" class="node-sub">张三的姓名值：“张三”</text></g>','0 0 930 570')
items=[('class','类 Class','员工、经理、部门','定义概念与类别'),('property','属性 Property','姓名、入职时间','描述对象具有什么特征'),('relation','关系 Relation','员工隶属于部门','描述对象之间的联系'),('axiom','公理 Axiom','经理是一类员工','明确具有逻辑含义的断言'),('individual','个体 Individual','张三、研发部','表示具体对象，可按需纳入')]
add('本体的常见组成','用同一个模型看清五类内容各自承担的作用。',grid('<section class="panel graph-panel" id="ingredientGraph"><h3>一张模型，几种不同的表达角色</h3>'+model5+'<p class="small">轮廓表示概念，深色表示个体；关系在线上，属性描述特征。</p></section>', '<section class="panel ingredient-list"><h3>点击一项，观察对应的模型部分</h3>'+''.join(f'<button class="ingredient" data-action="ingredient" data-value="{k}"><b>{a}</b><span>{b}<small>{c}</small></span></button>' for k,a,b,c in items)+'</section>'),
 '这些是常见组成；按用途选取，重点是把领域语义建模清楚。','OWL 中，对象间关系通常也是 Property；公理用于陈述知识。',
 '这张图里，我们可以看到本体常见的五类内容。\n\n第一类是类，也就是概念和类别。员工、经理、部门，都属于这一类。第二类是属性，用来描述对象的特征，比如员工的姓名和入职时间。\n\n第三类是关系。比如员工隶属于部门，它说明不同对象怎样联系起来。在 OWL 里，这种对象之间的关系通常也属于属性，我们这里把它单独拿出来，是为了便于理解。\n\n第四类是公理。这个词听起来很数学化，在这里可以先理解为具有明确逻辑含义的知识声明。比如“经理是一类员工”，就说明了两个类别之间的包含关系。\n\n第五类是个体，也就是具体对象。张三是一个具体的人，研发部是一个具体部门。这里有个容易混淆的地方：“经理是一类员工”，说的是类别之间的关系；“张三是员工”，说的是某个具体对象属于哪个类别。\n\n这些是常见组成，实际建模时按用途选择。关键是表达清楚，而不是把每一种元素都凑齐。接下来，我们用其中的分类和互斥声明，看一看形式语义能带来什么。',sources=['owl'])

# === 08 · Explain two different outcomes ===
add('形式语义怎样支持推理与检查','同一套明确的逻辑约定，可以用于推导新结论，也可以用于发现矛盾。',
 grid(panel('01 推导：把已知知识的后果算出来',row('已知一','经理是一类员工。')+row('已知二','李敏是经理。')+flow(['李敏','经理','员工'],['属于','是一种'])+'<button class="action" data-action="infer">运行教学推导</button><div class="demo-result" id="inferenceResult"><b>可推出：李敏是员工。</b><p>结论没有在两个前提中直接写出，但由它们共同蕴含。</p></div>'),
 panel('02 检查：发现与约定冲突的陈述',row('已有约定','员工与部门互斥。')+row('正常事实','张三是员工。')+'<label class="check-option"><input type="checkbox" id="badFact"> 加入假设误录：“张三也是部门”</label><div class="demo-result" id="consistencyResult"><b>当前两项陈述没有这个互斥冲突。</b><p>切换误录项，观察分类断言是否与约定相容。</p></div>'+p('检查对象是知识之间的逻辑关系；外部事实是否真实仍需业务证据。','small'),'ochre'))+
 '<div class="evidence-strip"><div><b>前提</b><span>给定明确表达的知识与逻辑含义。</span></div><div><b>结果</b><span>可解释的推导，或可定位的矛盾。</span></div><div><b>使用</b><span>让知识维护与核对有明确依据。</span></div></div>',
 '形式推理计算逻辑后果；业务判断还要结合政策适用范围与事实来源。','教学模拟；需相应推理工具，OntoWeave 当前不提供这里展示的 OWL 自动推理。',
 '先看左边。我们已经知道两件事：经理是一类员工，李敏是经理。这两条知识放在一起，就能推出“李敏是员工”。虽然我们没有单独写下这句话，但它已经包含在前面的逻辑关系里了。\n\n再看右边。假设我们已经明确规定，员工和部门是互斥的类别。原来只记录“张三是员工”，没有这个冲突；如果又误录了一条“张三也是部门”，这些声明就不能同时成立了。相应的推理工具可以帮助我们发现这种矛盾。\n\n大家可以注意到，这里的推理和检查都有前提：含义必须先明确，相关知识也必须已经表达出来。工具检查的是这些知识之间的逻辑关系。至于李敏在现实中是不是经理，仍然要回到可靠的业务来源核实。\n\n屏幕上的按钮是这两个例子的教学演示。今天介绍的是一般的形式推理能力，OntoWeave 当前还没有提供这里展示的 OWL 自动推理。\n\n接下来，我们把目光从逻辑声明移到知识的组织方式，看看本体与知识图谱怎样联系起来。',sources=['owl','project'])

# === 09 · Ontology supplies semantics; a knowledge graph connects knowledge ===
kg_diagram=svg(
 '<rect class="kg-schema" x="0" y="0" width="1000" height="190"/>'+
 '<text class="kg-band-label" x="28" y="36">本体定义 · 语义模型</text>'+
 snode(100,65,250,85,'员工')+snode(650,65,250,85,'部门')+
 sedge('M350 107 H650','所属部门',500,85)+
 '<text class="kg-explanation" x="500" y="178" text-anchor="middle">定义：员工归属哪个部门</text>'+
 '<rect class="kg-facts" x="0" y="285" width="1000" height="170"/>'+
 '<text class="kg-band-label" x="28" y="322">具体事实</text>'+
 snode(100,350,250,85,'张三','','dark')+snode(650,350,250,85,'研发部','','dark')+
 sedge('M350 392 H650','所属部门',500,370)+
 sedge('M225 350 V150','是一个员工',225,247,'dashed')+
 sedge('M775 350 V150','是一个部门',775,247,'dashed'),
 '0 0 1000 465').replace('aria-label="业务概念及关系示意"','aria-label="采用本体的知识图谱：员工和部门的定义，以及张三、研发部的事实通过类别归属与所属部门关系连接"')
add('本体与知识图谱：语义模型怎样支撑知识网络','本体可以作为知识图谱的语义模型；图谱使用这些定义，把知识连接起来。',
 grid(panel('本体：明确知识的含义',p('有哪些概念？关系代表什么？','question')+
 row('员工、部门','分别是什么，怎样区分。')+row('所属部门','表示员工归属哪个部门。')+
 '<hr><h3>知识图谱：把知识连接起来</h3>'+p('有哪些对象？它们怎样关联？','question')+
 p('张三是员工，研发部是部门；<br>张三的所属部门是研发部。'),'kg-explainer'),
 panel('一种采用本体的知识图谱',kg_diagram+p('虚线说明对象属于哪个类；上下共用同一套关系含义。','small'),'kg-diagram')),
 '本体可作为图谱的语义模型；知识图谱可以同时组织本体定义与具体事实。','图示为一种常见用法；本体也可包含个体，知识图谱不限定使用 OWL。',
 '我们用同一个例子，把本体和知识图谱的关系讲清楚。先看“员工”“部门”“所属部门”这几个词。本体要明确，员工是什么，部门是什么，以及“所属部门”这条关系表示员工归属哪个部门。这些定义提供了一套共同的业务含义。\n\n再看具体知识：张三是一个员工，研发部是一个部门，张三的所属部门是研发部。我们把这些对象和关系连接起来，就得到了一小块知识图谱。这里用到的“员工”和“所属部门”，都引用了刚才明确的定义。\n\n请看右边这张图。上面是本体提供的定义，下面是具体对象和事实。两条向上的虚线告诉我们，张三属于员工这一类，研发部属于部门这一类；上下两处“所属部门”也使用同一个含义。这样，定义和事实就关联起来了。\n\n整张图展示的是一种采用本体的知识图谱。我们可以说，本体在其中承担语义模型的角色，帮助大家一致地理解和使用知识；图谱则把定义、对象和事实组织成可以关联和查询的网络。本体还可以被其他系统引用，同一套定义也可以被多个图谱复用。\n\n因此，我们不能简单地把“上面全是本体、下面才叫知识图谱”作为两个概念的严格边界。知识图谱可以包含本体定义，本体本身也可以包含具体个体。这张图的重点，是让大家看到本体怎样为知识图谱提供含义。\n\n理解了这个关系，我们再把本体放到 AI 的发展路线中，看看这种明确表达知识的方法，怎样与大模型的学习能力配合。',sources=['kg','owl','rdf'],cls='ontology-kg')

# === 10 · Two traditions: explicit knowledge and learned representations ===
neural_layers=[[(65,y) for y in (60,130,200)],[(270,y) for y in (35,100,165,230)],[(475,y) for y in (60,130,200)],[(680,y) for y in (95,165)]]
neural_lines=''.join(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>' for a,b in zip(neural_layers,neural_layers[1:]) for x1,y1 in a for x2,y2 in b)
neural_nodes=''.join(f'<circle cx="{x}" cy="{y}" r="14"/>' for layer in neural_layers for x,y in layer)
neural_graph='<svg class="neural-sketch" viewBox="0 0 750 290" role="img" aria-label="神经网络简化示意：多层计算单元通过带权连接传递信息"><g class="neural-links">'+neural_lines+'</g><g class="neural-nodes">'+neural_nodes+'</g><text x="65" y="282" text-anchor="middle">输入</text><text x="372" y="282" text-anchor="middle">多层计算与学习</text><text x="680" y="282" text-anchor="middle">输出</text></svg>'
add('AI 的两条路线：符号主义与联结主义','一个侧重把知识明确表示出来，一个侧重从数据中学习表示与规律。',
 grid(panel('符号主义 · Symbolic AI',p('用有含义的符号、关系和规则表达知识。','question')+flow(['经理','员工'],['是一类'])+
 row('怎样工作','把概念与条件明确写出，再由程序查询、匹配或推理。')+row('代表成果','早期的重要成果包括专家系统；本体是这条路线中的知识表示方式。')+call('<b>本体属于符号主义的知识表示路线。</b><span>“部门负责人”是有明确含义的关系。</span>'),'accent'),
 panel('联结主义 · Connectionism',p('用相互连接的计算单元，从数据中学习。','question')+neural_graph+
 row('怎样工作','训练调整连接权重等参数，学会识别模式、预测或生成内容。')+row('代表发展','以神经网络为代表，发展出深度学习，并支撑今天的大语言模型。')+call('<b>神经网络是联结主义的核心代表。</b><span>“谁来批”“交给哪位领导”可被理解为相近意图。</span>'),'ochre')),
 '理解本体与大模型的配合，可以先看“显式知识”与“学习能力”这两种长处。','两条路线长期并行发展；右图为简化神经网络示意，并非实际大模型结构。',
 '我们可以先从两种不同的思路理解 AI。\n\n符号主义侧重把知识明确地表示出来。一个符号代表什么，一个概念和另一个概念有什么关系，什么条件下可以得到什么结论，都尽可能写清楚，然后由程序进行查询、匹配或者推理。前面讲的本体，就属于这条知识表示路线。专家系统是这条路线早期的重要成果，下一页我们会具体看。\n\n联结主义则侧重通过相互连接的计算单元来学习。神经网络是它的核心代表。训练过程中，系统不断调整连接权重等参数，从数据和反馈中学会识别模式、预测或者生成内容。沿着这条路线，发展出了深度学习，也支撑了今天的大语言模型。\n\n比如“这单找谁批”和“应该交给哪位领导”，说法不同，语言模型可以理解它们可能在表达相近的意图。而本体可以明确，这个业务里的“部门负责人”究竟指哪一种关系。\n\n这两条路线长期并行发展。把它们放在一起看，我们就更容易理解，为什么语言模型的学习能力与明确的业务知识可以互相补充。先从符号主义的一个典型应用——专家系统——说起。',sources=['gruber','expert','deep','transformer'],cls='ai-traditions')

# === 11 · An expert system makes domain expertise operational ===
add('专家系统：把领域经验写成可用的规则','在特定领域中，把专家知识存入知识库，由推理机制结合事实给出判断或建议。',
 '<div class="expert-definition"><b>经典例子：MYCIN</b><span>20 世纪 70 年代的研究系统，利用医学知识与规则提供感染诊断和治疗建议。</span></div>'+grid(
 panel('01 知识库 · 知道什么',p('知识工程师与领域专家整理概念、事实和规则。')+'<div class="rule-example"><b>如果</b><p>申请适用本例政策，申请人属于部门 D，且 D 的当前负责人为 H；</p><b>那么</b><p>该申请应由 H 审批。</p></div>'+p('事实可以来自用户输入或外部系统。','small')),
 panel('02 推理机制 · 怎样判断',p('把当前事实代入规则，检查条件，再推出结论。')+'<ol class="expert-checks"><li>选择与问题相关的规则。</li><li>用已知事实匹配规则条件。</li><li>条件满足时产生结论。</li><li>记录使用的规则与事实。</li></ol>'+p('缺少必要事实时，可以继续提问或查询。','small'),'accent'),
 panel('03 结论与解释 · 为什么',p('本例审批人是李敏。','expert-answer')+p('解释可以指出使用了哪条规则、哪些事实，以及中间判断。')+row('擅长','边界明确、知识可整理的专业任务。')+row('难点','获取专家经验，维护例外与规则之间的关系。')),cls='three')+
 call('<b>本体提供概念与关系的语义基础；专家系统在领域知识之上加入求解与交互机制。</b>本体可以被专家系统使用，也可以提供给今天的 Agent。'),
 '专家系统是符号主义的代表应用；本体是一种知识模型，两者处在不同层次。','差旅规则为教学示意；MYCIN 仅作历史例子，不讨论临床应用建议。',
 '专家系统的基本思路，是把某个专业领域里的知识整理到知识库中，再让推理机制结合当前事实，给出判断或建议。\n\n一个经典例子是二十世纪七十年代的 MYCIN 研究系统，它利用医学知识和规则，研究感染诊断与治疗建议。今天我们只借这个历史例子理解系统结构。\n\n回到差旅场景，我们可以把专家系统分成三个部分看。第一部分是知识库，保存概念、事实和规则。比如，如果申请适用这条政策，申请人属于某个部门，而这个部门的当前负责人是某个人，那么就由这个人审批。\n\n第二部分是推理机制。它选择有关规则，把查到的事实代入条件，条件满足时产生结论。如果缺少必要事实，也可以继续提问或查询。\n\n第三部分是结论和解释。系统除了给出审批人，还可以说明用了哪条规则、依据哪些事实、经过了什么判断。\n\n这里也就能看出本体的位置：本体帮助明确概念和关系的含义；专家系统则在领域知识之上，增加了求解和交互机制。一个是知识模型，一个是利用知识完成任务的应用系统。\n\n这种方式在边界明确的专业任务里很有价值，但专家经验的获取、例外的处理和规则维护，也需要持续投入。下面我们把这两条 AI 路线放在一起比较。',sources=['expert','gruber'],cls='expert-system')

# === 12 · Compare strengths and costs without absolute claims ===
comparison=[
 ('知识怎样获得','把领域定义、关系与条件显式整理出来；<br>可以逐条审阅和确认。','从样本与训练反馈中学习参数；<br>可以发现难以逐条编写的复杂模式。'),
 ('主要优势','含义与条件明确，便于约束、检查和追溯；<br>适合分类、规则判断与关系推演。','适应语言、图像等复杂输入；<br>擅长模式识别、语义匹配与内容生成。'),
 ('主要代价','知识获取与维护费力；<br>未覆盖的情形、模糊输入和大量例外难处理。','依赖数据、训练与计算；<br>判断依据难逐项追溯，也可能出现不可靠输出。'),
 ('业务变化时','可定位修订定义或规则；<br>仍需检查关联影响与事实来源。','参数中的旧知识不易精确更新；<br>可借助新上下文、检索、工具或再训练。'),
]
add('两条路线，各有擅长与代价','把能力放在具体任务中比较，才知道哪些部分适合交给谁。',
 '<table class="ai-comparison"><thead><tr><th scope="col">比较维度</th><th scope="col">符号主义 · 显式知识</th><th scope="col">联结主义 · 学习表示</th></tr></thead><tbody>'+''.join(f'<tr><th scope="row">{a}</th><td>{b}</td><td>{c}</td></tr>' for a,b,c in comparison)+'</tbody></table>'+
 '<div class="comparison-case"><b>回到差旅审批</b><span>多样表达：“这单找谁批？” → 语言模型理解任务</span><span>明确口径：“部门负责人” → 本体与规则约束判断</span></div>',
 '两者结合的价值：让灵活理解有明确依据，让明确知识更容易被构建和使用。','这里概括典型侧重，能力可以重叠；模型与规则都可能出错，实际收益需验证。',
 '如果用一句话概括，符号主义的长处在于明确，联结主义的长处在于学习复杂模式。\n\n明确知识有什么好处？我们可以逐条审阅定义和条件，检查一条规则为什么成立，也可以在业务变化时，定位需要修改的地方。代价是，这些知识需要有人整理和维护；遇到没有覆盖的情况、大量例外或者很模糊的输入，处理起来会比较费力。\n\n神经网络则可以从数据里学习许多很难逐条编写的模式。语言、图像和多样化表达，都是它能够发挥作用的地方。但学习依赖数据、训练和计算；一个结果究竟依据了哪些内部知识，往往难以逐项追溯，输出也可能不可靠。\n\n回到我们的案例：用户怎样描述问题，可以有很多种说法；公司当前采用哪条审批政策，却需要有明确依据。前一部分适合发挥语言模型的理解能力，后一部分适合使用经过确认的知识和相应的检查机制。\n\n这些是典型侧重，实际能力会有重叠。我们真正关心的是，怎样把它们组合起来，让各自擅长的部分服务于同一个业务任务。',sources=['expert','deep','nesy'],cls='ai-tradeoffs')

# === 13 · One architecture covers neural, symbolic, retrieval, and tools ===
arch=svg(snode(385,15,310,80,'谁来审批 T-101？')+snode(360,250,360,120,'Agent','语言模型理解与组织','dark')+snode(0,120,255,100,'资料检索','制度原文与上下文')+snode(0,420,255,100,'本体语义','定义、关系与政策','soft')+snode(825,120,255,100,'当前事实','申请与组织信息')+snode(825,420,255,100,'业务工具','查询、计算与执行')+sedge('M540 95 V250')+sedge('M360 280 H310 V170 H255','找原文',320,135)+sedge('M360 340 H310 V470 H255','读语义',320,435)+sedge('M720 280 H770 V170 H825','取事实',770,135)+sedge('M720 340 H770 V470 H825','用工具',770,435),'0 0 1080 580')
add('Agent 怎样结合两条 AI 路线','把神经网络的学习能力，与显式语义、资料依据和外部工具连接起来。',
 grid(panel('围绕任务组织知识与能力',arch,'graph-panel'),panel('各部分解决不同问题',row('语言模型','理解多样表达，规划信息需求，组织回答。')+row('资料检索','找到制度原文、适用条件与上下文。')+row('本体语义','明确概念含义、关系路径和业务约定。')+row('工具与事实','从业务系统取当前数据，按授权查询、计算或执行。')+call('需要严格规则判断时，由相应规则或业务程序执行并返回结果。')))+
 call('<b>互补的价值：</b>语言模型带来灵活理解；显式知识提供共同口径；工具连接当前事实和真实操作。'),
 '先明确谁负责理解、谁提供依据、谁执行操作，再让它们围绕任务协作。','概念分工可有重叠；读取本体不等于形式推理，也不表示平台已有 OWL 推理或规则执行引擎。',
 '大家看这张图，中间是 Agent，它围绕用户的问题组织信息和能力。\n\n语言模型首先帮助理解用户想做什么，判断还需要哪些信息，并组织后续处理。资料检索帮助找到制度原文和上下文；本体提供明确的概念定义、关系和业务约定；业务系统提供当前事实；工具负责具体的查询、计算和获准操作。\n\n例如，“部门负责人”是什么意思，可以从明确的业务语义中取得；这个部门今天由谁负责，要查询当前组织信息；如果需要真正提交审批，还要调用具备相应权限的业务接口。\n\n需要严格执行的规则，可以交给相应的规则程序或业务程序，执行后把结果交回 Agent。这样，每一个判断就能找到它所依赖的知识或者执行结果。\n\n这是一种容易理解的组合方式：用语言模型处理多样表达，用显式知识提供共同口径，再通过工具连接现实业务。它与神经符号结合的思路是相通的。实际效果仍然取决于知识是否正确，以及 Agent 是否正确使用了它。\n\n下面，我们就用这套分工，把开头那张申请完整走一遍。',sources=['nesy','ibm'],cls='agent-architecture')

# === 14 · The single complete walkthrough ===
steps=[('确认口径','先识别申请类型与适用政策。','本例政策使用当前部门负责人。'),('查询事实','取得申请人和相关组织信息。','按已确认的时间口径查询当前数据。'),('核对条件','检查关系是否完整、是否匹配政策。','直属主管不自动等同部门负责人。'),('形成回答','给出人选、依据与仍未知之处。','需要提交时，另走获准业务操作。')]
add('Agent 如何找到审批人','把前页的分工用于 T-101：从确认政策，到查询、核对与回答。',
 '<div class="agent-steps">'+''.join(f'<button class="agent-step {"selected" if i==0 else ""}" data-action="agentStep" data-value="{i}"><span class="step-index">0{i+1}</span><h3>{t}</h3><p>{a}</p><small>{b}</small></button>' for i,(t,a,b) in enumerate(steps))+'</div>'+flow(['T-101','张三','研发部','李敏'],['申请人','所属部门','负责人'])+
 '<div class="sources-row"><span>差旅系统：申请人</span><span>人事系统：部门归属与负责人</span></div>'+grid('<div class="response"><b>给用户的回答</b><p id="agentAnswer">应由李敏审批。依据为本例差旅政策与当前组织查询结果。</p></div>',panel('如果关键事实缺失',p('明确指出缺失项，再继续查询或询问。')+'<label class="check-option"><input type="checkbox" id="missingHead"> 模拟缺少当前负责人信息</label>','compact')),
 '语义约束要走的路径，事实决定路径最终指向谁。','教学推演，未调用真实业务系统；若继续提交，应按授权执行并核对回执。',
 '现在用户问：“T-101 应该找谁审批？”Agent 可以按四步完成这件事。\n\n第一步，确认口径。先识别这是什么类型的申请，适用哪一条政策。在我们的设定里，政策指定的是申请人当前所属部门的负责人。\n\n第二步，查询事实。差旅系统告诉我们，申请人是张三；人事系统告诉我们，张三属于研发部，研发部当前负责人是李敏。屏幕上的这条路径，就是把这些信息连接起来的结果。\n\n第三步，核对条件。关系是否齐全？查询的时间口径是否符合政策？有没有把直属主管当成部门负责人？这些地方核对清楚，答案才有依据。\n\n第四步，形成回答：“应由李敏审批，依据是本例差旅政策和当前组织查询结果。”如果还要提交申请，就继续走获准的业务操作，并核对执行结果。\n\n我们再看一个信息不完整的情况：如果能确认张三属于研发部，但查不到研发部当前负责人，回答就应该停在这里，明确缺少哪项信息，再继续查询或询问。\n\n这个过程里，语义决定应该沿着什么关系找，当前事实决定最终找到谁。看到这里，我们还需要问一个实际问题：要把这套知识建起来、长期用下去，需要付出什么代价？',cls='agent-walkthrough')

# === 15 · Adoption barriers: the costs behind explicit semantics ===
tradeoffs=[
 ('业务共识难','“负责人”可能是部门负责人、项目负责人或代理人，含义和适用边界需要确认。','依赖专家与跨团队协作；口径谈不拢，模型就难共享。'),
 ('建模与接入贵','把概念连到实际字段、数据源和接口，还要学习方法、校验模型、验证效果。','前期投入大、见效需要时间；自动抽取仍需业务核对。'),
 ('维护负担重','政策、组织结构或系统字段变化后，要同步相关定义、映射与依赖。','多维护一套共享知识；更新滞后会让下游沿用旧口径。'),
 ('表达有边界','隐性经验、模糊条件和临时例外难以穷尽，逻辑一致也不能证明事实真实。','要在简化和精细之间取舍；错误或遗漏可能被多个任务复用。'),
]
add('本体的难点与代价：为何难成通用默认方案','显式建模需要业务共识、技术能力和持续维护，也会增加系统依赖。',
 '<table class="ontology-tradeoffs-table"><thead><tr><th scope="col">难点</th><th scope="col">在实际业务中意味着什么</th><th scope="col">带来的代价与风险</th></tr></thead><tbody>'+''.join(f'<tr><th scope="row">{kind}</th><td>{meaning}</td><td>{cost}</td></tr>' for kind,meaning,cost in tradeoffs)+'</tbody></table>'+
 call('<b>推广门槛：</b>建设与维护成本先发生，收益往往依赖持续复用；简单任务已有更轻的实现。'),
 '引入本体需要同时考虑业务收益与长期负担，下一步再判断哪些场景值得投入。',
 '生物医学等领域已有成熟应用；此处讨论推广门槛，非普及率统计。',
 '看完刚才的例子，大家可能会问：既然本体能把业务含义说清楚，为什么没有成为所有系统的默认方案？我们先把它的难点和代价摆出来。\n\n第一，业务共识很难获得。就拿“负责人”来说，不同部门可能想到的是部门负责人、项目负责人，或者临时代理人。把这些含义、边界和例外确认下来，需要领域专家参与，也需要跨团队讨论。软件能记录结论，但不能替业务人员解决还没有达成的共识。\n\n第二，从模型走到实际应用，中间有不少工作。我们需要把概念对应到真实字段、数据源和接口，选择表达方式，再验证查询和使用是否正确。即使 Agent 已经抽取出候选模型，业务含义和映射仍要核对。选择较复杂的形式语言时，还会增加学习和工具使用门槛。\n\n第三，维护会一直存在。政策变了、部门调整了、系统字段改了，相关定义和映射都可能需要修改。这相当于多了一份需要负责和维护的共享知识。更新跟不上时，多个助手反而可能一起沿用旧口径。\n\n第四，模型有自己的边界。真实业务中的隐性经验和临时例外，很难一次写全。模型过于简单，会漏掉重要条件；建得过细，又会增加理解和修改成本。逻辑上没有矛盾，也不能证明资料真实。错误定义一旦被共享，还可能影响更多任务。\n\n所以，从工程投入看，我会把推广门槛概括为：成本较早发生，收益往往要靠长期使用和跨任务复用才能体现。对于简单任务，现有文档检索或业务程序可能已经足够。\n\n当然，应用情况要按领域看。比如 Gene Ontology 已经在生物医学研究中广泛使用。这里讨论的是，为什么不能把同一套建设投入直接套到所有业务里。接下来我们就看，哪些场景更值得承担这些投入。',
 sources=['ontology101','ontologyChallenges','ontologyDebug','go'],cls='ontology-tradeoffs')

# === 16 · Shared use and the decision to invest ===
add('何时值得建本体？看跨任务的语义复用','当多个助手长期依赖同一套业务定义时，集中澄清与维护更容易体现价值。',
 '<div class="shared-definition"><div><span class="eyebrow">共同维护，按任务读取</span><h3>员工 · 所属部门 · 部门负责人</h3><p>同一份定义与来源说明，供不同任务引用。</p></div><b class="shared-badge">一处澄清<br>多处引用</b></div>'+grid(
 panel('差旅助手',p('确定申请审批人。','question')+p('使用申请、组织关系与审批政策。')),
 panel('报表助手',p('按部门统计申请。','question')+p('复用组织关系，另行确认统计时点与口径。')),
 panel('组织助手',p('查询部门负责人。','question')+p('使用同一定义，从指定来源读取当前事实。')),cls='three')+
 '<div class="scenario-choice"><b>投入是否值得？</b><div class="choices">'+btn('一次性查一条制度','fit','data-value="small"',True)+btn('跨系统、跨任务反复使用','fit','data-value="shared"')+'</div><p id="fitText">简单单次任务可以先用制度检索；长期复用时，再比较收益与澄清、连接、验证、维护的投入。</p></div>',
 '优先选择歧义多、关系多、反复使用且有人维护的业务范围。','共享语义不等于共享所有数据；各助手仍保留自身任务、工具和访问权限。',
 '刚才看到了建设和维护的代价，现在我们再看，哪些业务收益能让这些投入变得值得。\n\n如果只是偶尔查一条制度，已有的文档检索就能稳定回答，那么我们可以先使用这个轻量方案。本体的价值更容易在长期、反复的使用中体现出来。\n\n看这三个助手。差旅助手需要确定审批人，报表助手需要按部门统计申请，组织助手需要查询部门负责人。它们任务不同，但都要理解员工、部门和负责人这些概念。\n\n如果这套含义经过一次共同澄清，三个助手就可以引用同一份定义和来源说明。以后遇到术语歧义，也有一个共同的讨论基础。当然，各自的任务条件仍然要确认，比如报表统计的是申请提交时的部门，还是查询时的部门。\n\n这种复用有收益，也有建设成本：澄清含义、连接来源、验证效果，都需要时间，后续还有维护工作。所以，比较适合先尝试的，是歧义多、关系多、经常重复使用，而且有人负责维护的业务范围。\n\n选定这样的范围后，接下来就可以开始建立第一个有用的本体。',cls='reuse-value')

# === 17 · A compact engineering loop ===
phase=[('确定范围','先问要解决什么','T-101 由谁审批？哪些申请属于本轮范围？','产物：问题与范围清单'),('澄清含义','确认容易混淆的词','负责人是部门负责人，还是直属主管？“当前”如何理解？','产物：定义与待澄清项'),('建立模型','把含义明确表达','员工、部门、申请；申请人、所属部门、负责人；审批政策。','产物：概念、关系、约定'),('连接来源','明确事实到哪里找','差旅系统提供申请人，人事系统提供组织归属与负责人。','产物：来源与映射说明'),('问题验证','回到原问题核对','正常情况下解释李敏；负责人未知时，指出缺失而不猜测。','产物：问题、答案与依据')]
add('一个有用的本体怎样建立','从实际问题开始，让澄清、建模与验证形成可反复改进的过程。',
 '<div class="build-phases">'+''.join(f'<section class="build-phase"><span>0{i+1}</span><h3>{a}</h3><b>{b}</b><p>{c}</p><small>{d}</small></section>' for i,(a,b,c,d) in enumerate(phase))+'</div>'+grid(panel('资料与领域人员确认业务含义',p('数据库字段说明可以帮助理解存储；制度、访谈和业务确认帮助理解真正的业务口径。')+p('无法确认的内容明确保留为未知，避免把猜测固化成知识。'),'compact'),panel('Agent 可以协助整理和检查',p('从资料中提出候选概念与关系，帮助发现术语不一致、条件遗漏和待澄清问题。')+p('最后用业务问题检验定义、关联、来源与回答依据。'),'compact accent')),
 '建设的终点是一组能回答、能解释、能维护的业务问题。','按当前范围选择表达内容；不要求一次性覆盖整个组织。',
 '建设可以从五件事开始。\n\n首先，确定要解决的问题和范围。比如，我们先处理某一类差旅申请的审批人查询，把它涉及的政策和系统范围划清楚。\n\n第二，澄清容易产生歧义的含义。“负责人”是哪一种负责人？“当前”按什么时间理解？如果资料里说法不一致，就把问题提出来，请业务人员确认。\n\n第三，把确认过的含义建立成模型，明确概念、关系和业务约定。第四，连接事实来源，说明申请信息从哪里取，组织关系由哪个系统提供，模型中的业务含义怎样对应到实际数据。\n\n第五，回到最初的问题验证。事实齐全时，能否找到正确的人并解释依据？负责人未知时，能否明确指出缺失？如果回答不对，我们再检查是定义、关系、来源还是使用过程出了问题。\n\nAgent 可以协助阅读资料、提出候选概念、发现不一致，也可以调用平台保存和读取模型。业务人员则提供和确认业务含义，特别是资料中没有说清楚的部分。无法确认的内容，应该明确保留为未知。\n\n这五件事可以来回迭代。随着模型持续建设，我们也需要一个地方来组织、维护和提供这些知识，这就引出了 OntoWeave。',cls='modeling-process')

# === 18 · Product architecture, with the modeling Agent as a distinct feature ===
platform_arch='''<svg class="platform-architecture" viewBox="0 0 1712 620" role="img" aria-label="OntoWeave 产品能力：业务人员提供资料，独立的建模 Agent 生成和修订模型，语义平台服务向业务 Agent 提供上下文，业务 Agent 调用外部系统">
<rect class="platform-boundary" x="300" y="18" width="1020" height="440"/>
<text class="platform-boundary-title" x="328" y="65">OntoWeave ／ 织义 · 产品能力</text>
<rect class="architecture-box" x="0" y="145" width="230" height="245"/>
<text class="architecture-heading" x="25" y="207">业务人员</text>
<text class="architecture-copy" x="25" y="263">提供资料与任务</text>
<text class="architecture-copy" x="25" y="306">确认业务口径</text>
<text class="architecture-copy" x="25" y="349">回答澄清问题</text>
<rect class="modeling-agent-box" x="330" y="105" width="430" height="320"/>
<text class="modeling-agent-kicker" x="358" y="150">平台特性 · Modeling Agent</text>
<text class="modeling-agent-title" x="358" y="218">建模 Agent</text>
<text class="modeling-agent-copy" x="358" y="280">理解资料 · 发起澄清</text>
<text class="modeling-agent-copy" x="358" y="328">组织模型 · 提交变更</text>
<text class="modeling-agent-copy" x="358" y="376">读取模型 · 自查修订</text>
<rect class="architecture-box core-box" x="855" y="105" width="430" height="320"/>
<text class="architecture-heading" x="880" y="170">语义知识与平台服务</text>
<text class="architecture-copy" x="880" y="235">保存概念、关系和业务约定</text>
<text class="architecture-copy" x="880" y="293">校验并应用模型变更</text>
<text class="architecture-copy" x="880" y="351">按权限和范围提供语义</text>
<rect class="architecture-box" x="1430" y="145" width="280" height="245"/>
<text class="architecture-heading" x="1455" y="207">业务 Agent</text>
<text class="architecture-copy" x="1455" y="271">读取相关业务语义</text>
<text class="architecture-copy" x="1455" y="322">结合工具处理任务</text>
<path class="architecture-arrow" d="M230 280 H330" marker-end="url(#arrow)"/>
<text class="architecture-label" x="280" y="250" text-anchor="middle">输入</text>
<path class="architecture-arrow" d="M760 240 H855" marker-end="url(#arrow)"/>
<text class="architecture-label" x="807" y="210" text-anchor="middle">写入</text>
<path class="architecture-arrow" d="M855 350 H760" marker-end="url(#arrow)"/>
<text class="architecture-label" x="807" y="323" text-anchor="middle">读回</text>
<path class="architecture-arrow" d="M1285 280 H1430" marker-end="url(#arrow)"/>
<text class="architecture-label" x="1357" y="250" text-anchor="middle">语义上下文</text>
<path class="architecture-arrow" d="M1570 390 V485" marker-end="url(#arrow)"/>
<text class="architecture-label" x="1570" y="446" text-anchor="middle">查询 / 执行</text>
<rect class="external-box" x="1430" y="485" width="280" height="122"/>
<text class="architecture-heading" x="1450" y="534">外部业务系统</text>
<text class="architecture-small" x="1450" y="578">数据 · 查询 · 获准操作</text>
<rect class="architecture-summary" x="0" y="493" width="1320" height="114"/>
<text class="architecture-heading" x="28" y="538">两类 Agent，各有明确任务</text>
<text class="architecture-copy" x="28" y="582">建模 Agent 建设与维护知识；业务 Agent 读取知识，处理业务任务。</text>
</svg>'''
add('OntoWeave：建模与业务使用如何连接','建模 Agent 是平台的重要特性：把业务资料与澄清结果组织成可供业务 Agent 使用的模型。',
 platform_arch,
 '从资料理解、模型建设，到业务语义的读取与使用，形成持续协作。','产品能力示意，非部署拓扑；建模质量仍需业务核对与独立验证。',
 'OntoWeave 的中文名叫“织义”。我们先用这张图看看，它怎样把业务知识的建设和使用连接起来。\n\n从左边看，业务人员提供资料和任务，确认业务口径，也回答资料中没有说清楚的问题。图中间这个深绿色模块，是我们希望重点介绍的平台特性：建模 Agent。\n\n建模 Agent 有自己的任务。它阅读业务资料，发现含义不清楚的地方，提出需要澄清的问题，再把已经确认的知识组织成概念、关系和业务约定。获得相应授权后，它可以提交模型变更，读取已建模型进行自查，并根据发现的问题继续修订。\n\n它右边是语义知识与平台服务。这部分负责保存模型，对提交进行校验和应用，并按照权限和任务范围提供相关语义。建模 Agent 负责理解和组织业务含义，平台程序负责可靠地保存和提供这些内容，两者配合工作。\n\n最右边则是业务 Agent。它使用模型中的定义、关系和条件，再结合外部业务系统里的当前数据完成任务。真正的数据查询和业务操作，仍由对应的系统和工具承担。\n\n所以，这里有两类 Agent：建模 Agent 面向知识建设，业务 Agent 面向具体任务。我们把建模 Agent 单独列出来，就是因为它是 OntoWeave 支持业务语义建设的一项重要特性。下面再具体看看，这套平台提供哪些能力。',sources=['project'],cls='platform-architecture-slide')

# === 19 · Concrete platform capabilities, beyond the architecture ===
add('OntoWeave 提供哪些关键能力','把业务知识的建设、组织、读取和维护，放到一套相互衔接的工作方式中。',
 '<div class="platform-capabilities">'+
 panel('<span class="capability-number">01</span> Agent 辅助建模',p('阅读资料、发现语义缺口、提出澄清问题，组织模型并提交修订。')+p('将资料整理、建模与读回自查串起来。','capability-value'),'featured-capability')+
 panel('<span class="capability-number">02</span> 一份模型，多种视角',p('从对象、行为、规则、角色、流程，以及数据和接口映射观察同一份知识。')+p('帮助核对业务含义及其相互关联。','capability-value'))+
 panel('<span class="capability-number">03</span> 按任务获取语义',p('围绕问题读取相关定义、关系、条件与映射；读取范围遵循已有授权。')+p('为业务 Agent 提供任务所需的业务上下文。','capability-value'))+
 panel('<span class="capability-number">04</span> 浏览与持续维护',p('查看节点和关系，澄清已发现的缺口，修订模型，再用业务问题核对。')+p('让业务知识成为可以维护、反复使用的成果。','capability-value'))+
 '</div><div class="platform-delivery"><b>以差旅场景为例</b><div><span>输入</span>制度、访谈与系统说明</div><i>→</i><div><span>形成</span>概念、关系、政策与映射</div><i>→</i><div><span>供给</span>审批查询所需的业务语义</div></div>',
 '平台特性：Agent 辅助建设，共同模型组织知识，按任务提供语义，并支持持续维护。','功能与使用方式介绍；业务含义需确认，实际质量需验证，业务操作由外部系统执行。',
 '从实际使用的角度，我们可以把 OntoWeave 的能力概括为四个方面。\n\n第一，是 Agent 辅助建模。业务人员提供资料和需要解决的问题，建模 Agent 协助阅读、整理和发现缺口，把明确下来的含义组织成模型。在获准范围内，它还能提交修订并读取结果自查，让建模过程能够继续往前走。涉及业务口径的判断，仍然需要可靠资料和业务确认。\n\n第二，是用多种视角观察同一份模型。对象、行为、规则、角色、流程，以及数据和接口映射，帮助我们检查不同方面的知识有没有关联起来。例如，一条审批政策涉及谁、使用什么关系、到哪里查询相关信息，都可以放到共同的模型里理解。\n\n第三，是按任务获取语义。业务 Agent 提出问题后，平台根据获准范围提供相关定义、关系、条件和映射，让它能够取得完成当前任务所需的业务上下文，再去查询实际数据。\n\n第四，是浏览和持续维护。我们可以在界面里查看模型中的节点与关系。发现遗漏或者业务发生变化后，继续澄清和修订，再通过业务问题核对结果。\n\n拿差旅场景来说，输入可以是制度、访谈结果和系统说明；形成的成果是明确的概念、关系、政策和映射；交给业务 Agent 的，则是审批查询所需的相关语义。我们希望这些工作能够持续衔接，让一份知识被逐步完善、反复使用。下一页用实际界面来看这些模型怎样呈现。',sources=['project'],cls='platform-capabilities-slide')

# === 20 · Product screenshot ===
add('在界面中查看 OntoWeave 的模型','从真实界面认识模型浏览、视角筛选与知识之间的关联。',
 '<div class="screenshot-layout"><button class="screenshot-frame" data-action="screenshot" aria-label="放大查看 OntoWeave 截图"><img src="__SCREENSHOT__" alt="用户提供的 OntoWeave 模型浏览截图：搜索、七种视角和关系网络"></button><div class="screenshot-detail">'+
 panel('模型浏览：把已建知识放在同一视野',p('界面支持按名称、IRI 或已记录的业务说明搜索。图中节点与连线呈现对象及其关联，便于查看模型。'))+
 panel('按视角观察同一份知识',p('截图可见七类筛选入口：')+'<div class="view-chips">'+''.join('<span>'+x+'</span>' for x in ['对象','行为','规则','角色','流程','数据映射','接口映射'])+'</div>','accent')+
 panel('截图中的规模与读图提示','<div class="snapshot-numbers"><div><b>156</b><span>已加载节点</span></div><div><b>225</b><span>已读取关系</span></div></div>'+p('颜色表示视角；节点大小与可见连接有关。左侧还可见建模对话、召回测试、成员权限等入口。','small'),'compact')+'</div></div>',
 '模型浏览把知识连接呈现出来；理解和验证仍要回到具体业务问题。','用户提供的界面截图；数量仅为截图时状态，不代表质量指标。点击图片可放大。',
 '大家现在看到的是 OntoWeave 的实际模型浏览界面。\n\n我们先看搜索和筛选区域。可以按名称、资源标识，也就是 IRI，或者已经记录的业务说明寻找模型内容。下面这些节点和连线，则把知识对象以及它们之间的关联呈现出来。\n\n界面上还有七类视角：对象、行为、规则、角色、流程、数据映射和接口映射。可以把它们理解为观察和检查业务知识的不同角度。比如看对象与关系，再看相关规则，或者看这些业务含义怎样连接到数据和接口。\n\n截图里显示了已加载的节点数和已读取的关系数，这些数字反映的是当时的界面状态。实际使用时，更有意义的是围绕一个问题去看：有关的概念是否齐全，关系是否清楚，来源能否找到。\n\n如果需要看细节，可以把图片放大。前面我们介绍了建模 Agent 和平台能力，这张界面展示了已经建好的模型怎样被查看和维护。大家可以从自己的一个具体业务问题开始，逐步确认相关概念、关系和条件。我的主要分享就到这里，谢谢大家，接下来可以结合常见问题继续交流。',sources=['project'],cls='product-screen')

# === Restore all 13 questions from the previous edition ===
def faq(items):
 return '<div class="faq-list">'+''.join(f'<details open><summary>{q}</summary><div class="faq-answer">{a}</div></details>' for q,a in items)+'</div>'
def links(items):
 return '<nav class="backlinks">'+''.join(f'<button data-go="{n}">{label} · P{n:02}</button>' for n,label in items)+'</nav>'
add('FAQ：什么时候值得使用本体','先看当前任务与已有方案，再决定是否增加显式语义建模。',
 faq([
 ('已经有 RAG，还需要本体吗？','文档检索已能稳定回答时，可以继续使用。跨对象、跨任务的关系需要明确复用时，可试用本体并做同条件比较。'),
 ('直接把业务规则写进提示词不行吗？','小范围任务可以。文档、词典和规则服务也能共享口径。显式关联带来的复用收益值得投入时，再进一步建模。'),
 ('本体会替代数据库或业务系统吗？','业务记录与操作仍留在原系统。本体提供业务含义、关系、条件及系统映射，帮助 Agent 理解该读什么、怎样解释。'),
 ('所有业务都要先建本体吗？','优先选择含义歧义多、跨系统关系多、同一定义被反复使用的场景。简单固定任务可以采用更轻的方案。'),
 ('本体与知识图谱有什么区别？','本体提供概念、关系及其语义约定；知识图谱用图组织知识，可以同时包含本体定义与具体事实。本体可作为图谱的语义模型。')])+links([(9,'本体与知识图谱'),(13,'Agent 分工'),(16,'适用条件')]),
 '从一个有代表性的问题试起，比较正确性、复用与实际投入。','点击问题可收起或展开；PDF 保留完整答案。',
 '“已经有 RAG，还需要本体吗？”\n\n可以先看已有方案是否已经稳定解决问题。RAG 能把相关资料找出来，很多任务做到这一步就已经够用了。如果困难主要出现在跨对象的关系、不同材料中的口径冲突，或者多个助手反复理解同一套定义，那么可以试着补充显式语义建模，再用相同条件比较效果。\n\n“直接把规则写进提示词，不也能做吗？”\n\n可以，小范围任务往往就适合这样做。规则需要共享时，也可以先用统一文档、词典或者规则服务。只有当关联关系的表达和复用确实带来收益，值得承担建模与维护成本时，再进一步使用本体。\n\n“本体会替代数据库或业务系统吗？”\n\n业务记录和实际操作仍然由原系统管理。本体帮助明确数据代表什么、对象怎样关联、哪些条件适用，以及应该到哪里取数。比如负责人是谁，可以继续从人事系统查询；本体说明的是这个关系的含义和来源。\n\n“所有业务都要先建本体吗？”\n\n可以优先选择歧义多、跨系统关系多、同一套含义被反复使用的场景。简单、固定、一次性的任务，采用更轻的方案就可以。我们可以从一个有代表性的问题试起，用结果判断下一步投入。\n\n“本体与知识图谱到底有什么区别？”\n\n本体提供概念、关系及其语义约定，知识图谱用相互连接的对象和关系组织知识。本体可以作为图谱的语义模型。比如，本体明确员工、部门和所属部门的含义；图谱把张三属于员工、研发部属于部门，以及张三所属部门是研发部这些知识连接起来。这张图可以同时包含本体定义与具体事实。',sources=['owl','kg'],cls='faq-five')
add('FAQ：怎么建，哪些工作需要人参与','从一条有界业务链开始，按实际依赖安排建模与验证。',
 faq([
 ('必须先学会 RDF 和 OWL 吗？','业务人员先确认概念与口径，技术人员选择表达及查询方式。理解本体不要求先写 OWL，当前项目也不要求自动推理。'),
 ('七个视角是通用的本体方法论吗？','这是 OntoWeave 当前的组织与检查方式，可按场景取舍；其他方案可以不同，也不要求七个本体或七个 Agent。'),
 ('Agent 能全自动把模型建好吗？','可以自动整理资料、提出模型并调用平台。资料缺失、口径冲突与授权仍需确认，质量由独立验证判断。'),
 ('是否需要一次建完整个企业？','先完成一条有代表性、可验证的业务链，再维护共享定义，并逐步扩展相邻业务范围。')])+
 links([(17,'怎样建立本体'),(20,'模型浏览界面'),(19,'平台关键能力')]),
 '自动化承担整理与调用，业务人员确认含义，独立验证判断是否可用。','七视角是平台当前方式，不是本体的通用必备组成。',
 '“必须先学会 RDF 和 OWL，才能参与本体建设吗？”\n\n业务人员可以先从自己的专业知识出发，确认概念、口径、政策和例外。技术人员再根据用途选择合适的表达和查询方式。我们完全可以先把业务问题讲清楚，再讨论怎样编码。当前这个项目也没有把 OWL 自动推理作为使用前提。\n\n“界面里的七个视角，是通用的本体方法论吗？”\n\n这是 OntoWeave 当前组织和检查业务知识的方式，实际可以按场景取舍。它与前面介绍的类、属性、关系等组成关注点不同。七个视角并不要求建立七个本体，也不要求安排七个 Agent，其他平台可以采用不同方式。\n\n“Agent 能全自动把模型建好吗？”\n\n它可以承担不少工作，比如整理资料、提出模型、发现待澄清问题，以及调用平台保存和读取知识。但如果源材料本身没有说明负责人是谁，或者两个部门对同一个词理解不同，Agent 仍然需要可靠的信息和业务确认。最终是否可用，要通过独立验证来判断。\n\n“是不是需要一次把整个企业建完？”\n\n可以先完成一条范围明确、能够验证的业务链。把这条链里的定义、关系和来源确认好，再把已经稳定的公共知识用于相邻场景。这样，业务人员能较早看到结果，我们也能较早发现理解上的偏差。',sources=['project'],cls='faq-four')
add('FAQ：怎样保证质量并持续维护','定义、事实、检索和使用都需要检查；政策变化还需外部系统对齐。',
 '<div class="faq-layout">'+faq([
 ('有了本体就不会产生幻觉了吗？','源材料、模型、检索与 Agent 使用都可能出错。需要逐环节验证，也允许合理回答未知。'),
 ('业务规则变了，是否要全部重建？','业务负责人确认新口径、生效时间和范围，再修订相关定义及映射，检查受影响问题。修改范围由实际依赖决定。'),
 ('怎样评估成本与收益？','同资料、同澄清、同工具比较正确性和完整性，分别记录建模、维护、人工确认与调用成本。'),
 ('本体权限能保护数据库和业务操作吗？','语义权限控制语义知识。数据库行列访问与审批、退款等操作权限由外部系统执行，必须分别验证。')])+
 '<aside class="maintenance"><h3>独立教学变更</h3><p class="version">部门负责人<br>↓<br>直属主管</p><p>假设自 2026-11-01 起提交的新申请改用新政策，旧申请保留原政策解释。</p><hr><p>① 确认口径与生效范围<br>② 修订语义和映射<br>③ 对齐业务系统执行<br>④ 核对新旧边界问题</p><p class="small">不改变正文的李敏结论；不代表平台自动完成影响分析或任意历史版本读取。</p></aside></div>',
 '结合你的业务继续讨论：哪些含义、关系和判断，最需要共同引用？','按需答疑；政策变更示例独立于正文案例。',
 '“有了本体，就不会产生幻觉了吗？”\n\n我们仍然需要检查整条使用过程。源材料可能有误，建模可能理解错，检索可能漏掉关键条件，Agent 也可能没有正确使用取得的知识。本体的作用，是让一部分含义和依据变得明确、可检查。对于缺失的信息，系统也应该能够合理地回答未知。\n\n“业务规则变了，是否要全部重建？”\n\n通常先看变化影响了哪些内容。比如，假设从二〇二六年十一月一日起提交的新申请改由直属主管审批，之前的申请仍按原政策解释。我们需要确认生效时间、适用范围，再修改相关语义和映射，并核对新旧申请的边界情况。同时，业务系统也要按确认后的政策执行，知识更新和实际执行需要对齐。\n\n“怎样判断这套方案是否划算？”\n\n比较时，尽量让两种方案使用同样的资料、业务澄清结果、模型、题目、数据和工具。然后看答案是否正确、条件是否完整、依据是否清楚，再分别记录建模、维护、人工确认和调用成本。这样才容易分清，收益来自本体本身，还是来自额外补充了更好的资料和工具。\n\n“本体的权限，能同时保护数据库和业务操作吗？”\n\n语义权限控制的是哪些业务知识可以被读取。数据库里的行列权限，以及审批、退款等操作权限，仍然要由相应的外部系统执行和验证。知道一项操作的含义，并不自动意味着有权执行它。\n\n这些问题最终都要回到各自的业务。我们可以继续讨论：在大家的场景里，哪一个含义、哪一条关系，最值得先明确下来，让不同的人和 Agent 共同使用？',sources=['project'],cls='faq-maintenance')

assert len(SLIDES)==23


def make_fonts(text):
 out=[]
 for name,src,weight,family in [('sans-regular','NotoSansCJK-Regular.ttc',400,'Deck Sans'),('sans-bold','NotoSansCJK-Bold.ttc',700,'Deck Sans'),('serif-bold','NotoSerifCJK-Bold.ttc',700,'Deck Serif')]:
  target=HERE/'assets'/f'{name}.woff'
  font=TTFont('/usr/share/fonts/opentype/noto/'+src,fontNumber=2)
  options=subset.Options();options.flavor='woff'
  sub=subset.Subsetter(options=options);sub.populate(text=text+'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz←→↑↓？—·×＋−／≤≥');sub.subset(font);font.flavor='woff';font.save(target)
  data=base64.b64encode(target.read_bytes()).decode()
  out.append(f"@font-face{{font-family:'{family}';font-weight:{weight};font-display:swap;src:url(data:font/woff;base64,{data}) format('woff')}}")
 return '\n'.join(out)

def main():
 sections=[];notes=[]
 for i,s in enumerate(SLIDES,1):
  chapter='01 / 认识本体' if i<=9 else '02 / 两条 AI 路线' if i<=12 else '03 / Agent 协作' if i<=16 else '04 / 建设与平台' if i<=20 else '附录 / 按需答疑'
  body=s['body'].replace('__SCREENSHOT__','data:image/jpeg;base64,'+base64.b64encode((ROOT/'Screenshot_2026-10-15-14-42-11-459_mark.via-edit.jpg').read_bytes()).decode()).replace('__COVER__','data:image/png;base64,'+base64.b64encode((ROOT/'deck/assets/cover-network.png').read_bytes()).decode())
  sections.append(f'<section class="slide {s["cls"]} {"active" if i==1 else ""}" data-page="{i}" aria-label="第 {i} 页：{esc(s["title"])}"><div class="mast"><span>OntoWeave ／ 织义</span><span>{chapter}</span></div><header><h1 class="edit-text">{s["title"]}</h1><p class="lead edit-text">{s["lead"]}</p></header><div class="slide-body">{body}</div><div class="takeaway edit-text">{s["take"]}</div><footer><span>{s["note"]}</span><b>{i:02} / {len(SLIDES)}</b></footer></section>')
  notes.append(dict(title=s['title'],text=s['notes'],sources=[dict(title=S[k][0],href=S[k][1]) for k in s['sources']]))
 markup=''.join(sections)
 css=(HERE/'vendor/frontend-slides/viewport-base.css').read_text()+'\n'+(HERE/'deck.css').read_text()
 js=(HERE/'deck.js').read_text()
 controls='''<nav class="toolbar" aria-label="演示控制"><button id="prev" title="上一页（←）">←</button><span id="pageLabel">01 / 23</span><button id="next" title="下一页（→ 或空格）">→</button><i></i><button id="contents" title="目录（G）">目录</button><button id="steps" aria-pressed="false" title="分步演讲（S）">分步</button><button id="notes" title="逐页演讲稿（N）">讲稿</button><button id="fullscreen" title="全屏（F）">全屏</button><button id="edit" aria-pressed="false" title="编辑正文（E），Ctrl+S 下载修改后的 HTML">编辑</button></nav><div class="progress"><div id="progressBar"></div></div><dialog id="contentsDialog"><div class="dialog-head"><h2>本体论思想在agent中的应用</h2><button data-close="contentsDialog" aria-label="关闭目录">×</button></div><div class="contents-grid">'''+''.join(f'<button data-go="{i}"><span>{i:02}</span>{esc(s["title"])}</button>' for i,s in enumerate(SLIDES,1))+'''</div></dialog><dialog id="notesDialog"><div class="dialog-head"><h2 id="noteTitle"></h2><button data-close="notesDialog" aria-label="关闭讲稿">×</button></div><p id="noteText"></p><div id="noteSources"></div></dialog><div id="toast" role="status" hidden></div>'''
 controls+='<dialog id="imageDialog"><button data-close="imageDialog" aria-label="关闭图片">关闭</button><img src="data:image/jpeg;base64,'+base64.b64encode((ROOT/'Screenshot_2026-10-15-14-42-11-459_mark.via-edit.jpg').read_bytes()).decode()+'" alt="OntoWeave 模型浏览完整截图"></dialog>'
 fontcss=make_fonts(re.sub('<[^>]+>','',markup)+json.dumps(notes,ensure_ascii=False)+controls+js)
 defs='<svg class="svg-defs" aria-hidden="true"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 1 L9 5 L0 9" fill="none" stroke="#73927e" stroke-width="1.8"/></marker></defs></svg>'
 license=(ROOT/'deck/THIRD-PARTY-NOTICES.txt').read_text()
 output='<!doctype html>\n<!--\n'+license+'\n-->\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>本体论思想在agent中的应用 · v3.6</title><style>'+fontcss+css+'</style></head><body>'+defs+'<main class="deck-viewport"><div class="deck-stage" id="stage">'+markup+'</div></main>'+controls+'<script type="application/json" id="notesData">'+json.dumps(notes,ensure_ascii=False).replace('</','<\\/')+'</script><script>'+js+'</script></body></html>'
 (HERE/'editorial.html').write_text(output)
 speech='# 本体论思想在agent中的应用 · v3.6 逐页演讲稿\n\n对应 v3.6 发布版（23 页）。P01–P20 为连续主讲，按约 30–35 分钟准备，实际时长随语速与互动调整；P21–P23 为按需使用的现场问答。正文可直接口述，参考资料集中在稿末，不需朗读。\n\n'
 speech+='\n'.join(f'## P{i:02} {n["title"]}\n\n{n["text"]}\n' for i,n in enumerate(notes,1))
 speech+='\n## 参考资料（不朗读）\n\n'
 for i,n in enumerate(notes,1):
  if n['sources']:
   speech+=f'### P{i:02} {n["title"]}\n\n'+'\n'.join(f'- [{x["title"]}]({x["href"]})' for x in n['sources'])+'\n\n'
 speech=speech.rstrip()+'\n'
 (HERE/'speech.md').write_text(speech)
 (HERE/'speaker-notes.md').write_text(speech)
 (HERE/'slide-manifest.json').write_text(json.dumps([dict(number=i,title=s['title'],body_characters=len(re.sub('<[^>]+>','',s['body']))) for i,s in enumerate(SLIDES,1)],ensure_ascii=False,indent=2))
 content=['# 本体论思想在agent中的应用 · v3.6 内容审阅稿\n\n23 页，包含 20 页正文（含平台能力与截图），以及 3 页按需答疑附录、13 个 FAQ。\n\n本文件便于审阅逐页文字。图示、截图与交互以同版 HTML 为准；完整口述讲稿和依据见 speech.md。\n']
 for i,s in enumerate(SLIDES,1):
  plain=s['body']
  if 'class="ontology-tradeoffs-table"' in plain:
   plain='| 难点 | 在实际业务中意味着什么 | 带来的代价与风险 |\n| --- | --- | --- |\n'+'\n'.join('| '+' | '.join(r)+' |' for r in tradeoffs)+'\n\n'+re.sub(r'<table.*?</table>','',plain)
  if 'class="ai-comparison tech-table"' in plain:
   plain='| 技术 | 主要用途 | 差旅场景中的例子 |\n| --- | --- | --- |\n'+'\n'.join(f'| {name} · {role} | {use} | {example} |' for name,role,use,example in technologies)+'\n\n'+re.sub(r'<table.*?</table>','',plain)
  if 'class="ai-comparison"' in plain:
   table='| 比较维度 | 符号主义 · 显式知识 | 联结主义 · 学习表示 |\n| --- | --- | --- |\n'+'\n'.join('| '+' | '.join(x.replace('<br>','') for x in r)+' |' for r in comparison)+'\n\n'
   plain=re.sub(r'<table class="ai-comparison">.*?</table>',lambda m:table,plain)
  plain=re.sub(r'<div class="row"><b>(.*?)</b><span>(.*?)</span></div>',r'- **\1：** \2\n',plain)
  plain=re.sub(r'<h[23][^>]*>(.*?)</h[23]>',r'\n### \1\n',plain)
  plain=re.sub(r'<div class="expert-definition"><b>(.*?)</b>',r'**\1：** ',plain)
  plain=re.sub(r'<summary>(.*?)</summary>',r'**\1**\n',plain)
  plain=re.sub(r'<br\s*/?>','\n',plain)
  plain=re.sub(r'</(?:p|div|section|h3|h2|pre|summary|details|li|text|button|td|th|tr|span)>','\n',plain)
  plain=html.unescape(re.sub(r'<[^>]+>','',plain))
  plain=re.sub(r'\n{3,}','\n\n',plain).strip()
  content.append(f'## P{i:02} {s["title"]}\n\n{s["lead"]}\n\n{plain}\n\n**本页结论：** {s["take"]}\n\n'+(f'小注：{s["note"]}\n' if s['note'] else ''))
 (HERE/'content.md').write_text('\n'.join(content))
 print(f'Built {len(SLIDES)} slides, {len(output.encode()):,} bytes. Offline fonts and image embedded.')
if __name__=='__main__':main()
