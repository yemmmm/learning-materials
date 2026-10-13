---
slide: 2
title: Agent 怎样完成一个任务
filename: 02-slide-agent-task-loop.png
aspect_ratio: 16:9
language: zh-CN
backend: codex-imagegen
session_id: slides-ontology-agent-part1-20261013
references:
  - ref_id: 01
    filename: 01-style-reference.png
    usage: direct
---

Use case: productivity-visual
Asset type: A complete PowerPoint presentation slide, 16:9 landscape, target 1920×1080 or another exact 16:9 high-resolution canvas. Render the finished slide including all simplified Chinese text. Generate only ONE slide, not a contact sheet.
Input image: Reference image 1 is a STYLE AND PALETTE reference. This is a NEW slide with the new content below, not an edit or copy of the reference slide. Keep the warm paper, ink line quality and readable typography. Add slightly more purposeful illustrative elements as requested.
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

SLIDE CONTENT AND COMPOSITION:
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

GLOBAL CONSTRAINTS: At least 5% safe margins. Preserve exact Chinese text and source meaning. No text clipping, overlapping connectors, extraneous prose, logos, slide numbers, running footer, photorealism, 3D rendering, screenshots, or watermarks. Large clear title and readable body text. Follow the slide-specific layout rather than copying the reference's left-text/right-map arrangement.
