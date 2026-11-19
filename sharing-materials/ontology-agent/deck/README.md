# 本体与 Agent：OntoWeave 演示分享

依据 [2026-10-14 内容修订方案](source-plan.md) 制作的独立新版，共 **37 页、四章正文、13 个 FAQ**。沿用暖白底、森林绿与宋体标题，用退货与退款问题贯穿概念、技术、建模方法与完整案例。

- [演示入口与逐页预览](index.html)
- [完整交互演示](editorial.html)
- [完整 PDF](editorial.pdf)
- [逐页讲解备注与来源](speaker-notes.md)
- [虚构教学材料](case-materials.md)
- [项目来源摘录](sources.html)

## 页序

| 页码 | 内容 |
| --- | --- |
| 1—2 | 封面与目录 |
| 3—7 | Agent 的业务理解难题 |
| 8—17 | 本体的概念、技术与价值 |
| 18—25 | OntoWeave 与建模方法 |
| 26—34 | 电商退货与退款模拟案例 |
| 35—37 | 选型、建设、质量与维护 FAQ |

## 使用

解压完整 ZIP 后，在现代浏览器中打开 `index.html`。也可以单独打开 `editorial.html`；字体、图形、样式、交互与讲解备注均已内嵌，播放不依赖网络。独立来源文件保留在完整包中。

方向键、空格及 PageDown／PageUp 用于逐步展示与翻页。`A` 展开当前页，`N` 显示备注，`G` 返回目录，`F` 全屏，`Home`／`End` 跳转首页／末页，`?` 查看帮助。手机横屏支持左右滑动。

首页在标题下方突出贯穿问题；第 5 页并列 A/B 店两份相似政策及不同结论；第 6 页聚焦如何分清政策；第 9 页解释工程本体并简要区分本体论，第 10 页介绍 Palantir 应用与公司背景；第 20 页展示含 Team 内部职责的系统架构，远期设想标为“待实现·规划待确认”；第 22 页同时列出七个视角与具体例子，点击条目高亮图中相关内容；FAQ 可以收起或展开，末页政策变更示例随对应问题展示。PDF 展开全部讲解内容，完整保留七项视角。七视角是 OntoWeave 当前的组织方式，并非通用本体方法论。

`E` 开启正文编辑，`Ctrl+S` 下载修改后的 HTML。编辑结果保存在下载文件中。正文图形由原生 SVG 表达，可在 `build.py` 中修改节点、关系与文字；封面使用 `assets/cover-network.png` 抽象装饰图，生成提示保留在同目录的 `cover-network.prompt.txt`，图片随 HTML 内嵌。CSS 和交互分别位于 `deck.css`、`deck.js`。单独下载的修改版不会自动重写本目录的讲解备注、预览或 PDF。

## 内容边界

电商资料、订单、规则、SQL 与 API 均为虚构教学设计，本次没有接入或调用真实订单、售后或退款系统。P25 分别保留项目已实现能力、历史有界通过与当前整体 PARTIAL，不将历史题集结果当成通用准确率。

RDF／RDFS／OWL／SPARQL 的原理说明与 OntoWeave 当前实现分开。当前不提供 OWL 自动推理、SHACL 专用校验、业务规则脚本及业务流程执行引擎。

## 重建

```bash
python build.py
```

上述命令从当前目录内容生成 HTML、目录、备注、材料与清单，使用已经随包提供的字体。新增文字后，可在安装 Noto CJK 字体及 FontTools 的环境中执行 `python build.py --refresh-fonts` 更新字体子集。`project-sources.json` 为制作时的摘录，只有显式添加 `--refresh-sources` 才从原仓库重新截取。

PDF 与预览由 Chromium 渲染 HTML 生成。PDF 使用 16:9 全页，全部分步内容展开。字体与沿用基础样式的许可见 [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt)。

架构图可编辑源文件：[draw.io](assets/ontoweave-architecture.drawio)，嵌入版本：[SVG](assets/ontoweave-architecture.drawio.svg)，[边界与证据说明](assets/ontoweave-architecture.md)。P20/P23 按 R4.3-024/025 陈述当前工程实现；真实语义效果未验证。
