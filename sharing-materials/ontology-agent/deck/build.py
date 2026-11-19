"""Build the offline HTML deck from editable content, CSS, JS and subset fonts.

Run: python build.py
Refresh bundled font subsets when adding characters: python build.py --refresh-fonts
"""
from __future__ import annotations

import base64
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # docs/presentations/ontology-agent/deck -> repository root
SLIDES: list[dict] = []

SOURCES = {
    'rdf': ('W3C · RDF 1.1 Primer', 'https://www.w3.org/TR/rdf11-primer/'),
    'owl': ('W3C · OWL 2 Primer', 'https://www.w3.org/TR/owl2-primer/'),
    'knowledge-graphs': ('Hogan 等 · Knowledge Graphs（2021）', 'https://arxiv.org/abs/2003.02320'),
    'sparql': ('W3C · SPARQL 1.1 Overview', 'https://www.w3.org/TR/sparql11-overview/'),
    'philosophy': ('Stanford Encyclopedia of Philosophy · Logic and Ontology', 'https://plato.stanford.edu/entries/logic-ontology/'),
    'ontology-definition': ('Tom Gruber · Ontology：定义与工程语境', 'https://tomgruber.org/writing/definition-of-ontology/'),
    'ontology101': ('Noy 与 McGuinness · Ontology Development 101', 'https://protege.stanford.edu/publications/ontology_development/ontology101-noy-mcguinness.html'),
    'ontology-blog': ('Palantir 博客 · Ontology: Finding meaning in data（2022）', 'https://blog.palantir.com/ontology-finding-meaning-in-data-palantir-rfx-blog-series-1-399bd1a5971b'),
    'foundry': ('Palantir · Ontology Overview', 'https://www.palantir.com/docs/foundry/ontology/overview/'),
    'mcp': ('Palantir · Ontology MCP', 'https://www.palantir.com/docs/foundry/ontology-mcp/overview/'),
    'palantir-company': ('Palantir · 2025 年报：公司背景与产品', 'https://www.sec.gov/Archives/edgar/data/1321655/000132165526000011/pltr-20251231.htm'),
    'palantir-results': ('Palantir · 2025 全年业绩公告（2026-02-02）', 'https://www.sec.gov/Archives/edgar/data/1321655/000132165526000004/a2025q4ex991earningsrelease.htm'),
    'skywise': ('Airbus · 2017 年与 Palantir 合作推出 Skywise', 'https://www.airbus.com/en/newsroom/press-releases/2017-06-airbus-launches-skywise-aviations-open-data-platform'),
    'project': ('项目名称与技术栈 · 来源摘录', 'sources.html#project'),
    'r4': ('v4.0 多视角与当前能力边界 · 来源摘录', 'sources.html#r4'),
    'acceptance': ('2026-10-06 有界语义验收 · 来源摘录', 'sources.html#acceptance'),
    'retirement': ('R4.0-025 当前退役范围 · 来源摘录', 'sources.html#retirement'),
    'team': ('Modeling Team 职责与建模方法 · 来源摘录', 'sources.html#team'),
    'feedback': ('R4.3-015 写入反馈与信任边界 · 来源摘录', 'sources.html#feedback'),
    'direct-modeling': ('R4.3-024/025 当前直接建模写入 · 来源摘录', 'sources.html#direct-modeling'),
    'demo': ('虚构教学案例 · 统一政策、事实与边界', 'case-materials.md'),
}


def e(value):
    return html.escape(str(value), quote=True)


def reveal(content, step=1, tag='div', cls=''):
    return f'<{tag} class="reveal {cls}" data-step="{step}">{content}</{tag}>'


def svg(content, width=1696, height=562, label='业务关系示意'):
    return f'<svg class="diagram" viewBox="0 0 {width} {height}" role="img" aria-label="{e(label)}">{content}</svg>'


def text(x, y, lines, cls='small-text', anchor='start', gap=36):
    if isinstance(lines, str):
        lines = lines.split('\n')
    spans = ''.join(f'<tspan x="{x}" dy="{0 if i == 0 else gap}">{e(line)}</tspan>' for i, line in enumerate(lines))
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{spans}</text>'


def node(x, y, w, h, title, sub='', cls='', step=0, attrs=''):
    title_y = y + (h/2 + 11 if not sub else 42)
    content = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="node {cls}"/>'
    content += text(x+w/2, title_y, title, 'node-title' + (' dark-text' if cls == 'dark' else ''), 'middle')
    if sub:
        content += text(x+w/2, y+(80 if h >= 95 else 67), sub, 'node-sub' + (' dark-text' if cls == 'dark' else ''), 'middle', 31)
    return f'<g {attrs}>' + (reveal(content, step, 'g') if step else content) + '</g>'


def edge(x1, y1, x2, y2, label='', step=0, cls='', label_pos=None, path=None):
    d = path or f'M{x1},{y1} L{x2},{y2}'
    content = f'<path d="{d}" class="edge {cls}"/>'
    if label:
        lx, ly = label_pos or ((x1+x2)/2, (y1+y2)/2-15)
        content += text(lx, ly, label, 'edge-label', 'middle')
    return reveal(content, step, 'g') if step else content


def footnote(content):
    return f'<p class="note-strip">{content}</p>'


def topic(number, title, content, step=0):
    markup = f'<section class="topic"><div class="number">{number}</div><h3 class="edit-text">{title}</h3><p class="edit-text">{content}</p></section>'
    return reveal(markup, step) if step else markup


def fact(key, value):
    return f'<div class="fact"><span class="key edit-text">{key}</span><span class="edit-text">{value}</span></div>'


def add(title, lead, body, takeaway='', note='', sources=(), cls='', flag=''):
    SLIDES.append(dict(title=title, lead=lead, body=body, takeaway=takeaway, note=note, sources=list(sources), cls=cls, flag=flag))


def chapter(number, title, prompt, route, demo=False):
    add(title, prompt,
        '<div class="chapter-route">'+''.join(f'<span>{x}</span>' for x in route)+'</div>',
        cls='chapter', sources=('demo',) if demo else (),
        flag='虚构教学案例' if demo else '',
        note='本章围绕一个问题展开：'+prompt)
    SLIDES[-1]['chapter'] = number


def policy_card(compact=False):
    return f'<div class="policy{" compact" if compact else ""}"><h3 class="edit-text">RET-DEMO-v1</h3>' + ''.join(
        f'<div class="policy-row"><span class="edit-text">{a}</span><span class="edit-text">{b}</span></div>'
        for a,b in [
            ('适用对象', '普通商品，单件整件退货'),
            ('申请条件', '客户声明未使用<br>0 ≤ 间隔 ≤ 168 小时'),
            ('退款前提', '退回验收通过、客服批准'),
            ('事实来源', '<code>orders.signed_at</code><br>客户输入、外部售后接口'),
            ('范围与状态', '按权限读取，检查分页／截断<br>缺必要信息时补读或询问'),
        ][:4 if compact else 5]) + '</div>'


def returns_graph(complete=False):
    # The same skeleton is used on P11 and P30.
    s = ''
    s += node(18,190,200,108,'客户',step=0)
    s += node(330,190,220,108,'订单',step=0)
    s += node(670,190,230,108,'订单项','一条商品明细',step=0)
    s += node(1055,190,245,108,'退货申请',cls='soft',step=0)
    s += node(1440,190,235,108,'退款处理',step=0)
    s += node(670,420,230,105,'商品',step=0)
    s += node(1040,0,290,110,'RET-DEMO-v1','一份具体政策',cls='soft',step=1)
    s += edge(218,244,330,244,'下单形成',1)
    s += edge(550,244,670,244,'包含',1)
    s += edge(1055,244,900,244,'针对',1)
    s += edge(1440,244,1300,244,'关联',1)
    s += edge(785,298,785,420,'关联',1,label_pos=(835,365))
    s += edge(1178,110,1178,190,'规定申请条件',2,label_pos=(1300,163))
    s += edge(1330,58,1557,190,'规定退款前提',2,label_pos=(1494,85),path='M1330,58 H1557 V190')
    if complete:
        s += reveal(text(22,368,['普通商品','客户声明未使用','0—168 小时'], 'small-text'),2,'g')
        s += reveal(text(1060,376,['条件与范围：普通业务说明','数据映射：签收时间与商品类别','退款前提：验收通过、客服批准'], 'small-text',gap=42),2,'g')
        s += reveal(text(22,542,'具体订单、声明与状态从外部输入取得；模型不复制订单行','guide'),2,'g')
    else:
        s += reveal(text(22,378,['业务概念：退货申请','具体记录：申请 R001','具体订单记录来自外部系统'], 'small-text',gap=40),2,'g')
        s += reveal(text(1055,430,['先认识关系骨架','第四章再补齐条件与映射'], 'small-text',gap=42),2,'g')
    return svg(s,label='客户、订单、订单项、商品、退货申请、退款及政策的关联')


# 01–07: the business understanding problem
cover_art = base64.b64encode((HERE/'assets'/'cover-network.png').read_bytes()).decode()
add('本体如何帮助<br>Agent 理解与处理业务', '让 Agent 读懂业务含义，找到判断依据',
    f'<img class="cover-art" src="data:image/png;base64,{cover_art}" alt="" role="presentation" width="640" height="570">',
    '<span class="cover-question-label">贯穿问题</span>这笔订单能退吗？<br>为什么还不能马上退款？',
    '我们讨论的是 Agent 如何获得并使用业务依据。用同一个退货问题，依次理解业务歧义、本体表达、平台分工和消费判断。电商规则全部虚构，不是行业惯例或法律意见。',
    sources=('project','demo'),cls='cover')
SLIDES[-1]['extra'] = '<p class="cover-intro edit-text">OntoWeave（织义）</p>'

add('目录','四章正文，最后留时间回答建设与维护中的常见问题',
    '<nav class="toc" aria-label="演示目录">'+''.join(
        f'<a href="#{page}" data-go="{page}"><span class="toc-no">{num}</span><b>{title}</b><span class="toc-desc">{desc}</span></a>'
        for num,title,desc,page in [
            ('01','Agent 的业务理解难题','工具调用成功以后，为什么还会答错',3),
            ('02','本体的概念、技术与价值','业务含义怎样表达、查询与复用',8),
            ('03','OntoWeave 与建模方法','平台怎么分工，模型怎样建立',18),
            ('04','电商退货与退款模拟案例','用三笔订单核对完整判断过程',26),
            ('FAQ','常见问题','选型、建设、质量与维护',35),
        ])+'</nav>',
    '看完后，能判断何时值得用本体、Agent 怎样用、由谁建设和验证')

chapter('01','Agent 的<br>业务理解难题','这笔订单能退吗？<br>为什么还不能马上退款？',['任务机制','业务歧义','方法与局限'])

add('Agent 怎样完成一个业务任务','用户：这笔订单能退吗？为什么还不能马上退款？（当前订单 A101）',
    '<div class="flow case-flow">'+''.join(
        reveal(f'<div class="step"><small>{n}</small><b class="edit-text">{title}</b><p class="edit-text">{desc}</p><p class="task-detail edit-text">{example}</p></div>',step)
        for n,title,desc,example,step in [
            ('01','理解请求','语言模型拆分目标','当前订单：A101<br>先判断能否申请退货<br>再解释为何不能退款',0),
            ('02','查业务事实','查询工具与客户输入','A101 属于 A 店<br>普通商品、声明未使用<br>签收：10-01 10:00<br>验收未开始、审批未申请',1),
            ('03','检索候选政策','相似内容同时出现','A 店：签收后七天内<br>B 店：付款后七天内<br>两份都写普通商品可退<br>需要辨清各自适用范围',2),
            ('04','理解政策并判断','关联含义与本次事实','A101 应用 A 店政策<br>10-06 拟申请，距签收 120h<br>按声明可申请退货<br>退款仍需验收及批准',3),
            ('05','解释与继续','语言模型组织回答','按声明可申请退货<br>退款前需验收与批准<br>本次未提交或退款',4)])+'</div>'
    +reveal('<p class="note-strip edit-text" style="margin-top:38px">时间均为 2026 年、UTC+08:00，拟申请为 10-06 10:00。业务判断还要识别申请与退款的不同前提。</p>',4),
    '检索到相似政策后，还要辨清适用对象、时间含义和处理阶段',
    '本页以虚构 A101 展示完整路径，订单号由会话提供。订单归属 A 店；知识库同时检索到 A 店 RET-DEMO-v1 与 B 店 RET-B-DEMO-v1，不能因文字相似混用。前者按签收起算，后者按付款起算，两者都以普通商品及未使用声明为申请条件。Modeling/Agent 需要辨清政策适用商家、时间起点和判断的是申请还是退款。A101 适用 A 店政策，签收到拟申请 120 小时，可申请；尚未验收及批准，不能立即退款。本次没有真实调用、提交申请或退款。下一页把两份完整政策并列，展示错套政策会如何改变结论。',sources=('demo',),flag='虚构教学推演')

add('两份相似政策，两个判断','客服知识库同时找到了两份“七天内可退”政策，Agent 应该用哪一份？',
    '<div class="policy-context edit-text"><b>本次订单：A 店 · A101 · 普通商品 · 声明未使用</b><br>付款 09-28 10:00　签收 10-01 10:00　拟申请 10-06 10:00（2026 年，UTC+08:00）</div>'
    '<div class="policy-comparison"><section><p class="eyebrow">A 店 · RET-DEMO-v1</p><h3 class="edit-text">签收后七天内，可申请退货</h3><p class="policy-quote edit-text">普通商品、声明未使用，<br>从客户签收起算 0—168 小时。</p><p class="policy-calculation edit-text">距签收 <b>120 小时</b>，处于时间窗内。</p><p class="policy-verdict edit-text">本次适用：按声明可申请</p></section>'
    '<section><p class="eyebrow warn">B 店 · RET-B-DEMO-v1</p><h3 class="edit-text">付款后七天内，可申请退货</h3><p class="policy-quote edit-text">普通商品、声明未使用，<br>从付款起算 0—168 小时。</p><p class="policy-calculation edit-text">距付款 <b>192 小时</b>，已超过时间窗。</p><p class="policy-verdict warn edit-text">若错套此政策：会判为超时</p></section></div>'
    +'<p class="note-strip edit-text" style="margin-top:26px">Agent 需要理解：政策归哪家店、约束哪类申请、“七天”从哪里起算。相似文字不能替代适用性判断。</p>',
    'A101 属于 A 店；先确定适用政策，再按对应业务含义判断',sources=('demo',),flag='两份政策均为虚构 · B 店仅作对照',
    note='两份完整政策均为虚构，客服知识库可检索到不同商家的相似内容。A 店 RET-DEMO-v1 和 B 店 RET-B-DEMO-v1 不是同一政策的两种猜测。两者分别适用于各自商家，都要求普通商品、客户声明未使用，时间窗均为连续 0—168 小时且含边界，但起点分别为签收与付款。A101 的付款为 09-28 10:00、签收为 10-01 10:00、拟申请为 10-06 10:00，均为 2026 年 UTC+08:00，得到 192 与 120 小时。实际结论按 A 店政策，B 店结论是展示错用政策的后果，后续案例继续使用 A 店政策。退款另需验收和批准。下一页聚焦六种方法如何帮助 Agent 理解和区分这两份政策。')

METHODS=[('提示词与示例','当前任务、示例','交代本次目标','多应用各自维护，定义容易分叉'),
         ('文档检索 RAG','政策、说明材料','找到相关依据','仍需确认版本、范围与例外'),
         ('微调','训练样本','改善任务适配','难充当随时更新的精确政策库'),
         ('业务工具','查询与操作接口','取得事实或执行','字段与状态的业务含义仍需解释'),
         ('专家澄清','歧义与冲突问题','确认业务口径','确认结论需要继续沉淀与维护'),
         ('本体建模与复用','定义、关系与条件','复用共同语义','依赖正确建模、充分读取与维护')]


def methods_graph(limits=False):
    center_title='共同使用已确认的含义' if limits else '同一退货与退款问题'
    center_sub='客服、仓库与财务共同引用？' if limits else '这笔订单能退吗？\n为什么还不能马上退款？'
    s=node(615,203,465,153,center_title,center_sub,cls='soft')
    positions=[(0,0),(0,210),(0,420),(1196,0),(1196,210),(1196,420)]
    input_lines=[['第 1／5 步：拆清两个问题','分别回答申请资格与退款前提'],['第 3 步：找到 RET-DEMO-v1','取得适用商品、时间窗与退款条件'],['训练阶段：学习售后问答样例','改善拆题与缺信息时的补问'],['第 2／4 步：查事实并计算','取得签收与验收状态、算出 120 小时'],['第 3／4 步：补清含义与口径','确认签收起点及未验收状态的含义'],['第 2—5 步：复用已确认的语义','关联政策、订单项、验收及退款前提']]
    limit_lines=[['商家、起点若写进多个提示词','变更后容易出现不同口径'],['命中 A／B 两份相似政策后','仍需按归属、范围与含义选择'],['学过旧政策不等于取得新政策','仍要查询当前条件与事实'],['返回商家与日期字段','仍需知道字段的业务含义'],['缺失或冲突的口径得到确认后','还需保存，供下一次任务复用'],['共同定义也要建对、读全','政策变化后仍需修订与验证']]
    for i,((x,y),(title,*_)) in enumerate(zip(positions,METHODS)):
        side=i>=3
        s+=node(x,y,500,140,title,'\n'.join(limit_lines[i] if limits else input_lines[i]),step=(i//2+1 if limits else 0))
        target_y=245+(i%3)*35
        start_x=1196 if side else 500
        end_x=1080 if side else 615
        mid_x=1138 if side else 558
        s+=edge(start_x,y+70,end_x,target_y,'支持' if limits else ['拆题','政策','训练','事实','澄清','复用'][i],step=(i//2+1 if limits else 0),label_pos=(mid_x,y+48),path=f'M{start_x},{y+70} H{mid_x} V{target_y} H{end_x}')
    return svg(s,label='六种方法对应退货与退款任务中的具体步骤及判断依据')


add('怎样让 Agent 分清相似政策','围绕上一页的难点：商家是否匹配、时间含义是什么、判断的是哪个阶段',
    '<div class="policy-methods">'+''.join(f'<section><small>{i+1:02d}</small><h3 class="edit-text">{title}</h3><p class="edit-text">{copy}</p></section>' for i,(title,copy) in enumerate([
        ('提示词与示例','明确比较商家、适用范围和起算点；用 A／B 政策对照示例，要求给出选择依据。'),
        ('文档检索 RAG','连同正文取得商家、版本与出处；让 Agent 看到两份完整政策，而非孤立的“七天”。'),
        ('微调','用相似政策的辨别样例学习比较与补问；当前具体政策仍从资料中取得。'),
        ('业务工具','提供订单归属、付款与签收字段及说明；计算 192／120 小时，供已选政策使用。'),
        ('专家澄清','适用范围或字段含义缺失、冲突时，请业务负责人确认；保留确认的依据。'),
        ('本体建模与复用','显式关联政策、商家、时间起点与申请条件，让不同任务引用相同定义。'),
    ]))+'</div>',
    '把相似文字展开为可比较的业务含义，再选择适用政策；这些方法可以组合',
    note='六种方法均围绕 P05 的理解压力展开，不按 P04 的步骤分配角色。提示与示例规定比较维度；RAG 保留商家、版本、范围及出处；微调学习辨别习惯而非记住实时政策；工具提供订单归属、日期与字段说明，不能仅凭算出时间替 Agent 选政策；专家只在缺失或冲突处澄清，P05 已给足的信息不需要重复询问；本体将政策适用商家、条件和时间起点等含义显式关联，供后续读取复用。它不能自动保证政策选择正确，仍需建对、读全和验证。这里的方法是建立和使用本体，本体本身是知识模型。')

add('不同方法的局限性','客服、仓库和财务，能否共同引用“申请、验收、退款”的含义？',
    methods_graph(True),
    '共享文档和词典也能统一口径；是否需要本体，还要看关联与复用的价值',
    note='这里没有证明本体是唯一方案。统一文档、业务词典、共享配置和规则服务也能解决共同口径。后面继续考察：跨对象、跨任务、跨系统的显式关系能否改善知识复用，收益是否值得维护投入。RAG 不局限于关键词匹配，本体也不能消除所有错误。')

# 08–17: ontology and its mechanisms
chapter('02','本体的<br>概念、技术与价值','先说清业务里有什么、各自是什么意思、怎样关联，<br>再讨论 Agent 如何使用。',['定义与表达','使用机制','标准与适用性'])

add('什么是本体（Ontology）','为一块业务建立共同的概念、关系与约束，供人和程序使用',
    '<p class="ontology-definition edit-text">本体是一套可共享的领域定义：<br>明确有哪些概念、它们是什么意思、怎样关联，以及有哪些约束。</p>'
    '<div class="definition-grid">'
    '<section><h3 class="edit-text">概念及含义</h3><p class="edit-text">退货申请：客户请求退回<br>某个订单项。</p></section>'
    '<section><h3 class="edit-text">关系</h3><p class="edit-text">退货申请针对订单项。<br>政策适用于特定商家及商品范围。</p></section>'
    '<section><h3 class="edit-text">条件与约束</h3><p class="edit-text">申请资格与退款前提分开。<br>时间条件明确起点、单位和边界。</p></section></div>'
    '<p class="ontology-terms edit-text"><b>本体论</b>讨论存在及其类别等哲学问题。<br>本演示的<b>本体</b>指知识工程中的 Ontology 模型，用来明确表达业务含义。</p>',
    '本体是知识模型；建模方法论指导怎样建立、验证与维护它',
    note='依据 Gruber 的定义及 Noy/McGuinness 入门教程，以共享的领域概念、含义、关系与约束解释工程本体。专业表述常概括为对领域概念化的显式表达；机器可解释的表示让程序能够引用并处理这些定义。共享强调使用者对含义形成共同约定；显式强调把所需的概念区别和关系写清。退货申请、订单项、政策范围与时间起点的例子均来自虚构教学业务。普通业务条件可先保留为说明，精确形式化程度按需求选择；写出条件不自动得到计算或执行能力。术语上，哲学语境称本体论，知识工程模型在本演示中称本体，这是一项帮助听众理解的用词约定，不能据中文译名判断某篇文献属于哪一学科。本体是模型产物，建模方法论描述访谈、表达、验证与维护过程；围绕本体组织 Agent 是架构思路。',sources=('ontology-definition','ontology101','philosophy','demo'))

add('Palantir 如何将 Ontology 用于业务','一个产品化例子：让应用和 Agent 围绕共同的业务对象工作',
    '<div class="palantir-intro"><div><p class="palantir-idea edit-text">Foundry 将分散的数据<br>连接到业务对象、关系与操作。</p><div class="palantir-layers">'
    '<section><b class="edit-text">业务数据</b><p class="edit-text">订单表、商品数据、售后状态，<br>来自组织的不同系统。</p></section>'
    '<section><b class="edit-text">业务含义</b><p class="edit-text">用订单、商品、退货申请等对象，<br>以及明确的属性与关系表达业务。</p></section>'
    '<section><b class="edit-text">应用与操作</b><p class="edit-text">人员、应用和 Agent 通过获准能力，<br>查询对象并执行定义好的操作。</p></section></div></div>'
    '<aside><h3 class="edit-text">Palantir 是谁</h3><p class="company-summary edit-text">2003 年成立的美国软件公司，<br>面向政府与企业提供数据分析及 AI 软件。</p>'
    '<div class="company-proof"><b>2017 · 项目应用</b><p class="edit-text">与空客合作推出<br>Skywise 航空数据平台。</p></div>'
    '<div class="company-proof"><b>2025 · 公司规模</b><p class="edit-text">全年营收约 44.75 亿美元，<br>同比增长 56%。</p></div>'
    '<p class="micro" style="margin-top:18px">来源：Airbus（2017）及 Palantir（2026-02-02）。<br>公司营收不代表 Ontology 单项技术的贡献。</p></aside></div>',
    'Palantir 展示了一种产品实现；OntoWeave 的能力与业务执行边界在第三章说明',
    note='Palantir 官方博客 Ontology: Finding meaning in data（2022-10-03）以业务概念和关系解释数据的含义；官方 Foundry 文档进一步介绍对象、属性、链接、动作及其治理。左侧以虚构退货业务说明这种产品思路，不是 Palantir 客户运行截图。Foundry 的 Ontology 是连接数据、逻辑与操作的产品运行层；Ontology MCP 为外部 Agent 暴露获准工具。这是具体产品设计，不能将其中每一项能力都当作所有工程本体的定义，也不推导 OntoWeave 具备相同能力。OntoWeave 当前业务数据与执行仍在外部系统。Palantir 2003 年成立，主要平台包括 Gotham、Foundry、Apollo、AIP。2017 年 Airbus 与 Palantir 合作推出 Skywise；2026-02-02 公告 2025 全年营收 44.75446 亿美元，同比增长 56%，分别说明有年份的项目应用和公司整体规模。Palantir 是本体思想的应用者而非发明者。',sources=('ontology-blog','foundry','mcp','palantir-company','palantir-results','skywise'))

add('用本体描述退货业务','先认识对象和关系骨架，稍后补齐条件、事实来源与动作前提',returns_graph(),
    '订单项是一条商品明细；“退货申请”这个概念与“申请 R001”这条记录分别表达',sources=('demo',),flag='业务模型示意')

add('本体中的基本表达','在同一小段业务中，读懂类别、个体、属性、关系和分类',
    '<div class="split wide-left"><div>'+svg(
        node(20,15,350,95,'售后申请')+node(20,207,350,95,'退货申请',cls='soft')
        +node(20,412,350,95,'申请 R001')+node(620,412,325,95,'订单项')
        +edge(195,207,195,110,'是其子类',1,'dashed',label_pos=(335,166))
        +edge(195,412,195,302,'属于该类',2,'dashed',label_pos=(335,367))
        +edge(370,460,620,460,'针对',3)
        +reveal(text(620,215,['属性：申请时间','一个日期时间值'],'small-text'),3,'g')
        +reveal(text(620,310,['RET-DEMO-v1','一份具体政策，也可作为个体'],'small-text'),4,'g'),970,540,'类别、子类、个体、属性与业务关系')+'</div><div class="stack">'
    +'<div class="rule-top"><p class="statement edit-text"><b>类</b>描述一类对象<br><b>个体</b>指一个具体资源</p></div>'
    +reveal('<p class="statement edit-text"><b>属性</b>连接值<br><b>关系</b>连接资源</p>',3)
    +reveal('<p class="small edit-text">虚线表示分类／类型关系<br>实线表示业务关系<br>业务说明同时保留范围、例外与未知</p>',4)+'</div></div>',
    '名字相似不等于含义相同；同一资源需要稳定身份',
    note='业务角色不等于登录权限。正式分类按实际需要使用，不把每个名词强行设为类。语义层可以包含政策等知识个体，但本项目不为 SQL 问答搬入业务表行。',sources=('rdf','demo'))

add('本体、知识图谱与数据库的分工','同一业务，在定义、知识连接和记录存储三个层面表达',
    svg(
        text(0,35,'本体：约定含义与关系','label')
        +text(0,85,'定义对象与可用关系','small-text')
        +node(500,0,310,95,'退货申请',cls='soft')
        +node(1180,0,310,95,'订单项',cls='soft')
        +edge(810,48,1180,48,'针对')
        +edge(655,95,420,265,'使用共同定义',1,label_pos=(535,175),path='M655,95 V155 H420 V265')
        +edge(1335,95,1335,265,'映射到字段与连接',1,label_pos=(1500,175))
        +reveal(text(0,235,'知识图谱：连接具体知识','label'),1,'g')
        +node(0,290,330,100,'RET-DEMO-v1','一份具体政策',step=1)
        +node(550,290,250,100,'普通商品',step=1)
        +node(0,470,330,75,'退货政策',step=1)
        +edge(330,340,550,340,'适用于',1)
        +edge(165,390,165,470,'属于该类',1,'dashed',label_pos=(275,440))
        +reveal(text(430,494,['概念定义也可保存在图中','图数据库可存储知识图谱'],'small-text',gap=40),2,'g')
        +reveal(text(955,235,'数据库：存储与查询记录','label')
            +text(955,278,'orders（虚构数据片段）','guide')
            +'<rect x="955" y="300" width="740" height="210" class="thin"/>'
            +'<path d="M955,355 H1695 M955,430 H1695 M1140,300 V510" class="thin"/>'
            +text(985,335,'id','small-text')+text(1180,335,'signed_at','small-text')
            +text(985,402,'A101','small-text')+text(1180,402,'2026-10-01 10:00+08:00','small-text')
            +text(985,477,'A102','small-text')+text(1180,477,'2026-09-27 10:00+08:00','small-text')
            +text(955,550,'业务行留在外部，schema 也可表达约束','guide'),1,'g'),label='上方本体定义、左下知识关系与右下外部订单表的关联'),
    '本项目将订单等业务行保留在外部数据库，平台保存业务语义及映射',
    note='知识图谱是知识组织方式，数据库是存储与查询系统，层次不同，技术并不互斥。本体可作为图中的概念定义，图数据库也可保存知识图谱，关系型 schema 也有约束表达能力。',sources=('rdf','r4'))

add('本体怎样帮助 Agent 工作','相关定义、关系和必要说明，合起来形成“语义上下文”',
    svg(
        node(610,0,500,115,'业务语义模型','政策、关系、条件与映射',cls='soft')
        +node(40,215,360,130,'用户问题','这笔订单能退吗？')
        +node(620,225,480,130,'消费 Agent','组织任务、核对条件、解释结果',cls='dark')
        +node(1320,220,350,140,'业务答案','问答／分析／操作建议')
        +node(470,460,330,100,'数据库与 API','取得实时事实')
        +node(930,460,360,100,'原始资料 RAG','需要时补充说明')
        +edge(400,280,620,280,'提出任务',1)
        +edge(850,225,850,115,'按权限读取',1,label_pos=(1000,175))
        +edge(720,355,635,460,'查询事实',2,label_pos=(600,410))
        +edge(1000,355,1100,460,'查原始依据',2,label_pos=(1170,408))
        +edge(1100,290,1320,290,'计算并解释',3),label='消费 Agent 读取语义、查询事实与组织答案'),
    '本体提供依据，Agent 组织任务与解释，外部系统提供事实并执行操作',
    note='数据映射说明业务含义对应哪个字段或连接。消费 Agent 是读取已建语义来完成任务的 Agent。知道动作前提不等于具有执行权限。语义访问控制与业务系统授权需要分别验证。',sources=('r4','demo'))

add('业务含义怎样表达与查询','RDF、RDFS、OWL 与 SPARQL 各有职责',
    '<div class="split wide-left"><div>'+svg(
        node(0,130,330,120,'RET-DEMO-v1','主体 subject',cls='soft')
        +node(620,130,300,120,'普通商品','客体 object')
        +edge(330,190,620,190,'适用于',label_pos=(475,165))
        +text(0,80,'RDF 以“主体、谓词、客体”表达陈述','label')
        +text(390,257,'谓词 predicate','guide')
        +text(0,370,['IRI：为资源提供可稳定引用的身份','Turtle：RDF 的一种书写格式'],'small-text',gap=50)
        +text(0,520,'教学词汇示意，不代表专用业务规则执行合同','guide'),950,562,'RDF 三元组示意')+'</div><div class="stack">'
    +'<div class="rule-top"><p class="statement edit-text"><b>RDFS</b>　基础类型与层级</p><p class="small"><code>rdf:type</code>　属于某类<br><code>rdfs:subClassOf</code>　子类</p></div>'
    +reveal('<div><p class="statement edit-text"><b>OWL</b>　更丰富的形式语义</p><p class="small edit-text">表达形式化公理及其含义</p></div>',1)
    +reveal('<div><p class="statement edit-text"><b>SPARQL</b>　查询 RDF 图</p><p class="small edit-text">找到符合图关系的资源与值</p></div>',2)+'</div></div>',
    '能机器读取业务说明，不等于其中所有条件已经形式化或能够自动执行',
    note='RDF 是图数据模型，RDFS 是基础类型及层级词汇，OWL 提供更丰富的形式化语义，SPARQL 查询 RDF。OWL 可以有 RDF 表示，但所有 RDF 并不都是 OWL 2 DL 本体。\n\nTurtle 教学代码：\n@prefix ex: <https://example.org/returns/> .\n@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\nex:ReturnRequest rdfs:subClassOf ex:AfterSalesRequest .\nex:RET-DEMO-v1 rdf:type ex:ReturnPolicy ; ex:appliesTo ex:StandardProduct .\n\n这里只表达类型和关系。168 小时时间窗仍作为普通业务条件说明保留。',sources=('rdf','owl','sparql'))

add('形式推理的作用与边界','由明确的形式前提推出隐含结论，与退款资格计算分别理解',
    '<div class="split wide-left"><div>'+svg(
        node(35,0,420,95,'业务申请')+node(35,205,420,95,'售后申请')
        +node(35,410,420,95,'退货申请',cls='soft')
        +edge(245,205,245,95,'子类',1,'dashed',label_pos=(345,160))
        +edge(245,410,245,300,'子类',1,'dashed',label_pos=(345,365))
        +edge(455,458,455,48,'可推出：子类',2,'ochre-edge',label_pos=(705,255),path='M455,458 H610 V48 H455')
        +text(645,350,['推导线独立显示','分类传递可由 RDFS 支持'],'small-text'),940,540,'分类层级与子类传递推导')+'</div><div class="stack">'
    +'<div class="rule-top"><p class="eyebrow">原理示意</p><p class="statement edit-text" style="margin-top:20px">显式前提<br>形式规则<br>隐含结论</p></div>'
    +reveal('<p class="small edit-text">时间比较与金额计算需计算能力。<br>业务流程由对应系统执行。<br>缺少事实，不自动意味着事实为假。</p>',2)
    +'<span class="pill demo">OntoWeave 当前不提供自动推理运行</span></div></div>',
    '分类推导不能单独证明某张订单可以退款',sources=('owl','rdf','retirement'),flag='原理示意',
    note='本页分类传递可由 RDFS 支持，OWL 能表达更丰富的公理。开放世界下未声明不等于为假。退款需要时间、类别、声明、验收、审批等事实，以及相应计算和业务系统。当前项目已退役自动推理运行，不展示或承诺推理回执。')

add('本体的优势与适用条件','用“为什么还不能退款”连接客服、仓库与财务的任务',
    '<div class="split"><div><div class="rule-top"><h3 class="statement edit-text">共享口径已有轻量方案</h3><p class="statement edit-text" style="margin-top:30px">统一文档、业务词典、<br>共享配置与规则服务，<br>都能帮助多个应用复用定义。</p></div><p class="small edit-text" style="margin-top:40px">固定、简单的任务，可以继续使用更轻的方案。</p></div><div>'
    +svg(node(245,175,370,115,'同一业务语义模型','政策、订单项、验收与审批',cls='soft')
         +node(0,0,260,100,'客服 Agent','申请资格')+node(590,0,260,100,'仓库 Agent','验收要求')
         +node(270,420,310,100,'财务 Agent','退款前提')
         +edge(130,100,290,175,'引用适用条件',1,label_pos=(90,150))
         +edge(720,100,575,175,'引用验收含义',2,label_pos=(720,155))
         +edge(425,420,425,290,'引用审批与状态',3,label_pos=(605,370)),860,540,'三个消费 Agent 复用同一业务语义模型')+'</div></div>',
    '值得建模的地方，在于跨对象、跨任务、跨系统的显式关联能否改善实际复用',
    note='收益依赖定义准确、读取充分、持续维护和消费正确。先选择一个跨环节问题，同条件比较正确性、维护与人工确认成本，不许诺必然优于 RAG 或自动消除幻觉。',sources=('demo',))

# 18–25: platform and modeling method
chapter('03','OntoWeave<br>与建模方法','如何把业务材料变成可用的模型，<br>并让 Agent 可靠地取得它。',['系统分工','建模方法','自动建模','读取验证'])

add('OntoWeave 的定位与责任边界','平台保存与提供业务语义，业务判断和业务执行各有负责人',
    svg(
        node(0,35,360,125,'业务人员','确认含义、范围与歧义')
        +node(0,340,360,125,'建模 Agent','整理资料、提出模型')
        +node(610,195,480,150,'OntoWeave','保存业务语义模型\n管理写入与访问',cls='soft')
        +node(1320,35,375,125,'消费 Agent','读语义、查事实、处理任务')
        +node(1320,340,375,125,'外部业务系统','提供业务数据并执行操作')
        +edge(180,160,180,340,'确认与澄清',1,label_pos=(270,260))
        +edge(360,400,610,275,'提交语义模型',1,label_pos=(465,320))
        +edge(1320,95,1090,244,'按权限读取',2,label_pos=(1185,140))
        +edge(1510,160,1510,340,'独立业务授权',3,label_pos=(1400,265))
        +reveal(text(610,415,['平台边界：确定性检查、存储与读取','外部系统边界：数据访问、业务执行与回执'],'small-text',gap=45),3,'g'),label='业务人员、建模 Agent、平台、消费 Agent 与外部系统的责任分工'),
    '平台检查可执行性与资源完整性，业务含义仍由建模与独立验证确认',
    note='业务角色知识与应用访问控制是不同问题。消费 Agent 是使用已建知识完成业务任务的 Agent。平台不会因为保存了退款动作定义就拥有执行退款的权限或能力。',sources=('project','r4','retirement'))

architecture = (HERE/'assets/ontoweave-architecture.drawio.svg').read_text()
add('系统架构','建模协作、平台服务、外部业务系统与独立验收各有边界',
    architecture,
    '程序负责转换、校验与原子应用；业务含义及真实效果仍需独立验证',
    note='MCP 是连接 Agent 与工具、数据的协议，当前由 FastMCP 提供入口。Modeling、Coordinator、CQ 与 Delivery 承担建模、协调、出题及交付监督职责。当前 R4.3-024/025 已完成工程实现与开发验证：Modeling 直接提交统一图变更，compiler 确定性转换，执行器绑定真实上下文并按批调用 apply_atomic；不是跨批全局事务。正常成功信任回执，随后通过召回及 IRI 周边读取进行语义自查，独立 Acceptance 在生产链之外判断效果。真实自查质量及最终独立语义效果仍未验证。PostgreSQL 保存元数据与工作状态，Oxigraph 保存业务语义图；业务行与执行留在平台外。赭色虚线区的跨阶段协作调度、运行管理界面仅为远期设想，均待实现、规划待确认，不构成已立项或交付承诺。',sources=('project','direct-modeling'),cls='architecture-slide')

add('OntoWeave 的建模方法','先完成一条可读取、可验证的业务链，再扩展相邻范围',
    '<div class="flow" style="grid-template-columns:repeat(4,1fr)">'+''.join(
        reveal(f'<div class="step"><small>0{i+1}</small><b class="edit-text">{a}</b><p class="edit-text">{b}</p></div>',i)
        for i,(a,b) in enumerate([
            ('典型业务问题','“能申请，是否就能退款？”<br>这类问题称为能力问题 CQ'),
            ('逻辑切片','按业务目标、生命周期与依赖<br>分步分析和验证'),
            ('业务语义模型','先完成最小完整链<br>本项目用七视角检查覆盖'),
            ('实际读取与回答','检查消费者是否正确使用<br>再扩展相邻切片'),
        ]))+'</div>'
    +reveal('<div class="reading" style="margin-top:68px"><p class="edit-text">项目级始终保留：<b>共享术语、跨切片依赖、数据与接口映射、跨切片问题。</b><br>读取和回答中的缺口，返回业务澄清与语义修订。</p></div>',4),
    '切片是组织分析与验证的方式；不按表数量直接决定有几个本体',
    note='这里介绍 OntoWeave 当前采用的建模组织方式，其中七视角不是所有本体都必须遵循的通用方法论。能力问题 Competency Question 是模型应当支持回答的业务问题。全面指在当前有界范围内处理重要概念、条件、例外和未知，不是一次建完整个企业。一个逻辑切片不自动对应一个 Ontology 或一个 Agent。',sources=('team','r4'))

VIEWS = [
    dict(title='对象：业务中讨论什么', description='订单、订单项、商品与退货申请。确认每个对象的含义、身份和必要关系。', nodes=['order','item','application']),
    dict(title='行为：有哪些业务动作', description='提交申请、审核和退款。明确动作作用对象与前提，不把动作定义当作已经执行。', nodes=['application','refund']),
    dict(title='规则：在什么条件下成立', description='普通商品、客户未使用声明、0—168 小时时间窗，以及退款所需验收与审批。', nodes=['policy','application','refund']),
    dict(title='角色：谁参与这段业务', description='客户、客服、仓库分别提出申请、确认审批、检查退回商品。业务角色不等于登录权限。', nodes=['application','refund']),
    dict(title='流程：前后阶段怎样衔接', description='申请、退回、验收与退款各有状态。申请可受理与退款完成分别由对应事实支持。', nodes=['application','refund']),
    dict(title='数据映射：含义对应哪个字段', description='签收时刻来自 orders.signed_at，商品类别来自 products.category，表间连接有明确业务含义。', nodes=['order','item','data']),
    dict(title='接口映射：哪个系统提供能力', description='售后状态查询、提交退货申请与执行退款分别对应外部接口，前提、权限和回执分别确认。', nodes=['application','refund','api']),
]
add('OntoWeave 的七个建模视角','本项目用这七个视角组织与检查同一模型，可按场景取舍',
    '<div class="split wide-left"><div id="viewsGraph">'+svg(
        node(25,175,240,105,'订单',attrs='data-view-node="order"')
        +node(355,175,240,105,'订单项',attrs='data-view-node="item"')
        +node(710,175,250,105,'退货申请',cls='soft',attrs='data-view-node="application"')
        +node(340,0,270,105,'政策与条件',attrs='data-view-node="policy"')
        +node(710,405,250,105,'退款',attrs='data-view-node="refund"')
        +node(15,405,270,105,'数据映射',attrs='data-view-node="data"')
        +node(365,405,260,105,'接口映射',attrs='data-view-node="api"')
        +edge(265,228,355,228,'包含')+edge(710,228,595,228,'针对')
        +edge(475,105,835,175,'规定条件',label_pos=(760,110),path='M475,105 V135 H835 V175')
        +edge(835,405,835,280,'关联',label_pos=(900,350))
        +edge(150,405,150,280,'对应字段',label_pos=(235,350))
        +edge(625,457,710,457,'对应能力',label_pos=(670,365)),985,540,'从七个视角观察相同退货业务模型')+'</div><div>'
    +'<div class="view-checklist">'+''.join(f'<button data-view="{i}" aria-pressed="{"true" if i==0 else "false"}"><b>{i+1:02d} {title}</b><span>{example}</span></button>' for i,(title,example) in enumerate([
        ('对象','订单、订单项、商品、退货申请'),
        ('行为','提交申请、审核、退款'),
        ('规则','时间窗、适用范围、退款前提'),
        ('角色','客户、客服、仓库'),
        ('流程','申请、退回、验收、退款'),
        ('数据映射','签收时刻 → orders.signed_at'),
        ('接口映射','售后查询、申请提交、退款执行'),
    ]))+'</div>'
    +'<p class="micro" style="margin-top:22px">每个视角记录：已确认／待澄清／本范围不适用。<span class="screen-only"><br>点击条目，高亮左侧相关内容。</span></p></div></div>',
    '七视角是 OntoWeave 的组织与检查方式，不要求七个本体或七个 Agent',
    note='七视角是 OntoWeave 当前的实现与组织选择，并非通用本体方法论。七项名称与具体例子在 HTML 及 PDF 中同时可见，点击仅改变左图高亮。规则视角保留完整业务条件，但当前不要求生成规则脚本。每个视角以源材料与业务确认作依据，明确已确认、待澄清或不适用，不能用表字段或编码样例猜测业务含义。',sources=('team','retirement','demo'))

add('Agent Team 的自动建模方式','生产协作与独立验收分别承担职责，业务歧义仍需业务确认',
    svg(
        text(0,30,'生产协作','label')
        +node(0,85,330,135,'建模 Modeling','读材料、澄清、提出模型')
        +node(445,85,345,135,'协调 Coordinator','切片、共享定义与反馈',cls='soft')
        +node(910,85,320,135,'出题 CQ','准备能力问题')
        +node(1355,85,340,135,'平台程序','转换、校验、原子应用',cls='ochre')
        +edge(330,152,445,152,'协作',1)
        +edge(790,152,910,152,'核对',1)
        +edge(165,85,1525,85,'Modeling 直接提交',2,path='M165,85 V50 H1525 V85',label_pos=(1110,45))
        +text(0,267,'Modeling 直接提交变更 → 平台程序 → 回执 → 召回／周边自查','small-text')
        +text(0,310,'宿主监督 Delivery：授权、进度、交付与失败跟进','small-text')
        +'<path d="M0,335 H1696" class="thin"/>'
        +text(0,390,'独立验收','label')
        +node(500,420,400,105,'独立消费 Agent','只读已写入模型',step=3)
        +node(1160,420,400,105,'独立判定','核对业务依据与答案',step=3)
        +edge(900,472,1160,472,'提交业务答案',3)
        +reveal(text(0,466,['公开反馈可用于修订','隐藏答案保持隔离'],'small-text',gap=38),3,'g'),label='当前建模 Team 职责与生产外独立消费判定泳道'),
    '自动整理、建模和调用不替代业务确认；成功写入与业务语义通过分别证明',
    note='这里介绍当前 Team 的职责配置，不宣称所有场景都需要固定数量或顺序的 Agent。绿色节点为 Agent 协作，右侧平台程序承担技术转换与执行，并非新增 Agent 角色。Modeling 直接提交变更，不以 CQ 或 Protocol 审批作为必经写入中介。正常成功信任平台回执，召回与周边读取检查语义遗漏。独立验收不能创建、继续或修复被验收的 run，也不能修改保留证据。当前写入工程实现与开发验证完成，真实语义效果未验证。',sources=('team','direct-modeling'))

add('消费 Agent 实际需要读到什么','把“语义上下文”展开为能支撑业务判断的内容',
    '<div class="split wide-left"><div>'+svg(
        node(230,185,390,115,'RET-DEMO-v1','政策身份与说明',cls='soft')
        +node(0,0,270,100,'普通商品','适用对象')+node(580,0,320,100,'申请与退款','条件与前提')
        +node(0,425,300,100,'数据映射','签收、类别、售后状态')
        +node(580,425,320,100,'范围与未知','声明、例外、必要事实')
        +edge(230,185,140,100,'适用于')+edge(620,185,740,100,'规定条件')
        +edge(230,300,150,425,'关联来源')+edge(620,300,740,425,'明确范围'),920,550,'语义读取需要关联政策、对象、条件与数据映射')+'</div><div>'+policy_card()+'</div></div>',
    '按权限读到必需内容，并检查分页与截断；读取状态不保证答案正确',
    note='本页是虚构内容与人可读展示形式，非真实接口响应，也不新增 API 字段。读取还应显示查询的授权范围、返回的相关定义及分页／截断提示。必要内容未读全时继续补读。权限过滤先于候选计数与遍历。平台读取受限、读取失败和外部事实缺失分别处理，不把它们都解释成事实不存在。',sources=('r4','demo'),flag='虚构内容与展示形式，非真实接口响应')

add('当前能力与验证边界','截至 2026-10-14，按需求及保留交付记录陈述',
    '<div class="status-rows">'
    '<div class="status"><div><h3 class="edit-text">已实现能力</h3><p class="date">当前需求与交付范围</p></div><p class="edit-text">多视角语义表达、共享定义、确定性写入、受治理读取，<br>以及数据与接口映射表达。<strong>工程检查通过，不等于业务效果已证明。</strong></p></div>'
    '<div class="status"><div><h3 class="edit-text">已有有界证据</h3><p class="date">2026-10-06 · 工业服务四切片</p></div><p class="edit-text">冻结题集独立验收：<strong>公开 18/18、隐藏 8/8</strong>。<br>仅覆盖当时获准模型与题集，不能作为当前通用准确率。</p></div>'
    '<div class="status"><div><h3 class="edit-text">仍待验证范围</h3><p class="date">10 月 13—14 日后续场景</p></div><p class="edit-text">后续运行存在未通过或未完成验收，R4.0-009 整体仍为 <strong class="partial">PARTIAL</strong>。<br>全范围、SQL/API 联合验收、跨场景重复性与产品化尚未完成。</p></div></div>'
    +footnote('当前不提供 OWL 自动推理、SHACL 专用校验、规则脚本或业务流程执行引擎。'),
    '历史有界通过保留原义，当前部分验证保留边界；本次没有重跑平台验收',
    note='2026-10-06 的两份完整公开／隐藏报告来自同生产状态和 freeze，互斥题集覆盖 26 题，157 引用重放稳定。这是有界历史结果，不代表全场景通过。10 月 13—14 日增量记录包含未完整通过、未完成及平台／运行阻断，不能一概归因于模型质量。R4.0-009 整体仍为 PARTIAL。L0 Runtime、L1 Modeling quality、L2 Repeatability、L3 Productization 分阶段判断。',sources=('r4','acceptance','retirement'),flag='已有记录摘要，本次未重新验收')

# 26–34: one complete, explicitly fictional case
chapter('04','电商退货与退款<br>模拟案例','一家小型电商，希望让客服 Agent 判断退货资格，<br>并说明退款的下一步。',['公开材料','确认口径','建立语义','取得事实','解释与验证'],demo=True)

add('模拟业务背景与输入材料','A 店 · 单件商品整件退货 · 商品款整额退款',
    '<div class="split"><div><p class="statement edit-text">政策与业务确认<br>术语解释<br>数据库字段与编码说明<br>售后接口合同<br>客户本次声明</p><p class="small edit-text" style="margin-top:28px">不涉及运费、促销分摊、部分退货、<br>跨境业务或法律解释。</p></div><div><p class="eyebrow">三个对照订单</p>'
    +fact('A101','10-01 10:00 签收<br>普通商品，声明未使用')
    +fact('A102','09-27 10:00 签收<br>普通商品，声明未使用')
    +fact('A103','签收时刻缺失<br>普通商品，声明未使用')
    +'<p class="small" style="margin-top:25px">拟申请／判断时点：<b>2026-10-06 10:00</b><br>全部时间为 UTC+08:00</p></div></div>',
    '先公开范围、政策与事实来源，后续每个判断才能逐项核对',
    note='模拟政策 RET-DEMO-v1 对三个订单均适用。假设订单归属、当前业务可访问范围和无重复申请已由业务系统确认；这不是语义授权的替代品。所有案例均为教学输入，不是实际平台运行。',sources=('demo',),flag='全部材料与订单均为虚构')

add('建模前的业务确认','字段名和样例值是映射线索，业务确认决定政策含义',
    '<div class="three-cols">'
    +topic('01','“七天内”','需要问：从哪一刻起算？<br>按日历日还是连续小时？<br><br><b class="em">确认：提交减签收，<br>0—168 小时，包含等号。</b>')
    +topic('02','“没使用就能退”','需要问：申请时怎样确认？<br>定制商品是否适用？<br><br><b class="em">确认：普通商品，<br>申请时采用客户未使用声明。</b>',1)
    +topic('03','“申请后退款”','需要问：还有哪些前提？<br>信息缺失怎样处理？<br><br><b class="em">确认：验收通过、客服批准。<br>缺必要事实时保留未知。</b>',2)+'</div>',
    '客户声明与实际验收分别记录；申请受理、具备退款条件和退款完成分别判断',
    note='created_at 不能仅凭名字解释为签收时刻。签收对应 orders.signed_at，类别编码 STANDARD/CUSTOM 的含义也由字段说明与业务确认给出。真实提交时由业务系统按真实时刻重检，教学比较用拟申请时刻。',sources=('demo',),flag='模拟商家已确认的教学口径')

add('业务切片与共享定义','把 P21 的方法具体化为三段范围，逐步完成同一业务链',
    '<div class="three-cols">'
    +topic('01','退货资格','确认适用商品、声明与时间窗。<br><br>首先回答：<br><b class="em">是否允许提出申请？</b>')
    +topic('02','退货处理','表达申请、退回与验收状态。<br><br>继续回答：<br><b class="em">商品实际状态如何确认？</b>',1)
    +topic('03','退款处理','表达审批、退款前提与接口。<br><br>跨环节回答：<br><b class="em">何时具备退款条件？</b>',2)+'</div>'
    +reveal('<div class="reading" style="margin-top:62px"><p class="edit-text">共同引用：<b>客户、订单项、商品、政策、状态含义，以及必要数据与接口映射。</b><br>首条链也需保留“可以申请与退款完成是不同阶段”这一共同语义。</p></div>',2),
    '三个逻辑切片是分析组织方式，不预设三套本体或三个 Agent',sources=('team','demo'),flag='案例建模设计')

add('退货与退款的语义模型','沿用 P11 的骨架，补上已经确认的条件、前提与映射',returns_graph(True),
    '关系用于定位相关知识，普通业务说明保留条件、范围、例外和未知',
    note='RET-DEMO-v1 适用于普通商品，申请条件为未使用声明及 0—168 小时。退款需验收通过、客服批准，执行仍受外部权限和防重复约束。这张图表达业务语义，不计算 A101 的资格，也不把 A101 行数据写入平台。',sources=('demo','retirement'),flag='教学语义模型，不是运行截图')

add('语义怎样连接 SQL 与 API','先按获准语义取得事实，再由外部系统控制业务执行',
    '<div class="split"><div class="stack"><div class="rule-top"><p class="eyebrow">查询事实</p><p class="statement edit-text" style="margin-top:20px">签收时刻 → <code>orders.signed_at</code><br>商品类别 → <code>products.category</code></p><p class="small" style="margin-top:24px">订单项通过 <code>order_id</code> 与 <code>product_id</code><br>连接订单和商品。语义映射约束 SQL。</p></div>'
    +'<div class="reading"><p class="edit-text">声明来自<b>客户本次输入</b>。<br>验收、审批与退款状态来自<b>外部售后查询接口</b>。</p></div></div><div class="stack">'
    +'<div class="rule-top"><p class="eyebrow">执行动作</p><p class="statement edit-text" style="margin-top:20px">提交申请 → <code>POST /returns</code><br>执行退款 → <code>POST /refunds</code></p><p class="small" style="margin-top:24px">外部系统检查条件、业务权限与防重复。<br>语义知识中的前提，不授予操作权限。</p></div>'
    +'<div class="reading"><p class="edit-text"><code>ACCEPTED</code> 只表示退款请求受理。<br><code>SUCCEEDED</code> 才表示系统确认完成。</p></div></div></div>',
    'SQL、时间计算工具和 API 都是教学设计，本次没有接入或调用退款系统',
    note='先读取获准语义和真实 schema，才能在定义、连接与口径约束下生成 SQL。业务库行列访问控制由外部系统负责。示例查询：\nSELECT o.signed_at, p.category\nFROM order_items oi\nJOIN orders o ON oi.order_id = o.id\nJOIN products p ON oi.product_id = p.id\nWHERE o.id = :order_id AND oi.id = :item_id;\n\n售后事实来自 GET /order-items/{id}/after-sales-context，三字段是 inspection_status、approval_status、refund_status。时间差由日期计算工具给出。真正提交由外部系统重检，操作受理不等于完成。上述接口不是 OntoWeave 新增接口。',sources=('demo','r4'),flag='虚构外部字段与接口')

add('案例一：能申请，为什么不能马上退款','A101 · RET-DEMO-v1 · 2026-10-06 10:00+08:00 的模拟判断',
    '<div style="display:grid;grid-template-columns:480px 560px 1fr;gap:45px;height:100%">'
    +'<div>'+policy_card(True)+'</div><div>'
    +'<p class="eyebrow">取得具体事实</p>'
    +fact('订单库','10-01 10:00 签收<br>普通商品')
    +fact('客户输入','声明未使用')
    +fact('计算工具','间隔 <b class="em">120 小时</b><br>0 ≤ 120 ≤ 168')
    +fact('售后接口','验收尚未开始<br>审批尚未申请<br>无退款记录')+'</div><div>'
    +reveal('<div class="result-panel"><h3 class="edit-text">按当前政策和您的未使用声明，<br>可以申请退货。</h3><p class="edit-text">实际商品状态仍待验收。<br>当前尚未验收，也尚未获客服批准，<br><b>不能立即退款。</b></p></div>',1)
    +reveal('<p class="small edit-text" style="margin-top:28px">下一步：如决定申请，由业务系统<br>在实际提交时重检条件与权限。</p>',2)+'</div></div>',
    '可申请、已提交、具备退款条件、退款完成是不同阶段',
    note='签收与类别来自模拟订单库，声明来自客户，时间差来自计算工具。售后接口明确返回 inspection_status=NOT_STARTED、approval_status=NOT_REQUESTED、refund_status=NONE，所以“尚未”有明确依据，不是从空结果猜测。若值缺失或查询失败，则改为暂无法确认并指出待补事实。未进行实际提交或退款。',sources=('demo',),flag='教学推演，非真实运行结果')

add('案例二：超时与信息不足','相同政策，对明确不满足与无法判断分别回答',
    '<div class="split">'
    +'<div class="topic"><p class="eyebrow">A102 · 超时</p><div class="stat" style="margin-top:26px">216 <small>小时</small></div>'
    +'<p class="small" style="margin-top:20px">09-27 10:00 签收，10-06 10:00 拟申请。<br>普通商品，客户声明未使用。</p>'
    +reveal('<div class="result-panel" style="margin-top:30px;border-color:var(--ochre);background:var(--light-ochre)"><h3 class="edit-text">超过 168 小时，<br>不符合本例政策时间条件。</h3><p class="edit-text">解释明确不满足的条件，<br>不编造退款阶段事实。</p></div>',1)+'</div>'
    +'<div class="topic"><p class="eyebrow">A103 · 必要信息缺失</p><div class="stat" style="margin-top:26px;color:var(--muted)">未知</div>'
    +'<p class="small" style="margin-top:20px">签收时刻缺失，无法计算间隔。<br>普通商品，客户声明未使用。</p>'
    +reveal('<div class="result-panel" style="margin-top:30px"><h3 class="edit-text">暂无法判定时间条件，<br>需要补充签收时刻。</h3><p class="edit-text">保留未知并提出补问，<br>不将未知改写成允许或拒绝。</p></div>',2)+'</div></div>',
    '明确不满足的条件可以支持否定结论；必要条件尚未确定时保留相应未知',
    note='A102 有明确超时事实，可解释该条件不满足。A103 只缺少签收时刻，不能据此宣称被拒绝或仍在时间窗内。材料冲突、平台读取失败、权限拒绝与外部事实缺失应分别说明。',sources=('demo',),flag='教学预期，未运行真实验收')

add('怎样验证建模效果','独立检查含义、实际读取与业务回答，避免把写入成功当作质量证明',
    '<div class="check-line">'+''.join(f'<div class="check-stage"><b class="edit-text">{a}</b><p class="edit-text">{b}</p></div>' for a,b in [
        ('资料依据','先确定能力问题、适用范围<br>和可核对的判定依据'),
        ('模型表达','概念、关系、条件、例外<br>与未知是否忠于资料'),
        ('实际检索','在真实授权接口读取<br>必需内容是否取得'),
        ('业务答案','独立消费 Agent 回答<br>独立判定核对依据'),
    ])+'</div>'
    +'<div class="compare-note"><b>同条件比较</b><p class="edit-text">RAG 与本体辅助方案共用相同资料、澄清结果、政策版本、数据快照、题目、工具与权限。<br>尽量固定语言模型及调用条件，改变知识组织与读取方式。</p></div>'
    +'<div class="expected"><span>A101：可申请，不能立即退款</span><span>A102：超时</span><span>A103：补问</span><span>168 小时：含等号</span></div>'
    +footnote('分别记录错误允许、错误拒绝、应补问却强答与合理未知，以及建模、维护、确认和运行成本。'),
    '显式语义连接依据，外部事实支持结论，业务系统控制执行，独立验证检查整条链',
    note='正式验证覆盖正常、边界、未知、跨切片和权限。边界还包括负间隔、0、168 小时加 1 秒、定制、已使用／声明缺失、审批缺失、重复退款及 ACCEPTED/SUCCEEDED 区别。这些只是待验证设计。不能只给本体方案补全业务规则，再将所有收益归因于本体。本页无真实提升比例。',sources=('demo','r4'),flag='验证设计与教学预期')

# 35–37: FAQ, outside the four chapters
def faq(items, cls=''):
    return f'<div class="qa {cls}">'+''.join(
        f'<details open {"id="+chr(34)+"maintenanceQuestion"+chr(34) if maintenance else ""}><summary class="edit-text">{q}</summary><div class="answer edit-text">{a}</div></details>'
        for q,a,maintenance in items)+'</div>'


add('FAQ：什么时候值得使用本体','先看当前任务与已有方案，再决定是否增加显式语义建模',
    faq([
        ('已经有 RAG，还需要本体吗？','文档检索已能稳定回答时，可以继续使用。跨对象、跨任务的关系需要明确复用时，可试用本体并做同条件比较。',False),
        ('直接把业务规则写进提示词不行吗？','小范围任务可以。文档、词典和规则服务也能共享口径。显式关联带来的复用收益值得投入时，再进一步建模。',False),
        ('本体会替代数据库或业务系统吗？','业务记录与操作仍留在原系统。本体提供业务含义、关系、条件及系统映射。',False),
        ('所有业务都要先建本体吗？','优先选择含义歧义多、跨系统关系多、同一定义被反复使用的场景。简单固定任务可以采用更轻的方案。',False),
        ('本体与知识图谱有什么区别？','本体明确概念、含义和关系；知识图谱用实体与关系组织知识，可使用或包含本体定义。两者可以结合。',False),
    ],'full')+'<nav class="backlinks"><a href="#7" data-go="7">回看方法局限 P07</a><a href="#13" data-go="13">回看概念分工 P13</a><a href="#17" data-go="17">回看适用条件 P17</a></nav>',
    '从一个有代表性的跨环节问题试起，比较正确性与实际投入',
    note='本页五问可点击问题收起或展开。本体与知识图谱有重叠，不能简单理解为互斥技术或只有模式／只有实例。本体强调共享含义与语义定义，知识图谱强调以图组织知识，也可以含有本体定义。收益比较应共用材料、业务澄清、语言模型、题目、数据与工具条件。选择本体的依据是实际复用、理解和维护收益。',sources=('owl','knowledge-graphs'),cls='faq-selection')

add('FAQ：怎么建，哪些工作需要人参与','从一条有界业务链开始，按实际依赖安排分工',
    faq([
        ('必须先学会 RDF 和 OWL 吗？','业务人员先确认概念与口径，技术人员选择表达及查询方式。理解本体不要求先写 OWL，当前项目也不要求自动推理。',False),
        ('七个视角是通用的本体方法论吗？','这是 OntoWeave 当前的组织与检查方式，可按场景取舍；其他方案可以不同，也不要求七个本体或 Agent。',False),
        ('Agent 能全自动把模型建好吗？','可以自动整理资料、提出模型并调用平台。资料缺失、口径冲突与授权仍需确认，质量由独立验证判断。',False),
        ('是否需要一次建完整个企业？','先完成一条有代表性、可验证的业务链，再维护共享定义，并逐步扩展相邻切片。',False),
    ],'full')+'<nav class="backlinks"><a href="#21" data-go="21">建模方法 P21</a><a href="#22" data-go="22">七个视角 P22</a><a href="#23" data-go="23">Team 分工 P23</a></nav>',
    '自动化承担整理与调用，业务人员确认含义，独立验证判断是否可用',sources=('team','retirement'))

add('FAQ：怎样保证质量并持续维护','定义、事实、检索和使用都需要检查；政策变更还需外部系统对齐',
    '<div class="faq-layout"><div>'+faq([
        ('有了本体就不会产生幻觉了吗？','源材料、模型、检索与 Agent 使用都可能出错。需要逐环节验证，也允许合理回答未知。',False),
        ('业务规则变了，是否要全部重建？','业务负责人确认新口径、生效时间和范围，再修订相关定义及映射，检查受影响问题。修改范围由实际依赖决定。',True),
        ('怎样评估成本与收益？','同资料、同澄清、同工具比较正确性和完整性，分别记录建模、维护、人工确认与调用成本。',False),
        ('本体权限能保护数据库和退款吗？','语义权限控制语义知识。数据库行列访问与退款操作权限由外部系统执行，必须分别验证。',False),
    ],'full')+'</div><aside class="faq-aside"><div class="maintenance visible" id="maintenanceDiagram"><h3>政策变更示例</h3><p class="version">168 → 240 小时</p><p>自 <b>2026-11-01 00:00+08:00</b><br>起提交的申请采用 v2。<br>此前提交的仍按 v1。</p><p>业务负责人确认<br>维护者修订语义<br>系统负责人对齐执行<br>独立验证新旧边界</p><p class="micro">独立教学变更，不改变前三例。<br>不代表自动影响分析或任意历史版本读取功能。</p></div></aside></div>',
    '结合你的业务继续讨论：哪些含义、关系与判断，最需要共同引用？',
    note='v2 假设只将时间窗从 168 改为 240 小时，以提交申请时刻决定新旧政策，而非签收时刻。维护者保留解释旧申请所需的 v1 定义，检查相关条件与数据／接口映射，外部系统负责人对齐实际执行，再独立验证新旧适用范围、240 小时及加 1 秒、缺提交时刻等问题。这是人和 Agent 的维护工作，不承诺平台自动计算影响或固定读取同一资源任意历史版本。A101—A103 的 v1 结论保持原义。',sources=('demo','r4'),flag='v2 为独立教学维护示例')


def section_name(n):
    if n <= 2:
        return '让 Agent 读懂业务含义'
    if n <= 7:
        return '01 / Agent 的业务理解难题'
    if n <= 17:
        return '02 / 本体的概念、技术与价值'
    if n <= 25:
        return '03 / OntoWeave 与建模方法'
    if n <= 34:
        return '04 / 电商退货与退款模拟案例'
    return '常见问题 FAQ'


def plain(s):
    return html.unescape(re.sub('<[^>]+>', '', s.replace('<br>', ' ')))


def make_sources():
    cache = HERE / 'project-sources.json'
    if not cache.exists() or '--refresh-sources' in sys.argv:
        excerpts = {}
        specs = [
            ('project','README.md','## Project Name','## Repository Layout'),
            ('r4','docs/requirements/requirements-v4.0.md','### R4.0-009 ','**后续授权收回**'),
            ('acceptance','docs/delivery/records/2026-10-06-v4-glmflash-semantic-acceptance-record.md','## 最新：','## '),
            ('retirement','docs/requirements/requirements-v4.0.md','### R4.0-025 ','#### 2.'),
            ('team','modeling_team/skills/README.md',None,None),
            ('feedback','docs/requirements/requirements-v4.3.md','### R4.3-015 ','### R4.3-016 '),
            ('direct-modeling','docs/requirements/requirements-v4.3.md','### R4.3-024 ',None),
        ]
        for key,path,start,end in specs:
            content=(ROOT/path).read_text()
            if start:
                content=content[content.index(start):]
                # Search beyond the first heading, even when end is a generic heading.
                stop=content.find(end,len(start)) if end else -1
                if stop>=0:
                    content=content[:stop]
            excerpts[key]=dict(path=path,text=content[:15000].rstrip())
            if key == 'direct-modeling':
                excerpts[key]['date'] = '2026-10-15'
        cache.write_text(json.dumps(excerpts,ensure_ascii=False,indent=2)+'\n')
    excerpts=json.loads(cache.read_text())
    content=''.join(f'<section id="{key}"><h2>{e(SOURCES[key][0])}</h2><p class="origin">原始路径：<code>{e(item["path"])}</code> · {e(item.get("date", "2026-10-14"))} 内容摘录</p><details open><summary>查看原文摘录</summary><pre>{e(item["text"])}</pre></details></section>' for key,item in excerpts.items())
    page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>来源与项目证据 · 本体与 Agent</title><style>body{max-width:1100px;margin:60px auto;padding:0 30px;background:#f5f3ec;color:#16382e;font:18px/1.8 sans-serif}h1{font-size:38px}h2{font-size:27px;margin-top:60px}a{color:#2c7053}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.8 monospace;background:#e9ede2;padding:25px}.origin{color:#617068;font-size:15px}section{scroll-margin-top:30px}</style><a href="index.html">返回演示入口</a><h1>来源与项目证据</h1><p>以下为制作时的项目文件摘录。历史通过、当前部分验证与教学案例分别保留。外部标准及产品事实的原始来源见逐页讲解备注。</p>'+content+'</html>'
    (HERE/'sources.html').write_text(page.replace('<meta charset="utf-8">','<meta charset="utf-8"><link rel="icon" href="data:,">',1))
    return page


def font_css(body):
    if '--refresh-fonts' in sys.argv:
        from fontTools import subset
        from fontTools.ttLib import TTFont
        for dest,src in [
            ('sans-regular.woff','NotoSansCJK-Regular.ttc'),
            ('sans-bold.woff','NotoSansCJK-Bold.ttc'),
            ('serif-bold.woff','NotoSerifCJK-Bold.ttc'),
        ]:
            font=TTFont('/usr/share/fonts/opentype/noto/'+src,fontNumber=2)
            options=subset.Options()
            options.flavor='woff'
            sub=subset.Subsetter(options=options)
            sub.populate(text=body+'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz＋−／→≤≥？—·×')
            sub.subset(font)
            font.flavor='woff'
            font.save(HERE/'assets'/dest)
    css=(HERE/'deck.css').read_text()
    for token,name in [('SANS_REGULAR','sans-regular.woff'),('SANS_BOLD','sans-bold.woff'),('SERIF_BOLD','serif-bold.woff')]:
        data=base64.b64encode((HERE/'assets'/name).read_bytes()).decode()
        css=css.replace('__'+token+'__','data:font/woff;base64,'+data)
    return css


def write_index():
    groups=[('封面与目录',1,2),('01 · Agent 的业务理解难题',3,7),('02 · 本体的概念、技术与价值',8,17),('03 · OntoWeave 与建模方法',18,25),('04 · 电商退货与退款模拟案例',26,34),('常见问题 FAQ',35,37)]
    sections=''
    for title,start,end in groups:
        cards=''.join(f'<a class="page" href="editorial.html#{i}"><img loading="lazy" src="previews/{i:02}.png" alt="第 {i} 页：{e(plain(SLIDES[i-1]["title"]))}"><span><em>{i:02}</em>{e(plain(SLIDES[i-1]["title"]))}</span></a>' for i in range(start,end+1))
        sections+=f'<section><h2>{e(title)}</h2><div class="grid">{cards}</div></section>'
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>本体与 Agent · OntoWeave 演示</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f5f3ec;color:#16382e;font:18px/1.6 'Noto Sans CJK SC',sans-serif}main{max-width:1480px;margin:0 auto;padding:55px 55px 80px}header{border-top:2px solid #73927e;padding-top:20px}header small{letter-spacing:2px;color:#617068}h1{font-family:'Noto Serif CJK SC',serif;font-size:52px;line-height:1.5;margin:40px 0 15px}header p{color:#617068}nav{display:flex;gap:15px;flex-wrap:wrap;margin-top:32px}nav a{padding:12px 23px;color:#16382e;border:1px solid #73927e;text-decoration:none}nav a.primary{background:#16382e;color:#f5f3ec}section{margin-top:70px}h2{font-size:25px;font-weight:400;border-bottom:1px solid #bfccbf;padding-bottom:18px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}.page{color:inherit;text-decoration:none;display:block}.page img{display:block;width:100%;aspect-ratio:16/9;object-fit:contain;background:#e1e9dc;border:1px solid #d2dacb}.page span{display:flex;gap:13px;line-height:1.6;font-size:16px;margin-top:10px}.page em{font-style:normal;color:#73927e;font-variant-numeric:tabular-nums}.page:hover img{outline:2px solid #2c7053}.usage{font-size:16px;color:#617068;border-top:1px solid #bfccbf;padding-top:28px;margin-top:60px}a:focus-visible{outline:3px solid #9c6c36}@media(max-width:800px){main{padding:25px}.grid{grid-template-columns:repeat(2,1fr)}h1{font-size:35px}}@media(max-width:500px){.grid{grid-template-columns:1fr}}
    </style><main><header><small>ONTOWEAVE · 2026.10.14</small><h1>本体如何帮助 Agent<br>理解与处理业务</h1><p>让 Agent 读懂业务含义，找到判断依据 · 37 页，四章正文与 13 个 FAQ</p><nav><a class="primary" href="editorial.html">开始演示</a><a href="editorial.pdf">阅读 PDF</a><a href="speaker-notes.md">逐页讲解备注</a><a href="case-materials.md">教学材料</a><a href="sources.html">项目来源摘录</a></nav></header>'''+sections+'''<div class="usage">方向键或空格分步展示。A 展开当前页，N 讲解备注，G 返回目录，F 全屏，E 编辑正文，Ctrl+S 下载修改后的 HTML。<br>电商案例为虚构教学推演，未接入真实订单或退款系统。项目状态按 2026-10-14 保留记录陈述。</div></main></html>'''
    (HERE/'index.html').write_text(page.replace('<meta charset="utf-8">','<meta charset="utf-8"><link rel="icon" href="data:,">',1))


def main():
    assert len(SLIDES)==37, len(SLIDES)
    plan_path=HERE/'source-plan.md'
    if not plan_path.exists():
        plan_path.write_bytes((ROOT/'docs/presentations/2026-10-14-ontology-agent-next-version-plan.md').read_bytes())
    plan=plan_path.read_text()
    case=plan.split('## 四、模拟业务的一致性底稿\n',1)[1].split('## 五、',1)[0]
    (HERE/'case-materials.md').write_text('# 电商退货与退款：虚构教学材料\n\n本文件用于核对演示 P24、P27—P34 及 P37 的统一口径。不是平台运行报告，也不是行业或法律规定。\n\n'+case)
    notes=[]
    for n,slide in enumerate(SLIDES,1):
        match=re.search(rf'### P{n:02}｜[^\n]+\n(.*?)(?=\n### P|\n## |\Z)',plan,re.S)
        extra=[]
        if match:
            for label in ('讲解深度','技术备注','承接下一页'):
                line=re.search(rf'- \*\*{label}：\*\* (.*)',match.group(1))
                if line:
                    extra.append(('转场：' if label=='承接下一页' else '')+re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',line.group(1)).replace('**',''))
        note=slide['note']+'\n\n'+'\n\n'.join(extra)
        notes.append(dict(page=n,title=plain(slide['title']),text=note.strip(),sources=[dict(title=SOURCES[x][0],href=SOURCES[x][1]) for x in slide['sources']]))
    (HERE/'speaker-notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
    note_md='# 本体与 Agent：逐页讲解备注\n\n37 页，四章正文与 FAQ。案例为虚构教学推演，项目状态为 2026-10-14 记录摘要。\n\n'
    for item in notes:
        note_md+=f'## P{item["page"]:02} · {item["title"]}\n\n{item["text"]}\n\n'
        if item['sources']:
            note_md+='来源：'+'、'.join(f'[{x["title"]}]({x["href"]})' for x in item['sources'])+'\n\n'
    (HERE/'speaker-notes.md').write_text(note_md)
    sources_page=make_sources()
    parts=[]
    for n,slide in enumerate(SLIDES,1):
        long=' long' if len(plain(slide['title']))>26 else ''
        chapter_markup=f'<div class="chapter-no" aria-hidden="true">{slide["chapter"]}</div><div class="chapter-kicker">第 {int(slide["chapter"])} 章</div>' if 'chapter' in slide else ''
        parts.append(f'''<section class="slide {slide['cls']}" id="slide-{n}" aria-label="第 {n} 页：{e(plain(slide['title']))}">
<div class="mast"><span>OntoWeave <span style="font-weight:400">／ 织义</span></span><span class="section-name">{section_name(n)}</span></div>{chapter_markup}
<h1 class="page-title edit-text{long}">{slide['title']}</h1><p class="lead edit-text">{slide['lead']}</p>
<div class="body">{slide['body']}</div>{slide.get('extra','')}
<p class="takeaway edit-text">{slide['takeaway']}</p><div class="footer"><span class="flag">{slide['flag'] or '本体与 Agent'}</span><span>{n:02} / 37</span></div></section>''')
    markup='\n'.join(parts)
    css=font_css(markup+note_md+plan+sources_page+(HERE/'deck.js').read_text())
    definitions='''<svg width="0" height="0" aria-hidden="true" style="position:absolute"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="#73927e" stroke-width="1.6"/></marker><marker id="type-arrow" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M1,1 L11,6 L1,11 Z" fill="#f5f3ec" stroke="#73927e" stroke-width="1.4"/></marker><marker id="ochre-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="#9c6c36" stroke-width="1.6"/></marker></defs></svg>'''
    controls='''<nav id="toolbar" aria-label="演示控制"><button id="prevButton" title="上一步">←</button><input id="pageInput" type="number" min="1" max="37" value="1" aria-label="跳转到页码"><span class="total">/ 37</span><button id="nextButton" title="下一步">→</button><button id="contentsButton">目录</button><button id="expandButton">展开</button><button id="notesButton">备注</button><button class="optional" id="editButton" aria-pressed="false">编辑</button><button class="optional" id="saveButton">保存</button><button class="optional" id="fullscreenButton">全屏</button><button id="helpButton" aria-label="快捷键帮助">?</button></nav><div class="progress-track" aria-hidden="true"><i id="progress"></i></div>
<aside id="notesPanel" aria-label="讲解备注与来源" hidden><button id="closeNotes" aria-label="关闭备注">×</button><h2 id="noteTitle"></h2><div id="noteText" class="notes-copy"></div><div id="noteSources" class="note-sources"></div></aside>
<aside id="helpPanel" aria-label="演示快捷键" hidden><button id="closeHelp" aria-label="关闭帮助">×</button><h2>演示快捷键</h2><p><kbd>→</kbd> <kbd>空格</kbd> 下一步或下一页<br><kbd>←</kbd> 上一步或上一页<br><kbd>A</kbd> 展开本页　<kbd>N</kbd> 讲解备注<br><kbd>G</kbd> 目录　<kbd>F</kbd> 全屏<br><kbd>E</kbd> 编辑正文　<kbd>Ctrl+S</kbd> 下载 HTML<br><kbd>Home</kbd> 首页　<kbd>End</kbd> 末页<br><kbd>Esc</kbd> 关闭面板或退出编辑<br>手机横屏可左右滑动翻页。</p></aside><div id="toast" role="status" hidden></div>'''
    safe_json=lambda obj:json.dumps(obj,ensure_ascii=False).replace('</','<\\/')
    page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="本体如何帮助 Agent 理解与处理业务。37 页互动演示，四章正文与 FAQ。OntoWeave（织义）。"><title>本体与 Agent · OntoWeave</title><style>{css}</style></head><body>{definitions}<main id="viewport"><div id="stage">{markup}</div></main>{controls}<script type="application/json" id="speakerNotes">{safe_json(notes)}</script><script type="application/json" id="viewData">{safe_json(VIEWS)}</script><script>{(HERE/'deck.js').read_text()}</script></body></html>'''
    (HERE/'editorial.html').write_text(page.replace('<meta charset="utf-8">','<meta charset="utf-8"><link rel="icon" href="data:,">',1))
    write_index()
    manifest=dict(title='本体如何帮助 Agent 理解与处理业务',date='2026-10-14',slides=37,chapters=4,faq=13,pages=[dict(page=i,title=plain(x['title']),section=section_name(i)) for i,x in enumerate(SLIDES,1)])
    (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(f'Built {len(SLIDES)} slides · {len(page.encode()):,} bytes · offline fonts embedded')


if __name__=='__main__':
    main()
