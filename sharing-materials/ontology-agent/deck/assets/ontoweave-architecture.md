# OntoWeave 系统架构图说明

这张图用于 P20，画布为 1696×650。它把外部参与者、OntoWeave 平台边界、外部业务系统和独立验收边界分开，当前模型写入路径采用 R4.3-024/025 的 direct modeling 语义。

## 图中组件

| 区域 | 组件 | 图中含义 |
| --- | --- | --- |
| 外部协作 | 业务人员 | 确认业务含义与范围，不能由平台自动代替。 |
| 外部协作 | Modeling Team | 当前生产协作边界，内部展示 Modeling、Coordinator、CQ、Delivery 四类职责。 |
| 外部协作 | 远期设想｜待实现 · 规划待确认 | 仅作为远期演进占位，列出“跨阶段协作调度”“运行管理界面”两个候选；两者均未实现、未立项确认，不是当前产品承诺。 |
| 平台接口 | React/Vite、FastAPI、FastMCP | 管理界面与两类接口入口；接口复用平台应用服务。 |
| 平台服务 | 授权与范围 | Project/Ontology 访问范围和执行上下文边界。 |
| 平台服务 | 直接模型变更 | Modeling 提交统一图变更；程序编译、绑定真实上下文，在单次 `apply_atomic` 内校验并原子应用，保留回执和实际修订。 |
| 平台服务 | 语义查询与读取 | 受治理的 Context Query、IRI 周边读取与阶段自查。 |
| 平台数据 | PostgreSQL | 平台元数据、工作状态、请求/回执等工作流状态。 |
| 平台数据 | RDF/Oxigraph | 权威业务语义图。 |
| 外部业务 | 业务数据库、业务 API | 订单等业务行与业务执行留在平台外；消费 Agent 依据授权直接访问。 |
| 独立验收 | Acceptance | 只读治理上下文，独立判定，不创建、继续或修复生产建模 run。 |

## 当前路径与来源

- 当前直接写入链：`Modeling 提交 → compiler → apply_atomic → 回执/实际修订 → 召回与 IRI 周边自查 → 独立语义验收`。来源：`docs/requirements/requirements-v4.3.md:1789-1880`（R4.3-024）及 `:1891-1985`（R4.3-025）。
- R4.3-024 退役当前模型 Batch 写入的新增 dry-run、Protocol 翻译审批和隐藏 dry-run 依赖；图中因此没有把 dry-run 画成当前写入步骤。来源：`requirements-v4.3.md:1799-1804,1875-1880`。
- compiler 与 DirectModelExecutor 分工是：compiler 生成依赖有序 batches/source_map，Executor 取得真实 Session/lease/revision 并调用 `apply_atomic`；不把业务判断交给平台。来源：`requirements-v4.3.md:1901-1927` 与 `docs/architecture/overview.md:5-14`。
- 平台组件和存储边界来自 `docs/architecture/overview.md:18-38`：React/Vite、FastAPI、FastMCP、PostgreSQL、RDF Dataset/Oxigraph；外部 Agent 负责建模判断和最终答案。
- Modeling 的 direct capability 及工具说明来自 `modeling_team/capability_mcp.py:77-99,115-135,829-840`。Protocol 仍可在历史合同/兼容表面中出现，但本图没有将其画成当前 direct modeling 的必经写入角色。
- Team 角色职责与独立 Acceptance 的边界来自 `docs/presentations/ontology-agent/deck/source-plan.md:220-225`、`modeling_team/agent-packages/{modeling,coordinator,competency-question,delivery,acceptance}/package.yaml`，以及 R4.3-024 的 A8/A9 约束。
- 外部业务系统边界来自 `docs/architecture/overview.md:115-120`：平台只描述外部能力的 binding、输入输出、约束和凭证需求类型；执行与凭证实例留给外部 Agent/系统。

## 规划占位的状态

R4.3-015 的“全局规划与阶段选择”是当前 Coordinator/Agent 的工作方式，来源为 `requirements-v4.3.md:811-827`，图中没有把它整体标成未实现。用户已授权展示远期设想，但要求保留“待实现、规划待确认”的边界，因此赭色虚线区列出两个有架构演进依据的候选：

- **跨阶段协作调度**：ADR 0008 `:124-128` 将 generic workflow engine、distributed scheduling 等列为当前明确排除的未来产品化范围。
- **运行管理界面**：ADR 0007 `:53-56` 将 management UI 列为需要独立需求的后续能力；ADR 0008 `:124-128` 也明确 UI 属于排除项。

这两个候选都不是已立项、已实现或当前交付承诺；最终范围、优先级和需求归属仍待规划确认。退役的 dry-run、Protocol 翻译审批、OWL/SHACL/规则脚本等不列入远期设想。

## 图例

- 绿色实线：当前实现路径。
- 赭色实线：外部业务数据/执行边界。
- 赭色虚线：远期设想，待实现且规划待确认。
- 绿色虚线：独立 Acceptance 只读治理上下文；不回写生产链。

`.drawio` 是可编辑源文件；`.drawio.svg` 是与当前布局同步的原生 SVG，使用内嵌文本和样式，可直接嵌入 HTML 或导出 PDF。
