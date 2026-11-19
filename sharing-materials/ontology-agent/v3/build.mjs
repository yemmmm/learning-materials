import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const BUILD = path.join(ROOT, '.build-v3');
const RUNTIME = process.env.ONTO_PRESENTATION_RUNTIME || '/home/yangxiang/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(RUNTIME, 'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);

const C = { paper:'#f5f3ec', ink:'#16382e', green:'#2c7053', muted:'#617068', line:'#bfccbf', edge:'#73927e', soft:'#e1e9dc', ochre:'#9c6c36', lightOchre:'#eee4d3', red:'#9b5146', lightRed:'#f0e4de' };
const SANS = 'Noto Sans CJK SC';
const SERIF = 'Noto Serif CJK SC';
const P = Presentation.create({ slideSize:{ width:1920, height:1080 } });
const slides = [];
let slide;
let n = 0;
let element = 0;

function box(x,y,w,h,fill='none',stroke='none',width=1.8,geometry='rect',name='') {
  return slide.shapes.add({name:name||`p${n}-shape-${++element}`, geometry, position:{left:x,top:y,width:w,height:h}, fill, line:{fill:stroke,width:stroke==='none'?0:width,style:'solid'}});
}
function text(value,x,y,w,h,size=32,color=C.ink,opts={}) {
  const s=box(x,y,w,h,opts.fill||'none','none',0,'textbox',opts.name||`p${n}-text-${++element}`);
  s.text=value;
  s.text.style={fontSize:size,typeface:opts.serif?SERIF:SANS,color,bold:opts.bold||false,alignment:opts.align||'left',verticalAlignment:opts.valign||'top',autoFit:'none',wrap:'none',lineSpacing:1.25,insets:{top:0,right:0,bottom:0,left:0}};
  return s;
}
function rule(x,y,w,color=C.line,width=1.5) { return box(x,y,w,0,'none',color,width,'line'); }
function line(x1,y1,x2,y2,color=C.edge,width=2,dashed=false) {
  const s=box(Math.min(x1,x2),Math.min(y1,y2),Math.abs(x2-x1),Math.abs(y2-y1),'none',color,width,'line');
  s.position={left:Math.min(x1,x2),top:Math.min(y1,y2),width:Math.abs(x2-x1),height:Math.abs(y2-y1),verticalFlip:(x2-x1)*(y2-y1)<0};
  if(dashed)s.line={fill:color,width,style:'dashed'};
  return s;
}
function node(x,y,w,h,title,sub='',kind='plain',size=34) {
  const fill=kind==='dark'?C.ink:kind==='soft'?C.soft:kind==='ochre'?C.lightOchre:C.paper;
  const stroke=kind==='soft'||kind==='dark'?'none':kind==='ochre'?C.ochre:C.edge;
  const s=box(x,y,w,h,fill,stroke);
  const titleY=sub?y+22:y+(h-size*1.4)/2;
  text(title,x+12,titleY,w-24,size*1.6,size,kind==='dark'?C.paper:C.ink,{align:'center',bold:true});
  const subOffset=22+size*1.3+14;
  if(sub)text(sub,x+10,y+subOffset,w-20,h-subOffset-8,25,kind==='dark'?'#d7e1d4':C.muted,{align:'center'});
  return s;
}
function edge(a,b,label='',lx=0,ly=0,lw=200,opts={}) {
  const q=slide.shapes.connect(a,b,{kind:opts.kind||'straight',fromSide:opts.from||'right',toSide:opts.to||'left',line:{fill:opts.color||C.edge,width:opts.width||2.5,style:opts.dashed?'dashed':'solid'},tail:{type:opts.dashed?'triangle':'arrow',width:'med',length:'med'}});
  if(label)text(label,lx,ly,lw,40,opts.size||25,opts.color||C.muted,{align:'center',fill:C.paper});
  return q;
}
function label(value,x,y,w=320,color=C.green,size=25) {return text(value,x,y,w,45,size,color,{bold:true});}
function para(value,x,y,w,size=30,color=C.muted) {return text(value,x,y,w,Math.max(48,value.split('\n').length*size*1.5),size,color);}
function topic(x,y,w,title,body,number='') {
  rule(x,y,w,C.edge,2);
  if(number)text(number,x,y+25,w,65,48,C.edge,{serif:true});
  label(title,x,y+(number?101:25),w,C.ink,35);
  para(body,x,y+(number?167:91),w,30);
}
function base(title,lead,takeaway,foot='',section='本体与 Agent') {
  n+=1; slide=P.slides.add(); slide.background.fill=C.paper;
  slides.push({number:n,title,lead,takeaway,foot,notes:'',sources:[]});
  rule(112,61,1696,C.edge,2);
  text('OntoWeave ／ 织义',112,81,520,40,23,C.ink);
  text(section,1300,81,508,40,21,C.muted,{align:'right'});
  text(title,112,143,1696,95,title.length>26?57:66,C.ink,{bold:true,name:`p${n}-title`});
  if(lead)text(lead,114,245,1690,57,29,C.muted);
  if(takeaway){rule(112,932,1696);text(takeaway,112,954,1696,53,29,C.green);}
  if(foot)text(foot,112,1021,1540,35,20,C.ochre);
  text(`${String(n).padStart(2,'0')} / 18`,1660,1021,148,35,20,C.muted,{align:'right'});
  return slide;
}
function notes(value,sources=[]) {
  const d=slides.at(-1);d.notes=value;d.sources=sources;
  slide.speakerNotes.textFrame.setText(value+(sources.length?'\n\n参考资料：\n'+sources.join('\n'):''));
}
const SOURCES={
  gruber:'Tom Gruber · Ontology Definition: https://tomgruber.org/writing/definition-of-ontology/',
  rdf:'W3C · RDF 1.1 Primer: https://www.w3.org/TR/rdf11-primer/',
  owl:'W3C · OWL 2 Primer: https://www.w3.org/TR/owl2-primer/',
  kg:'Hogan et al. · Knowledge Graphs: https://arxiv.org/abs/2003.02320',
  project:'OntoWeave 原项目：README.md；docs/requirements/requirements-v4.0.md（R4.0-008、R4.0-025）；docs/requirements/requirements-v4.3.md（R4.3-024/025）。',
};

// 01 — Keep the established editorial cover and reuse the original artwork.
base('','','','','业务含义怎样成为 Agent 可用的知识');
text('本体与 Agent',112,229,1110,155,104,C.ink,{bold:true,serif:true,name:'p1-title'});
para('业务含义怎样成为\nAgent 可用的知识',116,425,1080,48,C.ink);
label('以一张差旅申请为例',116,666,850,C.green,29);
para('OntoWeave（织义）',116,805,900,30);
slide.images.add({blob:new Uint8Array(await fs.readFile(path.join(ROOT,'deck/assets/cover-network.png'))),contentType:'image/png',position:{left:1440,top:187,width:330,height:300},fit:'contain',alt:'复用 v2.3 的抽象关系网络装饰'});
box(1235,435,490,350,C.paper,C.edge,2);
label('差旅申请',1270,470,390,C.ink,36);
text('T-101',1570,480,120,40,25,C.muted,{align:'right'});
rule(1270,540,420);
text('申请人',1270,574,130,45,28,C.muted);text('张三',1435,574,240,45,32,C.ink,{bold:true});
text('所属部门',1270,645,150,45,28,C.muted);text('研发部',1435,645,240,45,32,C.ink,{bold:true});
text('该由谁审批？',1270,819,440,67,43,C.green,{serif:true,bold:true});
notes('我们从一件很普通的事情开始：张三提交了一张差旅申请，希望 Agent 帮忙找到审批人。沿着这个问题，我们会认识本体是什么，区分本体与 RDF、OWL 等表达技术，再看 Agent 如何使用领域知识，最后介绍 OntoWeave。这里的组织、人员关系与政策均为教学设定。');

// 02 — Two business relationships, one policy.
base('张三的差旅申请，该由谁审批？','同一位申请人，关联着不同的业务角色','找到审批人，需要把政策中的含义与具体人员对应起来','虚构组织与政策，仅用于教学。','01 / 认识本体');
box(112,329,1696,114,C.soft);
text('本例政策',145,365,210,48,28,C.green,{bold:true});
text('差旅申请由申请人当前所属部门的负责人审批',370,358,1390,60,37,C.ink,{bold:true});
const z2=node(200,582,300,128,'张三','申请人');
const d2=node(810,582,350,128,'研发部','张三所属部门','soft');
const l2=node(1460,582,300,128,'李敏','研发部负责人','dark');
const w2=node(810,780,350,105,'王强','', 'plain',32);
edge(z2,d2,'所属部门',530,609,250);
edge(d2,l2,'部门负责人',1180,609,255,{color:C.green,width:3});
edge(z2,w2,'直属主管',535,797,245,{kind:'elbow',from:'bottom',to:'left',color:C.muted});
notes('政策指定的是申请人当前所属部门的负责人。张三属于研发部，研发部负责人是李敏，因此本例应由李敏审批。王强是张三的直属主管，这是另一种关系。我们刚才把政策中的概念和关系，对应到了具体对象上。这个任务不要求证明语言模型一定会答错，而是帮助我们看清回答所依赖的业务含义。这些含义可以怎样明确记录，并被重复使用？');

// 03 — Definition before technologies.
base('本体：对领域语义的明确建模','把业务中默认理解的词语与联系，变成可以共同引用的定义','核心是明确业务含义，并表达当前用途需要的知识','本演示讨论知识工程中的本体（Ontology）。','01 / 认识本体');
text('本体是对一个领域中概念、关系\n及其语义约定的明确建模。',112,331,1696,160,54,C.ink,{serif:true,bold:true});
topic(112,558,500,'有哪些概念','员工、部门、差旅申请\n分别表示什么？');
topic(710,558,500,'怎样关联','申请人属于哪个部门？\n部门由谁负责？');
topic(1308,558,500,'哪些含义成立','经理是一类员工。\n审批政策适用于哪类申请？');
notes('知识工程中的本体，可以先理解为一份明确的领域语义模型。它说明业务里有哪些概念，这些概念是什么意思，对象怎样关联，以及哪些语义约定成立。例如，申请人与部门如何关联，经理和员工是什么分类关系。我们选择当前问题需要表达的知识，不需要把整个世界一次描述完整。接下来把现实中的业务、语义模型以及表达技术分开看。',[SOURCES.gruber]);

// 04 — The three-level anchor.
base('现实世界、本体、形式表达','分清我们要理解的对象、建立的模型，以及模型的表达方式','先明确表达什么含义，再选择合适的表达技术','','01 / 认识本体');
const cols=[112,710,1308];
const levels=[['现实世界','实际发生了什么？'],['本体','我们怎样理解这个领域？'],['形式表达','怎样明确表达这些含义？']];
levels.forEach((a,i)=>{rule(cols[i],335,500,i===1?C.green:C.edge,i===1?4:2);label(a[0],cols[i],365,500,C.ink,43);para(a[1],cols[i],437,500,28);});
box(112,527,500,280,'none',C.line,1.5);
label('张三',144,563,420,C.ink,37);para('属于研发部\n提交差旅申请 T-101',144,631,420,31);
box(710,527,500,280,C.soft);
label('员工 · 部门 · 申请',744,563,430,C.ink,35);para('概念、关系\n及其语义约定',744,631,430,31);
box(1308,527,500,280,'none',C.line,1.5);
label('RDF / OWL',1340,563,440,C.ink,40);para('或其他约定的\n表达方式',1340,631,430,31);
text('观察与抽象',490,849,400,45,25,C.muted,{align:'center'});
text('编码与表达',1080,849,400,45,25,C.muted,{align:'center'});
line(580,838,720,838);line(1180,838,1320,838);
notes('左边是现实业务：张三在一个部门工作，提交了一张申请。中间是我们对这些事情的理解：员工、部门、申请各是什么，它们如何关联。右边是用什么方式把含义记录下来。实际保存的本体产物当然有表达形式，但我们可以把语义选择和技术选择分别讨论。同一套业务理解可以通过不同方式表达。下面先认识本体的常见组成。',[SOURCES.gruber]);

// 05 — Editable schema/instance diagram plus a compact legend.
base('本体的常见组成','在同一张模型中认识类、属性、关系、公理与个体','按用途选取需要的内容，重点在于把领域语义说清楚','教学上分列属性与关系；OWL 中，对象关系通常也属于 Property。','01 / 认识本体');
const m5=node(200,361,240,85,'经理');
const e5=node(200,566,240,85,'员工');
const d5=node(710,566,260,85,'部门');
const z5=node(200,785,240,85,'张三','','dark');
const r5=node(710,785,260,85,'研发部','','dark');
edge(m5,e5,'是一种',222,486,195,{from:'bottom',to:'top',dashed:true});
edge(e5,d5,'隶属于',460,587,225);
edge(z5,e5,'属于这个类',204,705,235,{from:'top',to:'bottom',dashed:true});
edge(r5,d5,'属于这个类',722,705,235,{from:'top',to:'bottom',dashed:true});
edge(z5,r5,'隶属于',460,806,225);
text('员工的属性：姓名、入职时间',470,510,500,45,25,C.ochre,{align:'center'});
const legend=[['类 Class','员工、部门：概念及类别'],['属性 Property','姓名、入职时间：对象的特征'],['关系 Relation','隶属于：对象之间的联系'],['公理 Axiom','经理是一类员工：逻辑断言'],['个体 Individual','张三、研发部：具体对象']];
legend.forEach((a,i)=>{let y=337+i*111;rule(1110,y,698,i===0?C.edge:C.line,i===0?2:1);label(a[0],1110,y+18,698,C.green,28);text(a[1],1110,y+62,698,44,27,C.muted);});
notes('先看空心的概念：经理、员工和部门是类。姓名和入职时间描述对象的特征。隶属于说明两个对象之间的联系。经理是一类员工，是有逻辑含义的分类断言。底部实心的张三和研发部是具体对象。这里按教学目的把属性和关系分别列出，在 OWL 中，对象间的关系通常也属于属性。公理用于陈述知识，不是额外的一种业务对象。各项按用途选择，个体可以按需纳入。',[SOURCES.owl]);

// 06 — General definitions above, concrete facts below.
base('“员工”与“张三”处在不同层次','一般定义能够被许多具体对象重复使用','组织里的具体人员可以变化，概念和关系的含义仍可复用','个体可按需纳入；本体建设不要求复制全部业务数据。','01 / 认识本体');
label('一般定义',112,349,300,C.green,30);
label('具体事实',112,674,300,C.green,30);
rule(112,626,1696);
const e6=node(425,365,300,105,'员工');const d6=node(1050,365,300,105,'部门');
edge(e6,d6,'所属部门',760,395,255);
const z6=node(425,702,300,110,'张三','','dark');const r6=node(1050,702,300,110,'研发部','','dark');const l6=node(1585,702,223,110,'李敏','','soft',32);
edge(z6,r6,'所属部门',760,737,255);
edge(r6,l6,'负责人',1370,737,200);
edge(z6,e6,'属于员工',437,545,276,{from:'top',to:'bottom',dashed:true});
edge(r6,d6,'属于部门',1062,545,276,{from:'top',to:'bottom',dashed:true});
notes('员工是一种概念，张三是具体对象。部门是一种概念，研发部是具体对象。上面的定义告诉我们如何理解所属部门关系，下面的事实告诉我们这次关系连接着谁。即使负责人发生变化，上面的词汇与关系定义仍然可以继续使用。具体事实可以保存在知识系统中，也可以留在人事和差旅系统中，在使用时读取。这是定义与事实的作用区别，不是规定本体只能有类、知识图谱只能有实例。',[SOURCES.owl]);

// 07 — Technology comparison with the same business vocabulary.
base('RDF 与 OWL 分别做什么','RDF 是图数据模型，OWL 是具有形式语义的本体语言','这些技术帮助软件处理明确表达的知识','RDF/OWL 可以协同使用；并非两种互斥的文件格式。','02 / 表达与使用');
topic(112,337,790,'RDF：用图陈述知识','把对象及其关系写成可连接的陈述');
topic(1018,337,790,'OWL：表达形式语义','为类、关系及其组合明确逻辑含义');
const z7=node(112,573,240,100,'张三');const r7=node(662,573,240,100,'研发部');edge(z7,r7,'所属部门',375,604,264);
text('主体',112,703,240,45,24,C.muted,{align:'center'});text('关系',375,703,264,45,24,C.muted,{align:'center'});text('对象',662,703,240,45,24,C.muted,{align:'center'});
box(1018,563,790,143,C.soft);text('员工与部门是互斥的类别',1050,611,725,62,40,C.ink,{bold:true});
para('为一致性检查和逻辑推导提供依据',1018,758,790,29);
notes('RDF 用主体、谓词、对象这样的三元组来陈述知识，多个陈述通过共同对象连接成图。OWL 为本体表达提供形式定义的含义，可以描述类之间的互斥等关系。两者可以一起使用，也不是互斥的文件格式。RDF 既可用于事实，也可用于定义；RDFS 已提供一些基础分类词汇。我们先把这两个技术名词放在表达层，接着看看明确的逻辑含义能够带来什么。',[SOURCES.rdf,SOURCES.owl]);

// 08 — Deduction and inconsistency remain separate examples.
base('形式语义怎样支持推理与检查','根据已表达的知识，计算逻辑后果或发现矛盾','形式推理让一部分含义可以被明确检查和推导','自动推导需相应表达与推理工具；此页介绍通用技术能力。','02 / 表达与使用');
label('推导一个未直接写出的结论',112,342,930,C.green,31);
const given8=box(112,409,900,230,'none',C.edge);
text('经理是一类员工',153,451,818,62,39,C.ink,{bold:true});text('李敏是经理',153,545,818,62,39,C.ink,{bold:true});
const conclusion=node(112,756,900,125,'因此，李敏是员工','','dark',45);
edge(given8,conclusion,'推导',620,669,160,{from:'bottom',to:'top',color:C.green});
label('发现一个矛盾',1120,342,688,C.ochre,31);
rule(1120,409,688,C.ochre,2);
para('约定：员工与部门互斥',1120,449,688,33,C.ink);
para('假设误录：\n把张三同时标成员工和部门',1120,555,688,31);
box(1120,756,688,125,C.lightRed);
text('两项分类与互斥约定冲突',1150,796,628,62,35,C.red,{bold:true});
notes('经理属于员工，李敏属于经理，因此可以推出李敏也属于员工。这里是给定知识下的逻辑后果。右边是另外一个假设误录的例子：如果员工与部门已经声明为互斥，却把张三同时归到两个类别，就会产生矛盾。能够做什么检查和推导，取决于表达范围与所使用的推理工具。逻辑一致不自动证明外部数据真实，形式推理也与语言模型组织业务判断的过程有所不同。OntoWeave 当前不提供这里展示的 OWL 自动推理运行。',[SOURCES.owl,SOURCES.project]);

// 09 — One graph can contain semantic definitions and facts.
base('本体与知识图谱怎样配合','本体明确语义，知识图谱组织和连接知识','语义定义、知识组织和表达技术，各有自己的位置','知识图谱可包含本体定义，也可以采用不同的图技术。','02 / 表达与使用');
label('本体提供语义定义',112,342,1000,C.green,31);
const a9=node(112,416,310,100,'差旅申请');const e9=node(722,416,310,100,'员工');const d9=node(1332,416,476,100,'部门');
edge(a9,e9,'申请人',448,446,250);edge(e9,d9,'所属部门',1052,446,250);
rule(112,589,1696);
label('知识网络连接具体知识',112,621,1200,C.green,31);
const t9=node(112,720,280,100,'T-101','','soft');const z9=node(592,720,280,100,'张三','','dark');const r9=node(1072,720,280,100,'研发部','','dark');const l9=node(1552,720,256,100,'李敏','','soft');
edge(t9,z9,'申请人',410,750,165);edge(z9,r9,'所属部门',890,750,165);edge(r9,l9,'负责人',1370,750,165);
text('RDF / OWL 等技术可以参与表达这些知识',112,854,1696,45,27,C.muted);
notes('本体强调概念与关系的明确含义。知识图谱强调把有关对象的知识组织、连接起来，供查询和使用。一个知识图谱可以同时包含定义和具体事实，它也可以采用不同的图技术。RDF 和 OWL 则属于相关的表达技术。这里用同一幅图展示协作方式，避免把本体、知识图谱和某一种格式混为一谈。接下来，把这些知识放到 Agent 的工作过程中。',[SOURCES.kg,SOURCES.gruber,SOURCES.rdf]);

// 10 — Conceptual application architecture.
base('本体在 Agent 体系中的位置','Agent 结合领域语义、当前事实和工具能力处理业务','语言模型负责理解与组织判断，业务语义为任务提供明确依据','','02 / 表达与使用');
const request=node(690,331,540,90,'用户问题：该由谁审批？','','plain',30);
const agent=node(680,535,560,170,'Agent','语言模型理解请求、规划与解释','dark',46);
const ont=node(112,541,380,155,'语义模型','概念、关系与政策说明','soft',37);
const data=node(1430,430,378,135,'业务事实','当前申请人与组织关系','plain',34);
const tools=node(1430,737,378,135,'工具能力','查询、计算与获准操作','plain',34);
edge(request,agent,'',0,0,0,{from:'bottom',to:'top'});
edge(agent,ont,'查定义',507,579,158,{from:'left',to:'right',color:C.green});
edge(agent,data,'取事实',1253,465,165,{kind:'elbow'});
edge(agent,tools,'调用能力',1253,779,165,{kind:'elbow'});
notes('Agent 使用语言模型理解问题、组织计划和解释结果。语义模型提供组织特定的概念、关系和政策含义。业务系统提供当下的申请人与组织关系，工具则承担查询、计算或执行操作。这是一种概念分工，实际系统可以有不同实现。Agent 读取本体，不表示本体直接修改了语言模型参数。我们把这些分工放回刚才的审批任务，完整走一遍。');

// 11 — Four steps, actual provenance, no fake execution receipts.
base('Agent 如何找到审批人','把明确的业务含义与本次事实结合起来','按本例政策，应由研发部负责人李敏审批','教学推演，未调用真实业务系统。','02 / 表达与使用');
label('01 取得语义',112,332,500,C.green,29);
box(112,389,1696,92,C.soft);
text('此类差旅由申请人当前所属部门的负责人审批',145,413,1627,58,35,C.ink,{bold:true});
label('02 查询事实',112,522,500,C.green,29);
const t11=node(112,591,280,93,'T-101');const z11=node(592,591,280,93,'张三');const r11=node(1072,591,280,93,'研发部');const l11=node(1552,591,256,93,'李敏','','dark');
edge(t11,z11,'申请人',410,617,165);edge(z11,r11,'所属部门',890,617,165);edge(r11,l11,'负责人',1370,617,165);
text('差旅系统',112,703,760,40,23,C.muted,{align:'center'});text('人事系统',1072,703,736,40,23,C.muted,{align:'center'});
rule(112,764,1696);
label('03 结合政策判断',112,795,690,C.green,28);
para('选择“所属部门负责人”这条路径',112,846,770,29,C.ink);
label('04 给出答案与依据',1018,795,790,C.green,28);
para('张三属于研发部，李敏担任该部门负责人',1018,846,790,29,C.ink);
notes('第一步，取得适用政策以及申请人、所属部门、负责人这些定义。第二步，从差旅系统取得申请人张三，从人事系统取得研发部与李敏的事实。第三步，结合政策选用所属部门负责人这条路径。第四步，明确回答李敏，并解释每一个依据。直属主管王强对应另一种关系。若负责人事实缺失，Agent 应指出未知并补充查询或询问。若用户还要求提交申请，再按授权调用业务系统，以实际回执确认结果。');

// 12 — Three complementary inputs, not a straw-man comparison.
base('资料检索、本体与工具怎样配合','同一个业务问题，可以同时使用不同来源的帮助','明确的语义可以与资料检索、业务数据和工具一起使用','这些能力可以重叠组合，本体内容也可以成为检索对象。','02 / 表达与使用');
topic(112,339,500,'资料检索','找到相关材料与上下文','01');
topic(710,339,500,'本体与语义检索','取得明确的定义与关联','02');
topic(1308,339,500,'工具与业务系统','读取事实，完成获准操作','03');
para('找到差旅制度中的\n审批条款',112,647,500,33,C.ink);
para('理解“所属部门负责人”\n对应的业务路径',710,647,500,33,C.ink);
para('查询当前负责人\n按授权提交差旅申请',1308,647,500,33,C.ink);
rule(112,798,1696);
text('共同支持 Agent 对同一个业务问题的判断',112,843,1696,58,36,C.green,{align:'center',bold:true});
notes('资料检索帮助找到相关制度与背景。本体和语义检索提供明确整理的概念、关系与适用说明。工具和业务系统提供具体事实与操作能力。这些能力可以组合，边界也可能重叠，比如本体内容本身可以被检索，工具也可以封装业务规则。这里的分工是为了理解它们在任务中提供的帮助，不是把 RAG 简化成关键词匹配，也不是说每一个任务都必须使用本体。');

// 13 — Reuse by different business agents.
base('多个 Agent 可以引用同一套定义','共同使用业务含义，各自完成不同任务','共享语义的价值，会在跨任务和跨系统的复用中体现','各 Agent 按自身权限与适用范围读取知识。','02 / 表达与使用');
const shared=node(570,340,780,165,'共同的领域语义','员工、所属部门、部门负责人','soft',42);
const a13=node(112,677,480,145,'差旅助手','找到这张申请的审批人');
const b13=node(720,677,480,145,'报表助手','按申请人所属部门统计申请数');
const c13=node(1328,677,480,145,'组织助手','查询研发部负责人');
// Explicit shared bus keeps its orthogonal route stable across PPTX renderers.
line(352,555,1568,555,C.edge,2.5);
for(const x of [352,960,1568]){
  line(x,677,x,555,C.edge,2.5);
  text('引用定义',x-125,590,250,40,25,C.muted,{align:'center',fill:C.paper});
}
const bus13=box(959,554,2,2,'none','none');
edge(bus13,shared,'',0,0,0,{from:'top',to:'bottom'});
notes('差旅助手、报表助手和组织助手的问题不同，但都可以使用员工、所属部门和部门负责人的共同定义。每个 Agent 仍保留自己的任务、事实来源和工具。共享定义有助于让业务含义被统一澄清和维护，也方便发现同一个词在不同任务中是否被误用。共享不意味着越过各自权限。要建立这样的共同知识，需要从实际问题出发进行建设。');

// 14 — Five modest engineering steps.
base('一个有用的本体怎样建立','从实际问题开始，回到实际问题验证','Agent 可以协助整理与检查，业务含义仍需资料和领域人员确认','','03 / 建设与平台');
const steps=[['确定范围','要回答什么','这张差旅申请\n由谁审批？'],['澄清含义','确认业务口径','部门负责人，\n还是直属主管？'],['建立模型','明确概念与关联','员工、部门、申请\n及审批政策'],['连接来源','找到所需事实','差旅系统查申请人\n人事系统查组织关系'],['问题验证','核对回答与依据','正常情况能解释\n事实缺失能指出未知']];
steps.forEach((a,i)=>{let x=112+i*350;rule(x,345,296,C.edge,2);text(String(i+1).padStart(2,'0'),x,375,296,73,52,C.edge,{serif:true});label(a[0],x,477,296,C.ink,37);text(a[1],x,548,296,46,27,C.green);para(a[2],x,637,306,28);if(i<4)text('›',x+308,485,35,55,39,C.edge);});
box(112,798,1696,93,C.soft);text('用业务问题检查：定义是否清楚，关系是否完整，未知是否保留',145,823,1629,50,31,C.green);
notes('先确定要回答的问题，控制范围。再与资料和业务人员一起确认含义，例如这里的负责人到底是哪种角色。随后建立概念、关系和政策说明，并指出事实来自哪个系统。最后用实际业务问题验证：正常情况下能否解释，必要信息缺失时能否如实指出未知。审批政策可以表达成有明确关联的业务说明，是否进一步编码成可执行逻辑，取决于实际用途。生产者自查与独立业务验证承担不同职责。');

// 15 — Adoption needs and real effort.
base('什么时候值得建立本体','把共享和复用的需要，与建设和维护的投入放在一起考虑','从一组真实、反复出现的业务问题开始','','03 / 建设与平台');
label('更值得考虑的情况',112,344,1000,C.green,33);
const need=[['多个任务','反复使用同一套概念与定义'],['跨对象、跨系统','答案依赖明确的业务关系'],['长期维护','业务含义需要持续更新和复用']];
need.forEach((a,i)=>{let y=428+i*143;rule(112,y,1020,i===0?C.edge:C.line,i===0?2:1.5);label(a[0],112,y+27,330,C.ink,32);text(a[1],455,y+30,677,50,29,C.muted);});
rule(1240,344,568,C.ochre,2);label('相应投入',1240,375,568,C.ochre,33);para('澄清业务含义\n连接事实来源\n验证与持续维护',1240,473,568,35,C.ink);
para('问题少、变化少时，\n可以先采用轻量的组织方式。',1240,743,568,28);
notes('本体的价值通常来自业务知识的共享、关系的明确表达以及跨任务复用。如果多个系统和 Agent 反复使用相同的概念，投入可能更有意义。与此同时，模型需要业务澄清、来源连接、验证和维护，这些工作并不会自动消失。对于问题少、变化少且现有文档和工具已经足够的场景，可以先采用更轻量的方式。当共享需求增长，我们需要一个支持这些工作的语义平台。');

// 16 — Platform positioning, deliberately simpler than the legacy architecture.
base('OntoWeave：面向 Agent 的业务语义平台','连接构建领域语义的人与 Agent，以及使用语义的业务 Agent','平台承接语义模型的保存、维护、校验与读取','平台定位示意；业务数据查询与动作执行由外部能力承担。','03 / 建设与平台');
const build16=node(112,523,395,162,'业务人员与建模 Agent','理解资料，确认业务含义','plain',31);
const center16=box(715,389,545,431,C.soft);
text('OntoWeave',750,425,475,80,53,C.ink,{bold:true,serif:true,align:'center'});
rule(757,526,461,C.edge,2);
text('保存概念与关系',750,566,475,55,32,C.ink,{align:'center'});
text('支持模型维护与检查',750,644,475,55,32,C.ink,{align:'center'});
text('按权限提供相关语义',750,722,475,55,32,C.ink,{align:'center'});
const consume16=node(1467,431,341,144,'业务 Agent','结合语义处理任务','plain',34);
const external16=node(1467,721,341,144,'外部业务系统','提供数据与执行能力','plain',32);
edge(build16,center16,'构建与维护',521,551,180);
edge(center16,consume16,'语义读取',1275,458,177,{kind:'elbow'});
edge(consume16,external16,'查询与执行',1508,629,260,{from:'bottom',to:'top'});
notes('OntoWeave 是面向 Agent 的业务语义平台。外部建模 Agent 与业务人员理解资料、确认含义，平台保存模型，提供确定性校验与受治理读取。业务 Agent 从平台取得相关知识，再通过外部系统查询事实和执行获准操作。这里的模型检查与维护，不表示平台当前提供 OWL 自动推理或业务流程执行引擎。我们用这张简化的图介绍产品职责，接下来看看建设与使用如何衔接。',[SOURCES.project]);

// 17 — Build/read loop, with a tangible semantic context sample.
base('在 OntoWeave 中构建与使用语义','构建时整理含义，使用时取得与任务相关的知识','平台提供相关语义，Agent 再结合当前事实与工具完成任务','流程与读取内容为教学示意，非真实运行回执。','03 / 建设与平台');
label('构建时',112,336,330,C.green,30);
const doc17=node(112,420,300,104,'制度与访谈','','plain',31);const model17=node(580,420,300,104,'建模 Agent','','plain',31);const onto17=node(1048,420,380,104,'平台中的领域语义','','soft',31);const verify17=node(1580,420,228,104,'业务验证','','plain',31);
edge(doc17,model17,'澄清与整理',428,452,136,{size:22});edge(model17,onto17,'提交模型',896,452,136,{size:22});edge(onto17,verify17,'读取核对',1443,452,121,{size:22});
rule(112,588,1696);
label('使用时',112,627,330,C.green,30);
const question17=node(112,721,300,104,'谁来审批？','','plain',31);const agent17=node(580,721,300,104,'业务 Agent','','dark',31);
edge(question17,agent17,'理解任务',428,753,136,{size:22});
box(1048,663,760,218,C.soft);
label('本次读取的相关语义',1080,684,690,C.green,29);
text('审批政策    所属部门关系\n负责人含义    人事信息来源',1080,745,690,110,32,C.ink);
edge(agent17,onto17,'语义检索',852,610,190,{kind:'elbow',from:'top',to:'bottom',color:C.green});
text('再查询事实、解释答案或执行获准操作',112,858,900,43,27,C.muted);
notes('构建时，从制度与访谈形成输入，建模 Agent 整理概念、关系与政策说明，提交到平台，再通过业务问题读取与验证。使用时，业务 Agent 围绕当前问题读取相关语义。它得到的可以是审批政策、所属部门关系、负责人含义和人事信息来源，而具体谁担任负责人仍从业务系统读取。这里的四行内容是帮助理解读取结果的教学示意，不是实际接口 JSON 或运行回执。当前模型提交和读回按 R4.3-024/025 路径，真实业务语义效果需要相应验证。',[SOURCES.project]);

// 18 — Return to the original mental model.
base('让 Agent 有明确的业务语义可用','从一张差旅申请，回到我们对本体的理解','OntoWeave 支持这份领域知识的构建、维护与使用','','本体与 Agent');
topic(112,340,500,'现实世界','我们要描述和理解的对象');
topic(710,340,500,'本体','对领域语义的明确建模');
topic(1308,340,500,'RDF / OWL 等','表达这些知识的相关技术');
rule(112,566,1696);
text('Agent 结合语义、当前事实与工具，完成业务任务。',112,613,1696,80,45,C.ink,{bold:true,serif:true});
const z18=node(112,777,305,104,'张三');const d18=node(742,777,305,104,'研发部');const l18=node(1368,777,440,104,'李敏审批','','dark');
edge(z18,d18,'所属部门',450,809,255);edge(d18,l18,'按本例政策，找负责人',1075,809,267,{size:23,color:C.green});
notes('回到三个层次：现实世界是我们要描述和理解的对象，本体是对领域语义的明确建模，RDF、OWL 等技术帮助表达这些知识。Agent 结合语义、当下事实与工具，找到应由李敏审批的依据。我们把业务含义明确表达出来，Agent 就有了一份可以查询、共享和核对的领域知识。OntoWeave 支持的是这份知识的构建、维护与使用。',[SOURCES.gruber,SOURCES.rdf,SOURCES.owl]);

if(slides.length!==18)throw new Error(`Expected 18 slides, got ${slides.length}`);
await fs.mkdir(BUILD,{recursive:true});
await fs.mkdir(path.join(BUILD,'previews'),{recursive:true});
const draft=path.join(BUILD,'candidate.pptx');
await (await PresentationFile.exportPptx(P)).save(draft);
await fs.writeFile(path.join(BUILD,'slides.json'),JSON.stringify(slides,null,2));
await fs.writeFile(path.join(BUILD,'font-policy.json'),JSON.stringify({basis:'reference',families:[SANS,SERIF],referencePath:path.join(ROOT,'deck/editorial.pdf')},null,2));
await fs.writeFile(path.join(HERE,'speaker-notes.md'),'# 本体与 Agent：v3.0 讲者备注\n\n'+slides.map(d=>`## P${String(d.number).padStart(2,'0')} ${d.title||'本体与 Agent'}\n\n${d.notes}\n${d.sources.length?'\n参考资料：\n\n'+d.sources.map(s=>'- '+s).join('\n')+'\n':''}`).join('\n'));
for(let i=0;i<P.slides.items.length;i++){
  const s=P.slides.items[i];
  const img=await P.export({slide:s,format:'png',scale:0.8});
  await fs.writeFile(path.join(BUILD,'previews',`${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await img.arrayBuffer()));
  const layout=await s.export({format:'layout'});
  await fs.writeFile(path.join(BUILD,`slide-${i+1}.layout.json`),await layout.text());
  console.log(`Rendered ${i+1}/18`);
}
console.log(`Candidate written: ${draft}`);
