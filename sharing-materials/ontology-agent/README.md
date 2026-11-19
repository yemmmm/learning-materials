# 本体与 Agent：演示任务工作目录

本项目内处理本次演示任务的固定工作目录：`docs/presentations/ontology-agent/`。后续内容修订、页面制作、排练与导出从这里推进。

## 当前版本：v3.6

- [离线 HTML](exports/ontology-agent-slides-v3.6.html) · [PDF](exports/ontology-agent-slides-v3.6.pdf) · [完整演讲稿](exports/ontology-agent-speech-v3.6.md) · [整套 ZIP](exports/ontology-agent-v3.6.zip)
- [内容审阅稿](exports/ontology-agent-content-v3.6.md) · [本轮修订说明](exports/ontology-agent-review-v3.6.md) · [制作源码与使用说明](v3-html/README.md)
- 首页标题为“本体论思想在agent中的应用”。共 23 页，新增 P15 本体的难点与代价，紧接 P16“何时值得建本体”；平台三页与全部 13 个 FAQ 保留。

## 已发布版本入口

- [v3.4 HTML 演示：22 页，内容去重与页序调整](exports/ontology-agent-slides-v3.4.html)
- [v3.4 逐页演讲稿](exports/ontology-agent-speech-v3.4.md) · [内容审阅稿](exports/ontology-agent-content-v3.4.md) · [PDF](exports/ontology-agent-slides-v3.4.pdf) · [去重与页序审阅](exports/ontology-agent-review-v3.4.md) · [整套 ZIP](exports/ontology-agent-v3.4.zip)

- [v3.3 HTML 演示：27 页，新增 SKOS、SWRL、OWL-S、SPARQL 速览](exports/ontology-agent-slides-v3.3.html)
- [v3.3 内容审阅稿](exports/ontology-agent-content-v3.3.md) · [PDF](exports/ontology-agent-slides-v3.3.pdf) · [整套 ZIP](exports/ontology-agent-v3.3.zip)
- [v3.2 HTML 演示：26 页，新增符号主义、联结主义与专家系统](exports/ontology-agent-slides-v3.2.html)
- [v3.2 内容审阅稿](exports/ontology-agent-content-v3.2.md) · [PDF](exports/ontology-agent-slides-v3.2.pdf) · [整套 ZIP](exports/ontology-agent-v3.2.zip)
- [v3.1 HTML 内容增强版：22 页，含截图与 13 个 FAQ](exports/ontology-agent-slides-v3.1.html)
- [v3.1 内容审阅稿](exports/ontology-agent-content-v3.1.md) · [PDF](exports/ontology-agent-slides-v3.1.pdf) · [整套 ZIP](exports/ontology-agent-v3.1.zip)
- [v3.0 可编辑 PowerPoint：18 页](exports/ontology-agent-slides-v3.0.pptx)
- [v3.0 PDF](exports/ontology-agent-slides-v3.0.pdf) · [讲者备注与来源](exports/ontology-agent-speaker-notes-v3.0.md) · [整套 ZIP](exports/ontology-agent-v3.0.zip)
- [v3.0 已审阅的逐页草稿](outline-v3.0.md) · [制作源码与说明](v3/README.md)
- [演示总入口与逐页预览](deck/index.html)
- [完整网页演示](deck/editorial.html)
- [v2 完整演讲稿工作稿](speech.md)
- [逐页方案](deck/source-plan.md)
- [逐页备注与来源](deck/speaker-notes.md)
- [统一教学材料](deck/case-materials.md)

## 目录结构

```text
ontology-agent/
├── README.md                      # 本任务入口、路径与使用说明
├── speech.md                      # 完整演讲稿工作稿
├── deck/                          # 演示制作与预览
│   ├── source-plan.md             # 逐页方案
│   ├── build.py                   # 逐页内容与 HTML 生成
│   ├── deck.css                   # 页面样式
│   ├── deck.js                    # 交互
│   ├── assets/                    # 字体资源
│   ├── previews/                  # 逐页预览
│   ├── index.html                 # 演示入口
│   ├── editorial.html             # 交互演示
│   └── editorial.pdf              # 当前演示的静态 PDF
└── exports/                       # 按版本保留的发布产物
    ├── ontology-agent-slides-v2.0.pdf
    └── ontology-agent-speech-v2.0.md
```

已发布版本为 v3.6 HTML 演示，共 23 页：20 页主线与 3 页答疑附录。三层区分之后紧接 RDF/OWL 与相关技术速览；两条 AI 路线位于 P10–P12；P15 介绍本体难点与代价，P16 判断投入价值；OntoWeave 以 P18 架构、P19 能力、P20 实际界面展开；末尾保留全部 13 个 FAQ。制作入口见 [v3-html/README.md](v3-html/README.md)。

v3.0 PPTX 保留为此前的 18 页版本，文字、节点与连线为原生可编辑元素。

`v3/` 存放新版本制作源码和讲者备注。`deck/` 与 `speech.md` 保留 v2 的 37 页材料及完整演讲稿。

## 制作与导出

v3.0 已按审阅通过的草稿制作。新版本制作流程见 [v3/README.md](v3/README.md)，以下步骤保留用于 v2 历史材料。

用户于 2026-10-15 要求先修改前 10 页并发一版，当前修订稿已冻结并出版为 v2.3，包含 PDF、同步演讲稿、离线 HTML、配套来源、可编辑架构图和 ZIP 阅读包。已同步个人资料库并推送提交 `0e18aba`；保留 `exports/` 中的 v2.0、v2.1、v2.2。之后的修订按用户后续要求推进。

1. 修改逐页方案 `deck/source-plan.md`，在 `deck/build.py` 中落实页面内容，必要时调整 CSS／JS，并同步 `speech.md`。
2. 在项目根目录执行：

   ```bash
   python docs/presentations/ontology-agent/deck/build.py
   ```

   该命令重建 HTML、目录、备注和案例材料。PDF 与逐页预览需要随后通过浏览器渲染／打印另行更新。
3. 在浏览器中打开 `deck/index.html` 检查内容与交互，导出 PDF，核对与演讲稿的页序、条件和案例结论。
4. 用户明确说“出版”后，将确认后的成套 PDF、HTML、演讲稿、配套资源与 ZIP 放入 `exports/`，文件名使用同一版本号；下一次小幅修订可用 `v2.4`，主线或结构大幅调整可用 `v3.0`。新增版本文件，保留旧版。
5. 出版时将发布文件同步到[个人资料库的版本归档目录](https://github.com/yemmmm/learning-materials/tree/master/ontology/projects/ontology-agent-presentation)。本地位置为 `~/learning-materials/ontology/projects/ontology-agent-presentation/`，修改个人资料库后按其约定提交并推送。

## 已归档版本

| 版本 | PDF | 演讲稿 | HTML 与阅读包 | 说明 |
| --- | --- | --- | --- | --- |
| v3.6 | [23 页 PDF](exports/ontology-agent-slides-v3.6.pdf) | [内容审阅稿](exports/ontology-agent-content-v3.6.md) · [完整演讲稿](exports/ontology-agent-speech-v3.6.md) | [离线 HTML](exports/ontology-agent-slides-v3.6.html) · [ZIP](exports/ontology-agent-v3.6.zip) | 首页换题；新增难点与代价；[修订说明](exports/ontology-agent-review-v3.6.md) |
| v3.5 | [22 页 PDF](exports/ontology-agent-slides-v3.5.pdf) | [内容审阅稿](exports/ontology-agent-content-v3.5.md) · [完整演讲稿](exports/ontology-agent-speech-v3.5.md) | [离线 HTML](exports/ontology-agent-slides-v3.5.html) · [ZIP](exports/ontology-agent-v3.5.zip) | 平台三页重构并突出建模 Agent；[累计修订说明](exports/ontology-agent-review-v3.5.md) |
| v3.4 | [22 页 PDF](exports/ontology-agent-slides-v3.4.pdf) | [内容审阅稿](exports/ontology-agent-content-v3.4.md) · [完整演讲稿](exports/ontology-agent-speech-v3.4.md) | [离线 HTML](exports/ontology-agent-slides-v3.4.html) · [ZIP](exports/ontology-agent-v3.4.zip) | 27 页合为 22 页；三层后紧接 RDF/OWL；[去重与页序对照](exports/ontology-agent-review-v3.4.md) |
| v3.3 | [27 页 PDF](exports/ontology-agent-slides-v3.3.pdf) | [内容审阅稿](exports/ontology-agent-content-v3.3.md) · [讲者备注](exports/ontology-agent-speaker-notes-v3.3.md) | [离线 HTML](exports/ontology-agent-slides-v3.3.html) · [ZIP](exports/ontology-agent-v3.3.zip) | 一页速览 SKOS、SWRL、OWL-S、SPARQL；保留此前内容 |
| v3.2 | [26 页 PDF](exports/ontology-agent-slides-v3.2.pdf) | [内容审阅稿](exports/ontology-agent-content-v3.2.md) · [讲者备注](exports/ontology-agent-speaker-notes-v3.2.md) | [离线 HTML](exports/ontology-agent-slides-v3.2.html) · [ZIP](exports/ontology-agent-v3.2.zip) | 新增两条 AI 路线、专家系统、优缺点与 Agent 协作；保留截图及 13 个 FAQ |
| v3.1 | [22 页 PDF](exports/ontology-agent-slides-v3.1.pdf) | [内容审阅稿](exports/ontology-agent-content-v3.1.md) · [讲者备注](exports/ontology-agent-speaker-notes-v3.1.md) | [离线 HTML](exports/ontology-agent-slides-v3.1.html) · [ZIP](exports/ontology-agent-v3.1.zip) | 每页内容增强；实际模型浏览截图；恢复 13 个 FAQ；分步与语义交互 |
| v3.0 | [18 页演示](exports/ontology-agent-slides-v3.0.pdf) | [讲者备注与来源](exports/ontology-agent-speaker-notes-v3.0.md) | [可编辑 PPTX](exports/ontology-agent-slides-v3.0.pptx) · [ZIP](exports/ontology-agent-v3.0.zip) | 围绕差旅审批重构；本体三层区分、常见组成、Agent 使用与 OntoWeave 简介 |
| v2.3 | [37 页演示](exports/ontology-agent-slides-v2.3.pdf) | [同步演讲稿](exports/ontology-agent-speech-v2.3.md) | [离线 HTML](exports/ontology-agent-slides-v2.3.html) · [ZIP](exports/ontology-agent-v2.3.zip) | 首页问题上移；相似政策对照；聚焦理解的方法；定义与 Palantir 应用重构 |
| v2.2 | [37 页演示](exports/ontology-agent-slides-v2.2.pdf) | [同步演讲稿](exports/ontology-agent-speech-v2.2.md) | [离线 HTML](exports/ontology-agent-slides-v2.2.html) · [ZIP](exports/ontology-agent-v2.2.zip) | 架构与 Team 重绘；七视角完整展示；13 个 FAQ；附可编辑架构图 |
| v2.1 | [37 页演示](exports/ontology-agent-slides-v2.1.pdf) | [配套演讲稿](exports/ontology-agent-speech-v2.1.md) | [离线 HTML](exports/ontology-agent-slides-v2.1.html) · [ZIP](exports/ontology-agent-v2.1.zip) | 本轮继续调整前的同步稿；七视角交互可在 HTML 查看 |
| v2.0 | [37 页演示](exports/ontology-agent-slides-v2.0.pdf) | [配套演讲稿](exports/ontology-agent-speech-v2.0.md) | — | 与个人资料库已发布文件逐字节一致 |

v2.2 已同步重绘 P20 架构与 P23 当前直接写入路径，P22 在 HTML/PDF 中同时列出七项视角；P35 新增本体与知识图谱区别，P36 明确七视角属于 OntoWeave 当前方式。演讲稿同步更新。P25 保留截至 2026-10-14 的历史验证口径；架构图远期设想均标“待实现·规划待确认”。本轮调整已出版并同步个人资料库。

## 历史位置

- [原逐页方案](../2026-10-14-ontology-agent-next-version-plan.md)
- [原演讲稿](../2026-10-15-ontology-agent-talk-script.md)
- [原 v2 制作目录](../../../slide-deck/ontology-agent-editorial-20261014-v2/README.md)

这些位置保留为已有交付记录，后续工作以本目录为入口。

v2.3 完成前 10 页本轮意见：首页贯穿问题移至标题下方，副标题改为“让 Agent 读懂业务含义，找到判断依据”；P04/P05 并列 A/B 商家相似政策，P06 聚焦如何理解和辨别；P09 先解释工程本体并简要区分本体论，P10 单独介绍 Palantir 应用与背景。演讲稿同步，来源链接见逐页备注。第 11 页之后的主体内容保留。
