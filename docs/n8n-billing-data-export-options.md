# n8n 计费数据接入方案

> 场景：部门自建 n8n + 模型服务，业务方调用，总公司按 workflow 执行次数结算费用。统计与计费在总公司侧完成。
>
> 本文梳理给总公司提供"执行次数数据"的几种可行路径，以及落地前必须双方对齐的业务规则。

---

## 一、数据源摸底

### 1.1 n8n 内部已有的数据

| 表 | 含义 | 用于计费的可行性 |
|---|---|---|
| `execution_entity` | **权威源**：每条执行一行，含 `workflowId` / `status` / `mode` / `startedAt` / `stoppedAt` / `retryOf` | ⭐ 首选，已有索引 `idx_execution_entity_workflow_id_started_at` |
| `workflow_entity` | workflow 元信息（name、active、isArchived） | 用于名字映射 |
| `project` + `shared_workflow` | **workspace 概念**对应 n8n 的 project | 多 project 需 Enterprise License |
| `workflow_statistics` | n8n 自维护的按 workflow 聚合统计 | 当前为空，需特定配置触发 |
| `insights_by_period` | 按时段预聚合（Insights 功能） | 当前为空，企业版功能 |

### 1.2 `/metrics` 端点能力（实测 n8n v2.26.8）

业务相关指标只有：

- `n8n_workflow_execution_duration_seconds`（Histogram，默认开启）
- `n8n_active_workflow_count`（Gauge）
- `n8n_webhook_request_duration_seconds`（Histogram）
- `n8n_token_exchange_*` / `n8n_embed_login_*`（认证类 Counter）

**关键发现**：开启 `N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL=true` 后，`n8n_workflow_execution_duration_seconds` Histogram 的每次观测都会带 `workflow_id` 标签。Histogram 派生的 `_count` 时间序列语义就是"被观测了几次"=**执行次数**。

源码出处：`packages/cli/src/metrics/prometheus/workflow-execution-duration-metrics.service.ts`

```typescript
const labelNames = ['status', 'mode'];
if (this.config.includeWorkflowIdLabel) {
    labelNames.push('workflow_id');   // 开关一开就加 workflow_id 标签
}
```

这意味着：

```promql
# 每个 workflow 从进程启动以来的累计执行次数
sum by (workflow_id) (n8n_workflow_execution_duration_seconds_count{workflow_id!=""})

# 近 1 小时的执行次数
sum by (workflow_id) (increase(n8n_workflow_execution_duration_seconds_count{workflow_id!=""}[1h]))
```

技术上**可以用于按 workflow 统计执行次数**。

### 1.3 `/metrics` 用于计费的硬伤

| 硬伤 | 说明 |
|---|---|
| **重启清零** | `_count` 是 prom-client 进程内 counter，n8n 重启归零。总公司必须持续抓取并存储，否则丢数据 |
| **多实例各自计数** | multi-main（2 main + 3 worker）每个实例各自从 0 开始，总公司需 `sum by (workflow_id)` 跨实例聚合 |
| **无 executionId 明细** | `_count` 是数字，账期争议时给不出逐条核查 |
| **无账期对齐** | `increase()` 是基于 scrape 间隔的插值近似，月度账单有 1-2% 量级误差 |
| **无 workspace 维度** | 标签只有 `workflow_id` / `status` / `mode`，无 `project_id`。按部门/客户分账需另行映射 |
| **数据保留期受限** | Prometheus 本地默认 15 天保留；月度/年度账单需远程存储（Thanos / Mimir / VictoriaMetrics） |

---

## 二、五种方案对比

### 方案 A：直接暴露 `/metrics`

**做法**：你方在 `.env` 加 `N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL=true`，重启所有 n8n 实例，总公司用 Prometheus 持续抓取。

| 维度 | 评估 |
|---|---|
| 实现成本 | 极低（改 env，零自研） |
| 准确性 | 中（1-2% 量级误差） |
| 对账能力 | 弱（无明细） |
| workspace 维度 | 需总公司维护映射表 |
| 适合 | 总公司已有 Prometheus 基础设施，容许小误差 |

**前置条件**：
1. 你方开启 `N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL=true`（所有 main + worker）
2. 你方给总公司一个稳定的 `/metrics` 入口（建议加 Basic Auth 或 mTLS）
3. 总公司 Prometheus 持续抓取所有 5 个实例，数据保留期 ≥ 最长账期 + 对账窗口
4. 总公司处理 counter reset（用 `increase()` 或 `rate()*interval`）
5. 总公司跨实例聚合 `sum by (workflow_id)`
6. 双方约定业务过滤规则（按 `status` / `mode` 过滤）

---

### 方案 B：差值计数器接口（Pull）

**做法**：你方提供一个 HTTP 接口，总公司定期（每小时/每天）pull，记录两次结果之差作为本期计费。

接口示例：

```
GET /api/billing/counts?workflow_id=xxx&from=2026-07-01T00:00:00&to=2026-07-02T00:00:00
```

返回：

```json
{
  "workflow_id": "xxx",
  "from": "...",
  "to": "...",
  "count": 142
}
```

数据源：`SELECT count(*) FROM execution_entity WHERE startedAt >= ? AND startedAt < ? AND workflowId = ?`

| 维度 | 评估 |
|---|---|
| 实现成本 | 低（1-2 小时，可用 n8n Webhook Workflow 实现） |
| 准确性 | 高（PG 持久化、精确 COUNT） |
| 对账能力 | 中（有 workflow 维度，无 executionId 明细） |
| workspace 维度 | 原生支持 |
| 适合 | 总公司接受 pull 接口，需要比 metrics 更准确 |

---

### 方案 C：账期报表接口 ⭐ 推荐

**做法**：总公司传时间范围，返回该账期内每个 workflow / workspace 的执行次数（带哈希指纹用于一致性校验）。

接口示例：

```
GET /api/billing/period?from=2026-07-01T00:00:00&to=2026-07-31T23:59:59
```

返回：

```json
{
  "period": {"from": "...", "to": "..."},
  "generated_at": "...",
  "totals": {"workflow_executions": 12345},
  "by_workflow": [
    {
      "workflow_id": "abc",
      "name": "...",
      "project_id": "...",
      "success_count": 95,
      "failed_count": 5,
      "total_count": 100,
      "execution_ids_hash": "sha256:..."
    }
  ],
  "by_project": [...]
}
```

`execution_ids_hash` = 对该 workflow 在账期内所有 `executionId` 排序后取 sha256。总公司无需拉明细即可验证一致性，争议时可申请明细。

| 维度 | 评估 |
|---|---|
| 实现成本 | 中（半天-1 天，可用 n8n Webhook Workflow 实现） |
| 准确性 | 极高（基于 PG COUNT） |
| 对账能力 | 强（哈希指纹 + 可申请明细） |
| workspace 维度 | 原生支持 |
| 适合 | 严肃计费、有对账需求、账期固定 |

---

### 方案 D：主动推送账单 ⭐ 推荐

**做法**：你方每天/每月定时生成账单 JSON，主动 POST 到总公司提供的接收端，附 HMAC 签名防篡改。

推送示例：

```http
POST /api/billing/receive
X-Signature: hmac-sha256=...
Content-Type: application/json

{
  "bill_id": "2026-07-daily-20260731",
  "period": {"from": "...", "to": "..."},
  "generated_at": "...",
  "totals": {"workflow_executions": 412},
  "by_workflow": [...]
}
```

| 维度 | 评估 |
|---|---|
| 实现成本 | 中（半天，可用 n8n Schedule Workflow 实现） |
| 准确性 | 极高 |
| 对账能力 | 强（含签名 + 账单 ID） |
| workspace 维度 | 原生支持 |
| 适合 | 责任边界要清晰、总公司倾向被动接收 |

**优势**：你方出具账单，总公司核对，避免"谁统计错了"的扯皮。

---

### 方案 E：原始执行明细导出

**做法**：账期内所有 executionId + 元信息批量导出给总公司，总公司自行汇总。

| 维度 | 评估 |
|---|---|
| 实现成本 | 高（需分页、压缩、传输） |
| 准确性 | 极高 |
| 对账能力 | 极强（逐条核查） |
| workspace 维度 | 原生支持 |
| 适合 | 严苛审计场景、月执行量 ≤ 数十万 |

---

### 方案对比总览

| 方案 | 实现成本 | 准确性 | 对账能力 | workspace 维度 | 适合场景 |
|---|---|---|---|---|---|
| **A. 给 /metrics** | 极低（改 env） | 中（1-2% 误差） | 弱（无明细） | 需映射 | 总公司已有 Prometheus，容许小误差 |
| **B. 差值计数接口** | 低 | 高 | 中 | 原生支持 | 总公司接受 pull 接口 |
| **C. 账期报表接口** ⭐ | 中 | 极高 | 强（哈希指纹） | 原生支持 | 严肃计费、有对账需求 |
| **D. 主动推送账单** ⭐ | 中 | 极高 | 强（含签名） | 原生支持 | 责任边界要清晰 |
| **E. 明细批量导出** | 高 | 极高 | 极强（逐条） | 原生支持 | 严苛审计场景 |

---

## 三、实现位置（与方案正交）

方案 C/D 的"接口契约"和"部署形态"是两个独立决策。

| 实现位置 | 新增服务？ | 适合方案 | 说明 |
|---|---|---|---|
| **n8n 内部 Webhook Workflow** | ❌ | C | Webhook 节点 → Postgres 节点 → Respond。零额外组件，享受 n8n 原生认证/日志 |
| **n8n 内部 Schedule Workflow** | ❌ | D | Schedule Trigger → Postgres 节点 → HTTP Request POST。零额外组件 |
| **独立微服务容器** | ✅ | C 和 D | docker-compose 加 Node/FastAPI 容器，直读 PG。解耦、灵活，但多一个组件维护 |

**起步建议**：用 n8n Workflow 实现（选 A 或 B 的实现位置），不新增服务。

**触发升级到独立服务的信号**：
- 单次查询超过 1 秒（PG 索引扛不住）
- 需要给多个业务方不同视图
- 需要复杂对账逻辑（哈希指纹、签名）
- webhook workflow 自身的执行记录占用 PG 太多

---

## 四、需要双方商讨的业务规则

> 计费场景下，业务规则比技术实现更重要。**这些必须在落地前和总公司对齐**，否则方案再完美也会扯皮。

### 4.1 计费口径

| 规则 | 选项 | 影响 |
|---|---|---|
| **失败执行是否计费** | 计 / 不计 / 部分（如仅超时计） | 决定 `WHERE status = 'success'` 还是全计 |
| **手动执行是否计费** | 计 / 不计 | 决定 `WHERE mode != 'manual'`。手动执行是业务方调试时点 Test Run 触发的 |
| **重试执行是否计费** | 每次重试都计 / 只计根执行 | 涉及 `retryOf` 字段去重 |
| **运行中（running）/ 等待中（waiting）的执行如何处理** | 计 / 不计 | 账期截止时正在跑的执行归到哪个账期 |
| **被删除的执行（n8n retention 清理）** | 仍计入 / 不计 | n8n 默认自动清理历史，需关闭或调长 |
| **不同 workflow 价格是否不同** | 统一价 / 按 workflow 分档 / 按 node 类型 | 影响返回结构 |

### 4.2 账期与对账

| 规则 | 选项 | 影响 |
|---|---|---|
| **账期粒度** | 自然日 / 自然月 / 双方约定 | 决定 `from` / `to` 的对齐 |
| **账期可变性** | 关账后不可改 / 可补单 | 是否需要"账单 ID + 签名" |
| **数据可重现性** | 同一账期多次拉取必须返回相同数据 | 接口幂等保证 |
| **对账窗口** | 关账后多久内可发起核查（如 30 天） | 决定数据保留期下限 |
| **争议处理** | 总公司主张 vs 你方主张，谁出账 | 影响选 push（D）还是 pull（C） |

### 4.3 workspace 维度（如果需要分账）

| 规则 | 选项 | 影响 |
|---|---|---|
| **是否需要按 workspace/部门/客户分账** | 需要 / 不需要 | 决定是否需要 Enterprise License 激活多 project |
| **当前 license 状态** | 已激活 / 未激活 | `.env` 里 `N8N_LICENSE_ACTIVATION_KEY=` 留空 = 所有 workflow 在默认 personal project |
| **无 license 的替代方案** | 用 workflow 命名前缀（如 `custA-xxx`）或 tag 分组 | 软分组，不够严谨 |

### 4.4 接入与安全

| 规则 | 选项 | 影响 |
|---|---|---|
| **接口形式** | Pull（HTTP GET） / Push（你方 POST） | 决定方案 C 还是 D |
| **认证方式** | Basic Auth / API Key / mTLS / HMAC 签名 | 影响实现复杂度 |
| **网络可达性** | 总公司能否直接访问 n8n Traefik（5680） | 需打通网络策略 |
| **限流** | 是否需要防止总公司高频拉取 | 影响是否需要缓存层 |
| **数据格式** | JSON / CSV / Parquet | 影响总公司接入复杂度 |

---

## 五、推荐路径

### 5.1 决策树

```
总公司是否已有 Prometheus 且接受 1-2% 误差？
├─ 是 → 方案 A（开 env，零自研）
└─ 否
   └─ 是否需要 executionId 明细对账？
      ├─ 是 → 方案 E（明细导出）
      └─ 否
         └─ 责任边界由谁主导？
            ├─ 总公司主动 pull → 方案 C（账期报表接口）
            └─ 你方主动 push  → 方案 D（推送账单）
```

### 5.2 起步建议

1. **第一步**：与总公司确认第四节业务规则（至少 4.1 计费口径必须对齐）
2. **第二步**：确认是否需要 workspace 维度 → 决定是否激活 Enterprise License
3. **第三步**：选定方案（建议 C 或 D）+ 选定实现位置（建议先用 n8n Workflow，不新增服务）
4. **第四步**：试点 1 个月，对比总公司 Prometheus 拉取的数据和你方接口数据，验证一致性
5. **第五步**：试点通过后正式上线，加签名/审计/告警

---

## 六、附：n8n Webhook Workflow 实现草图（方案 C）

```
[Webhook: GET /billing/period?from=&to=]
    ↓
[Postgres Node]
    SELECT
        e."workflowId",
        MIN(w.name) AS workflow_name,
        MIN(w."projectId") AS project_id,
        COUNT(*) FILTER (WHERE e.status = 'success') AS success_count,
        COUNT(*) FILTER (WHERE e.status != 'success') AS failed_count,
        COUNT(*) AS total_count
    FROM execution_entity e
    LEFT JOIN workflow_entity w ON w.id = e."workflowId"
    WHERE e."startedAt" >= '{{ $json.from }}'
      AND e."startedAt" <  '{{ $json.to }}'
      AND e."deletedAt" IS NULL
      AND e.mode != 'manual'
    GROUP BY e."workflowId"
    ↓
[Code Node: 聚合 + 加 HMAC 签名 + 计算 execution_ids_hash]
    ↓
[Respond to Webhook: 返回 JSON]
```

4 个节点，开发 1-2 小时。

---

## 七、参考链接

- n8n Prometheus metrics 配置：
  https://github.com/n8n-io/n8n-docs/blob/main/docs/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/enable-prometheus-metrics.md
- n8n 可视化 metrics 教程：
  https://github.com/n8n-io/n8n-docs/blob/main/docs/deploy/host-n8n/keep-n8n-running/visualize-metrics-with-grafana.md
- n8n 源码（duration metrics）：
  https://github.com/n8n-io/n8n/blob/master/packages/cli/src/metrics/prometheus/workflow-execution-duration-metrics.service.ts
- Prometheus Histogram 规范：
  https://prometheus.io/docs/concepts/metric_types/#histogram
- n8n workflow_statistics 表结构：
  https://github.com/n8n-io/n8n/blob/master/docs/generated/sqlite-schema/workflow_statistics.md
