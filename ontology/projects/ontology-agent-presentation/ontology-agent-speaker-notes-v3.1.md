# 本体与 Agent · v3.1 讲者备注

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

## P09 本体与知识图谱怎样配合

图谱不是只能放实例，本体也并非只能放类。这里上下布局解释作用，不要求产品采用两个独立存储层。下面让 Agent 把这些知识用于一个具体任务。

- [Knowledge Graphs · Hogan 等](https://arxiv.org/abs/2003.02320)
- [RDF 1.1 Primer · W3C](https://www.w3.org/TR/rdf11-primer/)
- [本体定义 · Tom Gruber](https://tomgruber.org/writing/definition-of-ontology/)

## P10 本体在 Agent 体系中的位置

本体是 Agent 可访问的一种知识来源，读取本体不等于修改语言模型参数。平台可以提供定义和关联，具体查询和操作由工具完成。这里只展示协同职责，不用工具数量证明质量。



## P11 Agent 如何找到审批人

四步始终可见，点击或方向键只改变重点。讲完正常路径后勾选缺失事实，显示无法确定审批人的回答。不要把关系遍历本身称为 OWL 自动推理。



## P12 资料检索、本体与工具怎样配合

避免把 RAG 简化成关键词搜索，也不要宣称所有任务都必须使用本体。这张图解释当前案例中的协作价值。图里的业务工具均为教学示意。



## P13 多个 Agent 可以引用同一套定义

三个助手的任务不同，不要求三个助手读入全部知识。报表的历史时点与统计口径需按任务确认，不能因为复用所属部门就把所有口径都当作相同。



## P14 一个有用的本体怎样建立

讲建设过程时不要扩张成复杂的方法论清单。五步可以往返，验证失败可能需要回到业务澄清。Agent 负责协助推理和整理，业务定义仍需源材料与领域确认。



## P15 什么时候值得建立本体

不提供虚构 ROI，也不将本体描述为所有 Agent 的必需品。第二个场景强调共享定义的积累价值，但前提仍是有可验证的问题和维护责任。



## P16 OntoWeave：面向 Agent 的业务语义平台

这页介绍产品定位，不展示未经验证的成功率。当前模型提交与确定性应用按 R4.3-024/025，当前能力边界参考 R4.0-025。业务数据查询和动作执行仍由外部系统承担。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P17 在界面中查看 OntoWeave 的模型

展示用户提供的真实截图。只描述图片中可见的控件、说明和计数，不从节点多、连线多推导模型质量。七视角是 OntoWeave 的组织方式。界面并非贯穿案例的实际运行证据。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P18 在 OntoWeave 中构建与使用语义

把相关语义讲成有具体内容的业务知识，不停留在抽象检索框。使用者不必读取全部本体。模型构建与真实语义检索效果需要独立证据，这页没有虚构实际运行。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P19 让 Agent 有明确的业务语义可用

收束时回到开场问题。强调大家记住的是三个层次与语义、事实、工具的协同，而不是必须选某一种格式。可以请观众复述为何不沿直属主管这条关系找审批人。

- [本体定义 · Tom Gruber](https://tomgruber.org/writing/definition-of-ontology/)
- [RDF 1.1 Primer · W3C](https://www.w3.org/TR/rdf11-primer/)
- [OWL 2 Primer · W3C](https://www.w3.org/TR/owl2-primer/)

## P20 FAQ：什么时候值得使用本体

恢复此前版本的五项选型 FAQ。收益比较应共用资料、业务澄清、语言模型、题目、数据与工具条件，不承诺使用本体必然优于已有方案。

- [OWL 2 Primer · W3C](https://www.w3.org/TR/owl2-primer/)
- [Knowledge Graphs · Hogan 等](https://arxiv.org/abs/2003.02320)

## P21 FAQ：怎么建，哪些工作需要人参与

恢复此前版本的四项建设 FAQ。把七视角与第五页的常见组成区分：前者是业务知识的观察方式，后者是本体模型中的表达角色。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)

## P22 FAQ：怎样保证质量并持续维护

恢复四项质量 FAQ，并将旧版退款权限问题推广到业务操作，保留退款例子。维护示例是独立假设，要确认生效时点、适用范围与旧申请解释方式，不能把知识更新等同于业务系统已更新。

- [OntoWeave · 项目与版本需求](https://github.com/yemmmm/ontology-platform)
