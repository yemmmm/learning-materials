# 本体与 Agent · v3.3 讲者备注

## P01 本体与 Agent

先让听众看到具体申请，再提出王强与李敏的区别。今天不会从一串技术缩写开始，而是逐步说明业务含义如何成为可重复使用的知识。全篇保留同一个例子。



## P02 张三的差旅申请，该由谁审批？

先说明所有事实都可能是真实的，区别在于本次问题需要哪条关系。点击对照可以看到同样的组织事实在另一条政策下得到王强。切回本例再继续。这里不声称语言模型必然答错。



## P03 本体：对领域语义的明确建模

定义是面向入门听众的概括。强调范围选择：本体不需要穷尽世界，重点是把当前任务依赖的概念和关联说清楚。下一页把被描述的现实、语义选择和表达技术分开。

- [本体定义 · Tom Gruber](https://tomgruber.org/writing/definition-of-ontology/)

## P04 现实世界、本体、形式表达

从左到右走同一个例子。左边是业务现实，中间是对业务的选择性理解，右边是编码。不同表达形式可以承载同样的业务定义；同一种技术也可以表达不同领域。

- [本体定义 · Tom Gruber](https://tomgruber.org/writing/definition-of-ontology/)
- [RDF 1.1 Primer · W3C](https://www.w3.org/TR/rdf11-primer/)
- [OWL 2 Primer · W3C](https://www.w3.org/TR/owl2-primer/)

## P05 本体的常见组成

逐项高亮，解释类别、属性、联系、分类断言和具体对象。不要把公理讲成业务对象。经理属于员工是子类关系，张三属于员工是个体的类别归属。

- [OWL 2 Primer · W3C](https://www.w3.org/TR/owl2-primer/)

## P06 “员工”与“张三”处在不同层次

强调类与个体并非两个独立现实。组织变化不必改变全部概念定义。使用当前政策时，需要查当前事实；若业务要求历史时点，必须另行明确时间口径。继续时后续页面仍以原始李敏事实为例。

- [OWL 2 Primer · W3C](https://www.w3.org/TR/owl2-primer/)

## P07 RDF 与 OWL 分别做什么

RDF 使用三元组，屏幕上的短例子避免语法展开。OWL 用两个声明展示分类和互斥，下一页看它们如何支持推导与检查。RDF 和 OWL 并非互斥文件格式。

- [RDF 1.1 Primer · W3C](https://www.w3.org/TR/rdf11-primer/)
- [OWL 2 Primer · W3C](https://www.w3.org/TR/owl2-primer/)

## P08 形式语义怎样支持推理与检查

点击运行只演示给定例子的逻辑后果，不调用推理器。右边加入误录展示不一致；删去它后只说明这个特定冲突消失，不证明整个知识库完美或外部事实真实。

- [OWL 2 Primer · W3C](https://www.w3.org/TR/owl2-primer/)
- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P09 相关技术速览：词表、规则、服务与查询

这一页只作技术地图，建议用一分钟带过，不讲语法。SKOS 是基于 RDF 的知识组织词汇，可表示概念标签和上下位关联；这里的词表是教学设定，SKOS 的上下位关系不直接等于 OWL 的子类公理。SWRL 将规则与 OWL 结合，执行需要支持它的推理工具，不能把所有业务规则都当成能直接写成 SWRL。OWL-S 是基于 OWL 的服务描述本体，涉及服务能力、过程及调用映射，并非 OWL 的版本或直接执行服务的引擎。SPARQL 是 RDF 图查询的相关语言和协议，也包含更新等能力，本页只介绍查询；例子以图中存在相应事实或可查询视图为前提，不要求把业务系统所有数据搬入本体。SWRL 和 OWL-S 是 W3C Member Submission，不是 W3C Recommendation。四项分别解决不同问题，不构成必须依次采用的技术栈，也不声明平台已经具备相应功能。

- [SKOS Primer · W3C](https://www.w3.org/TR/skos-primer/)
- [SWRL · W3C Member Submission](https://www.w3.org/submissions/SWRL/)
- [OWL-S · W3C Member Submission](https://www.w3.org/submissions/OWL-S/)
- [SPARQL 1.1 Overview · W3C](https://www.w3.org/TR/sparql11-overview/)

## P10 本体与知识图谱怎样配合

图谱不是只能放实例，本体也并非只能放类。这里上下布局解释作用，不要求产品采用两个独立存储层。接下来回答一个自然的问题：明确写出的本体知识，与大模型学到的知识，是什么关系？

- [Knowledge Graphs · Hogan 等](https://arxiv.org/abs/2003.02320)
- [RDF 1.1 Primer · W3C](https://www.w3.org/TR/rdf11-primer/)
- [本体定义 · Tom Gruber](https://tomgruber.org/writing/definition-of-ontology/)

## P11 AI 的两条路线：符号主义与联结主义

从前面已经介绍的经理属于员工入手，说明符号具有可指定的含义。再解释神经网络：大量计算单元通过带权连接组成网络，训练调整参数以学习模式。知识通常分布在参数中，不是一条连接对应一条可读业务规则。联结主义与神经网络不是先后独立的两个阶段；用神经网络、深度学习和大语言模型说明这条路线的持续发展。这里按知识表示方式将知识工程本体放在符号主义一侧；本体也可以借助神经网络辅助构建。

- [本体定义 · Tom Gruber](https://tomgruber.org/writing/definition-of-ontology/)
- [MYCIN 原著 · 系统结构与规则推理](https://people.dbmi.columbia.edu/~ehs7001/Buchanan-Shortliffe-1984/Chapter-04.pdf)
- [Deep Learning · LeCun、Bengio、Hinton](https://www.nature.com/articles/nature14539)
- [Attention Is All You Need · Vaswani 等](https://arxiv.org/abs/1706.03762)

## P12 专家系统：把领域经验写成可用的规则

专家系统不是泛指很聪明的软件，而是围绕特定领域显式组织专业知识并据此求解的系统。典型规则系统可以区分知识库、推理机制与解释界面；实际系统结构并不都相同。MYCIN 原著显示它还包括知识获取、解释与不确定性处理，不要把所有符号系统说成只能处理确定的二值事实。回到差旅例子：规则使用部门负责人这个关系，本体帮助把它与直属主管区分；执行这条规则仍需要推理或业务程序。

- [MYCIN 原著 · 系统结构与规则推理](https://people.dbmi.columbia.edu/~ehs7001/Buchanan-Shortliffe-1984/Chapter-04.pdf)
- [本体定义 · Tom Gruber](https://tomgruber.org/writing/definition-of-ontology/)

## P13 两条路线，各有擅长与代价

不要把对比讲成符号系统不会学习或神经网络不会推理。这里强调表达方式、典型强项与代价。符号推理的可检查性依赖明确的表达和执行机制，也不保证前提符合现实。语言模型生成一段看似合理的解释，不等于该解释忠实反映了内部计算。外部语义上下文可以更新业务口径而不必每次重训，但读取正确也不保证模型使用正确。

- [MYCIN 原著 · 系统结构与规则推理](https://people.dbmi.columbia.edu/~ehs7001/Buchanan-Shortliffe-1984/Chapter-04.pdf)
- [Deep Learning · LeCun、Bengio、Hinton](https://www.nature.com/articles/nature14539)
- [Neurosymbolic AI — Why, What, and How · Sheth 等](https://arxiv.org/abs/2305.00813)

## P14 让学习能力与明确知识在 Agent 中配合

神经符号 AI 包含多种结合方式，本页展示最容易理解的工程协作方式，不宣称该项目实现了特定研究架构。读取本体和生成回答本身不是形式逻辑保证。若任务需要严格规则执行，应有相应外部业务程序、规则或推理工具负责，并核对其结果。构建阶段也能互补：模型减轻资料整理工作，但候选知识仍要有来源与业务确认。随后继续讲 Agent 的具体结构与查询步骤。

- [Neurosymbolic AI — Why, What, and How · Sheth 等](https://arxiv.org/abs/2305.00813)
- [神经符号 AI · IBM Research](https://research.ibm.com/topics/neuro-symbolic-ai)
- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P15 本体在 Agent 体系中的位置

承接两条 AI 路线：本体承载显式业务语义，语言模型主要从神经网络训练中获得理解和生成能力。读取本体不等于修改语言模型参数。平台可以提供定义和关联，具体查询和操作由工具完成。这里只展示协同职责，不用工具数量证明质量。



## P16 Agent 如何找到审批人

四步始终可见，点击或方向键只改变重点。讲完正常路径后勾选缺失事实，显示无法确定审批人的回答。不要把关系遍历本身称为 OWL 自动推理。



## P17 资料检索、本体与工具怎样配合

避免把 RAG 简化成关键词搜索，也不要宣称所有任务都必须使用本体。这张图解释当前案例中的协作价值。图里的业务工具均为教学示意。



## P18 多个 Agent 可以引用同一套定义

三个助手的任务不同，不要求三个助手读入全部知识。报表的历史时点与统计口径需按任务确认，不能因为复用所属部门就把所有口径都当作相同。



## P19 一个有用的本体怎样建立

讲建设过程时不要扩张成复杂的方法论清单。五步可以往返，验证失败可能需要回到业务澄清。Agent 负责协助推理和整理，业务定义仍需源材料与领域确认。



## P20 什么时候值得建立本体

不提供虚构 ROI，也不将本体描述为所有 Agent 的必需品。第二个场景强调共享定义的积累价值，但前提仍是有可验证的问题和维护责任。



## P21 OntoWeave：面向 Agent 的业务语义平台

这页介绍产品定位，不展示未经验证的成功率。当前模型提交与确定性应用按 R4.3-024/025，当前能力边界参考 R4.0-025。业务数据查询和动作执行仍由外部系统承担。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P22 在界面中查看 OntoWeave 的模型

展示用户提供的真实截图。只描述图片中可见的控件、说明和计数，不从节点多、连线多推导模型质量。七视角是 OntoWeave 的组织方式。界面并非贯穿案例的实际运行证据。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P23 在 OntoWeave 中构建与使用语义

把相关语义讲成有具体内容的业务知识，不停留在抽象检索框。使用者不必读取全部本体。模型构建与真实语义检索效果需要独立证据，这页没有虚构实际运行。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P24 让 Agent 有明确的业务语义可用

收束时回到开场问题。串起三个层次、两条 AI 路线和一条业务判断路径：现实是业务对象，本体明确语义，RDF/OWL 等提供表达方式；语言模型理解问题，本体提供明确含义，工具读取当前事实。可以请观众复述为何不沿直属主管这条关系找审批人。

- [本体定义 · Tom Gruber](https://tomgruber.org/writing/definition-of-ontology/)
- [RDF 1.1 Primer · W3C](https://www.w3.org/TR/rdf11-primer/)
- [OWL 2 Primer · W3C](https://www.w3.org/TR/owl2-primer/)
- [Neurosymbolic AI — Why, What, and How · Sheth 等](https://arxiv.org/abs/2305.00813)

## P25 FAQ：什么时候值得使用本体

恢复此前版本的五项选型 FAQ。收益比较应共用资料、业务澄清、语言模型、题目、数据与工具条件，不承诺使用本体必然优于已有方案。

- [OWL 2 Primer · W3C](https://www.w3.org/TR/owl2-primer/)
- [Knowledge Graphs · Hogan 等](https://arxiv.org/abs/2003.02320)

## P26 FAQ：怎么建，哪些工作需要人参与

恢复此前版本的四项建设 FAQ。把七视角与第五页的常见组成区分：前者是业务知识的观察方式，后者是本体模型中的表达角色。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P27 FAQ：怎样保证质量并持续维护

恢复四项质量 FAQ，并将旧版退款权限问题推广到业务操作，保留退款例子。维护示例是独立假设，要确认生效时点、适用范围与旧申请解释方式，不能把知识更新等同于业务系统已更新。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)
