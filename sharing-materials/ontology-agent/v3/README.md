# 本体与 Agent · v3.0

根据用户审阅通过的 [18 页草稿](../outline-v3.0.md) 制作，建议讲述 25–30 分钟。

- [可编辑 PPTX](../exports/ontology-agent-slides-v3.0.pptx)
- [PDF](../exports/ontology-agent-slides-v3.0.pdf)
- [逐页讲者备注与来源](speaker-notes.md)
- [完整发布包](../exports/ontology-agent-v3.0.zip)

## 内容与视觉

差旅审批贯穿全篇：从“谁来审批”引入，区分现实世界、本体与表达技术，介绍常见组成、类与个体、RDF/OWL、知识图谱，再说明 Agent 如何结合语义、事实与工具处理任务。最后两页介绍 OntoWeave 的职责和构建／使用路径。

匹配 `../deck/editorial.pdf` 的 16:9 画布、暖白底色、深绿色与细线版式，使用 Noto Sans CJK SC／Noto Serif CJK SC。封面复用 `../deck/assets/cover-network.png`。正文、关系图与流程图均为原生可编辑元素，PPTX 内含逐页讲者备注。PDF 内嵌所用字体；编辑 PPTX 时建议安装上述字体以保持版式一致。

OWL 推理页介绍通用技术能力。OntoWeave 当前职责以项目要求为依据，不表示平台已具备 OWL 自动推理。案例、流程和读取内容均为教学示意。

## 重建

使用已安装的 `@oai/artifact-tool` 运行时，无需安装额外依赖。默认路径在脚本中配置，可用 `ONTO_PRESENTATION_RUNTIME`、`ONTO_PRESENTATION_SKILL` 覆盖。

```bash
cd /home/yangxiang/ontology-platform/docs/presentations/ontology-agent
/home/yangxiang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node v3/build.mjs
/home/yangxiang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node v3/finalize.mjs exports/ontology-agent-slides-v3.1.pptx
```

`build.mjs` 写入私有 `.build-v3/` 中间目录及本目录的讲者备注。`finalize.mjs` 校验结构、页数、尺寸、字体来源及重新导入，输出指定的独立文件，不覆盖已有成品。后续版本仍需检查每页最终渲染结果，核对页脚版本与内容后再归档。

v3.0 已完成 18 页文件结构和版面检查，并使用随运行时提供的 LibreOffice 从最终 PPTX 导出 PDF，逐页检查文字、连线和裁切；未在 Microsoft PowerPoint 客户端实测。中间预览与检查过程文件在交付后清理。
