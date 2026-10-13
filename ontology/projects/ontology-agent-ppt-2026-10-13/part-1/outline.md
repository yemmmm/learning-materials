# Slide Deck Outline

**Topic**: 本体论如何帮助 Agent 理解与处理业务 · 第一部分
**Style**: 简约手绘业务讲解，元素略丰富
**Audience**: 业务、产品与技术混合受众
**Language**: zh-CN
**Slide Count**: 4（草稿第 1—4 页）
**Generated**: 2026-10-13

<STYLE_INSTRUCTIONS>
Design Aesthetic: A professional, approachable hand-drawn editorial deck for adult business, product, and technical audiences. Keep the visual language of the reference slide, but make the composition slightly richer with purposeful small illustrations, source-document drawings, and tools. All new details must explain the topic rather than fill empty space.

Background:
  Texture: Almost imperceptible fine paper grain, no notebook lines or grid.
  Base Color: Warm ivory (#FAF8F2).

Typography:
  Headlines: Large dark simplified Chinese, neatly hand-lettered, sober brush-marker character, steady baseline, immediately readable.
  Body: Clear simplified Chinese with subtle hard-pen handwriting, consistent sizing and spacing, no rushed cursive. Latin terms must be crisp and upright.

Color Palette:
  Primary Text: Charcoal (#29383C).
  Background: Warm ivory (#FAF8F2).
  Accent 1: Muted slate blue (#728E9A), very pale fills on diagrams and useful illustrations.
  Accent 2: Soft ochre (#D8B56C), selective emphasis, underlines, paper and equipment accents.
  Secondary Text: Warm gray (#66716F).

Visual Elements:
  - Small hand-drawn objects related to industrial service: pump, clipboard, contract, manual, database cylinder, API window, and clock.
  - Thin slightly irregular ink lines and precise labeled connections.
  - Pale translucent color washes, restrained tiny motion marks where useful.
  - No unrelated stars or doodles; no photographic, 3D, or corporate vector stock art.

Density Guidelines:
  - Balanced information density, slightly richer than the five-node reference sample.
  - One cohesive composition per slide, clear title, no UI card grid.
  - Preserve roughly 25–35 percent breathing space; the cover should feel more open.
  - Keep diagram labels and table text highly readable. Do not shrink copy to fit.

Style Rules:
  Do: Follow the source, draw objects that clarify the text, use each slide's unique arrangement, label feedback direction, retain teaching qualifiers.
  Don't: Add slide numbers, logos, running headers, decorative footers, badges, UI controls, cartoons with exaggerated faces, heavy shadows, gradients, invented statistics, product screenshots, or ranking symbols.
</STYLE_INSTRUCTIONS>

## Slide 1 of 4

**Type**: Cover
**Title**: 本体论如何帮助 Agent 理解与处理业务
**Filename**: 01-slide-cover.png
**Layout**: title-hero

// NARRATIVE GOAL
以工业服务的具体形象打开主题，保持封面简洁，同时比前次纯概念样张稍丰富。

// VISUAL AND KEY CONTENT
Create the COVER slide. Left 60%: the large two-line title, then subtitle and case line. Right 35%: a single elegant hand-drawn vignette of industrial service, comprising a small pump or industrial equipment, an adult service engineer with a clipboard, and a contract sheet. A faint, sparse three-node concept map sits behind the vignette, nodes labeled 工单, 设备, 合同. Its connections are merely a low-contrast conceptual backdrop; no dense technical labels or arrows. Human proportions and poses should be calm, simple, editorial, not a cute mascot. Use only pale gray-blue and ochre washes. Avoid a boxed illustration or panel. The title remains dominant, with abundant breathing room.
EXACT TEXT:
Title line 1: 本体论如何帮助 Agent
Title line 2: 理解与处理业务
Subtitle: 以 Ontology Platform 项目为例
Case line: 贯穿案例：工业设备售后服务
Only three small background node labels: 工单, 设备, 合同
No extra text, section label, page number, date, logo, success claims, or decorative slogan.

// SPEAKER NOTES
今天关注 Agent 如何获得业务依据。先认识 Agent 与本体，再看项目如何把业务知识组织起来，最后用一张服务工单说明实际应用路径。

## Slide 2 of 4

**Type**: Content
**Title**: Agent 怎样完成一个任务
**Filename**: 02-slide-agent-task-loop.png
**Layout**: circular-flow

// NARRATIVE GOAL
说明 Agent 的目标、模型、工具、上下文与反馈，用清楚的往返连接展示任务处理。

// VISUAL AND KEY CONTENT
Create a cohesive illustrated WORKFLOW slide. Title across the top, then one smaller explanatory line. Main diagram: on the left a user's request drawn as a speech bubble; in the middle a large Agent represented by a simple thoughtful assistant at a laptop, with an unobtrusive small reasoning/gear motif; on the right a compact group of THREE tool illustrations, not a UI grid. Above the Agent, draw a small open folio or a few paper sheets indicating context. In the lower-left, draw an answer sheet. Use clearly separated arrows: the request points to Agent; the upper horizontal arrow goes from Agent to tools and is labeled 调用工具; a distinct lower return arrow goes from tools back to Agent and is labeled 返回结果; Agent points down-left to the answer sheet. Never put both arrowheads on the same line. Feedback is a central explanatory relationship, not just decoration. Do not add further unlabeled loops. Context and output must remain visually separate.
EXACT TEXT:
Title: Agent 怎样完成一个任务
Explanatory line: 围绕目标使用工具，并根据结果继续工作
Request heading: 用户请求
Request text, may wrap to two lines: 帮我分析服务工单的处理情况。
Central heading: Agent
Central caption: 大语言模型
Central explanation, may wrap to two lines: 理解请求、分析信息、组织回答
Above-center heading: 上下文
Above-center caption: 要求、知识和结果
Right group heading: 工具
Three separate tool labels: 查询数据库 / 读取资料 / 调用业务接口
Upper outgoing connector: 调用工具
Lower incoming connector: 返回结果
Answer heading: 回答
Answer caption: 组织处理结果
Lower content takeaway: 反馈帮助 Agent 决定下一步
Small qualifier near the diagram: 任务示意
Slashes between the three tool labels are instructions for separate labels, not printed slash marks. Keep all characters and labels readable, no fake database rows, numerical results, success checkmarks, or chat-app interface.

// SPEAKER NOTES
可把 Agent 理解为一个会使用工具的工作助手。它可以先查询工单，再读取合同信息，遇到缺失内容时继续查询或提问。工具调用次数和执行步骤因任务而异。

概念来源：[Anthropic：Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)。

## Slide 3 of 4

**Type**: Content
**Title**: 业务任务需要明确的业务含义
**Filename**: 03-slide-business-meaning.png
**Layout**: hub-spoke

// NARRATIVE GOAL
围绕 SLA 提问展示四类资料与未确认口径，说明业务含义决定如何解释数据。

// VISUAL AND KEY CONTENT
Create an illustrated CENTRAL-QUESTION slide. Place a prominent service-work-order clipboard in the center with the question written on it. Arrange FOUR source illustrations around it in a calm open composition: top-left contract sheets, top-right an open business manual, bottom-left a database cylinder with a small clock beside it, bottom-right a simple API/technical document window. These are drawings of source objects, not rectangular UI cards. Each source has a clear heading and one concise question written beside/below its illustration. Four thin lines connect the sources inward to the central question; keep lines out of letters and use only the four labels below. The centerpiece and source illustrations should be larger than purely decorative icons. The concluding sentence is regular slide content in the lower open band, separated from the diagram. Keep the exact qualification that this is teaching illustration. No fabricated source clauses or schema fields.
EXACT TEXT:
Title: 业务任务需要明确的业务含义
Center question, two lines allowed: 这张工单满足 SLA 吗？
Center small caption: SLA：服务水平协议
Near center, small clear qualifier: 教学示意
Top-left heading: 合同条款
Top-left question: 哪份合同、哪种严重度决定目标？
Top-left connection label: 适用目标
Top-right heading: 业务手册
Top-right question, two lines: SLA 指响应、到场、恢复，还是解决时限？
Top-right connection label: 阶段含义
Bottom-left heading: 数据库字段
Bottom-left question, two lines: 从何时计时？暂停和空值怎样处理？
Bottom-left connection label: 计时数据
Bottom-right heading: 接口说明
Bottom-right question, two lines: 所需定义和数据分别在哪里？
Bottom-right connection label: 查询入口
Conclusion: 业务口径决定数据怎样解释。
Use only these texts. Do not assert a specific SLA target, timing policy, contract applicability, or yes/no verdict. All four questions must remain visible and large enough to read.

// SPEAKER NOTES
SLA 是服务水平协议，通常约定服务质量或时间目标。例如，同样写着“4 小时”，可能指首次响应，也可能指恢复服务。计时和适用条件不同，最终结论就可能不同。这里的问题来自案例中需要业务确认的内容，不预设实际口径。

案例来源：[工业服务场景摘要](https://github.com/yemmmm/ontology-platform/blob/main/docs/evaluation-scenarios/industrial-service-v3/modeling-input/scenario-brief.md)。

## Slide 4 of 4

**Type**: Content
**Title**: 帮助 Agent 完成业务任务的几种方法
**Filename**: 04-slide-methods-comparison.png
**Layout**: comparison-matrix

// NARRATIVE GOAL
完整比较提示词、文档 RAG、微调与本体的分工，不暗示单一技术更优。

// VISUAL AND KEY CONTENT
Create a full-width FOUR-ROW COMPARISON TABLE slide. Keep the source's four columns and four methods. Title at top. The table is drawn with thin slightly irregular ink rules, a very pale slate-blue header band and a subtle pale ochre tint behind the column 主要做什么. Use 22% of table width for 方法, 26% for 主要做什么, 26% for 工单场景中的例子, 26% for 需要关注什么. Table occupies the middle 70% of the canvas. At left of each method name, add ONE small sober hand-drawn icon: instruction/speech sheet, magnifying glass over a document, training/network sketch, concept-map sketch. Icons clarify the methods and must not replace text. Each cell may wrap to two short lines; keep all body text highly legible. Use equal row weight, no ranking, stairs, stars, badges, checkmarks, or crosses. Conclusion placed in the lower content band, not a running footer.
EXACT TEXT:
Title: 帮助 Agent 完成业务任务的几种方法
Headers, in order: 方法 / 主要做什么 / 工单场景中的例子 / 需要关注什么
Row 1:
提示词工程
用指令和示例引导处理
先核对合同，再回答 SLA
表达是否清楚，模型是否遵循
Row 2:
常见文档 RAG
检索资料，供模型参考
找到合同条款与手册片段
材料是否完整、是否适用
Row 3:
模型微调
用训练样本调整模型
训练工单分类或固定格式
训练样本、更新与效果验证
Row 4:
本体
组织业务定义、关系与语义约定
连接工单、合同、严重度与 SLA
定义是否正确，关系是否完整
Conclusion: 这些方法各有侧重，实际系统可以组合使用。
Slashes above separate columns and are not literal separators to print. Keep every table entry; do not drop the caution column or substitute invented advantages. No numerical performance claims, platform acceptance claims, or active automatic-reasoning claims.

// SPEAKER NOTES
RAG 可简单解释为“先查资料，再根据资料回答”。微调可理解为“用样本训练模型适应某类工作”。此处对比常见的文档片段 RAG；RAG 也可以读取结构化知识或本体。本体提供的定义和关系，同样需要通过检索或工具送入 Agent 的上下文。检索、模型训练和形式推理是不同机制；形式推理结论需要相应公理、事实和推理器支持。

来源：[RAG 原始论文](https://arxiv.org/abs/2005.11401)、[LoRA 论文中的任务适配方法](https://arxiv.org/abs/2106.09685)、[W3C OWL 2 Primer](https://www.w3.org/TR/owl2-primer/)。
