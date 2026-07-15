# n8n 计费数据接入方案

> 场景：部门自建 n8n + 模型服务，业务方调用，总公司按 workflow 执行次数结算费用。统计与计费在总公司侧完成。
>
> 本文梳理给总公司提供"执行次数数据"的几种可行路径，以及落地前必须双方对齐的业务规则。

---

## 一、数据源摸底

### 1.1 n8n 内部已有的数据

| 表 | 含义 | 用于计费的可行性 |
|---|---|---|
| `execution_entity` | **权威源**：每条执行一行，含 `workflowId` / `status` / `mode` / `startedAt` 等 | ⭐ 首选 |
| `workflow_entity` | workflow 元信息（name、active） | 用于名字映射 |
| `project` + `shared_workflow` | workspace 概念对应 n8n 的 project | 多 project 需 Enterprise License |
| `workflow_statistics` / `insights_by_period` | n8n 自维护聚合 | 当前为空，依赖特定配置触发 |

### 1.2 `/metrics` 端点能力

**技术上可以拿到 per-workflow 执行次数**：

- `n8n_workflow_execution_duration_seconds` 是 Histogram，开启 `N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL=true` 后每次观测都带 `workflow_id` 标签
- Histogram 派生的 `_count` 序列语义 = "被观测了几次" = **执行次数**
- 源码：`packages/cli/src/metrics/prometheus/workflow-execution-duration-metrics.service.ts`

**但用于计费有六个硬伤**：

| 硬伤 | 说明 |
|---|---|
| **重启清零** | 进程内 counter，n8n 重启归零，总公司必须持续抓取并存储 |
| **多实例各自计数** | multi-main 模式下每个实例各自从 0 开始，需跨实例聚合 |
| **无 executionId 明细** | 账期争议时给不出逐条核查 |
| **无账期对齐** | `increase()` 是基于采样间隔的近似，月度账单有 1-2% 量级误差 |
| **无 workspace 维度** | 标签只有 `workflow_id` / `status` / `mode`，无 `project_id` |
| **数据保留期受限** | Prometheus 本地默认 15 天，月度账单需远程存储（Thanos / Mimir） |

---

## 二、五种方案对比

| 方案 | 实现成本 | 准确性 | 对账能力 | workspace 维度 | 适合场景 |
|---|---|---|---|---|---|
| **A. 给 /metrics** | 极低（改 env） | 中（1-2% 误差） | 弱（无明细） | 需映射 | 总公司已有 Prometheus，容许小误差 |
| **B. 差值计数接口** | 低 | 高 | 中 | 原生支持 | 总公司接受 pull 接口 |
| **C. 账期报表接口** ⭐ | 中 | 极高 | 强（哈希指纹） | 原生支持 | 严肃计费、有对账需求 |
| **D. 主动推送账单** ⭐ | 中 | 极高 | 强（含签名） | 原生支持 | 责任边界要清晰 |
| **E. 明细批量导出** | 高 | 极高 | 极强（逐条） | 原生支持 | 严苛审计场景 |

### 各方案要点

- **方案 A**：开 env 开关，总公司用 Prometheus 抓 `/metrics`。零自研，但有上述六个硬伤
- **方案 B**：你方提供 HTTP 接口，总公司定期 pull 差值。PG 精确 COUNT
- **方案 C**：总公司传时间范围，返回该账期聚合 + 哈希指纹用于一致性校验。推荐用于严肃计费
- **方案 D**：你方定时生成账单主动 POST 给总公司，附 HMAC 签名。推荐用于责任清晰的结算
- **方案 E**：账期内所有 executionId 批量导出，总公司自行汇总。审计场景适用

---

## 三、实现位置（与方案正交）

方案 C/D 的"接口契约"和"部署形态"是两个独立决策。

| 实现位置 | 新增服务？ | 适合方案 | 说明 |
|---|---|---|---|
| **n8n 内部 Webhook Workflow** | ❌ | C | 拖节点即可，享受 n8n 原生认证/日志 |
| **n8n 内部 Schedule Workflow** | ❌ | D | Schedule Trigger 触发推送 |
| **独立微服务容器** | ✅ | C 和 D | docker-compose 加 Node/FastAPI 容器 |

**起步建议**：用 n8n Workflow 实现，不新增服务。

**触发升级到独立服务的信号**：
- 单次查询超过 1 秒
- 需要给多个业务方不同视图
- 需要复杂对账逻辑（哈希、签名）
- webhook workflow 自身的执行记录占用 PG 太多

---

## 四、需要双方商讨的业务规则

> 计费场景下，业务规则比技术实现更重要。**必须在落地前和总公司对齐**。

### 4.1 计费口径

| 规则 | 选项 |
|---|---|
| **失败执行是否计费** | 计 / 不计 / 部分 |
| **手动执行是否计费** | 计 / 不计（业务方调试时点 Test Run 触发的） |
| **重试执行是否计费** | 每次重试都计 / 只计根执行 |
| **运行中/等待中的执行** | 归到哪个账期 |
| **被删除的执行（n8n retention）** | 仍计入 / 不计 |
| **不同 workflow 价格是否不同** | 统一价 / 按 workflow 分档 / 按 node 类型 |

### 4.2 账期与对账

| 规则 | 选项 |
|---|---|
| **账期粒度** | 自然日 / 自然月 / 双方约定 |
| **账期可变性** | 关账后不可改 / 可补单 |
| **数据可重现性** | 同一账期多次拉取必须返回相同数据 |
| **对账窗口** | 关账后多久内可发起核查 |
| **争议处理** | 总公司主张 vs 你方主张，谁出账 |

### 4.3 workspace 维度（如果需要分账）

| 规则 | 选项 |
|---|---|
| **是否按 workspace/部门/客户分账** | 需要 / 不需要 |
| **当前 license 状态** | `.env` 里 `N8N_LICENSE_ACTIVATION_KEY=` 留空 = 全在默认 project |
| **无 license 的替代方案** | 用 workflow 命名前缀（如 `custA-xxx`）或 tag 软分组 |

### 4.4 接入与安全

| 规则 | 选项 |
|---|---|
| **接口形式** | Pull（总公司 GET） / Push（你方 POST） |
| **认证方式** | Basic Auth / API Key / mTLS / HMAC 签名 |
| **网络可达性** | 总公司能否直接访问 Traefik 入口 |
| **限流** | 是否需要防止高频拉取 |
| **数据格式** | JSON / CSV / Parquet |

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

1. **第一步**：与总公司确认第四节业务规则（4.1 计费口径必须先对齐）
2. **第二步**：确认是否需要 workspace 维度 → 决定是否激活 Enterprise License
3. **第三步**：选定方案（建议 C 或 D）+ 选定实现位置（建议先用 n8n Workflow）
4. **第四步**：试点 1 个月，对比总公司 Prometheus 数据和你方接口数据，验证一致性
5. **第五步**：试点通过后正式上线，加签名/审计/告警

---

## 六、参考链接

- n8n Prometheus metrics 配置：
  https://github.com/n8n-io/n8n-docs/blob/main/docs/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/enable-prometheus-metrics.md
- n8n 可视化 metrics 教程：
  https://github.com/n8n-io/n8n-docs/blob/main/docs/deploy/host-n8n/keep-n8n-running/visualize-metrics-with-grafana.md
- n8n 源码（duration metrics）：
  https://github.com/n8n-io/n8n/blob/master/packages/cli/src/metrics/prometheus/workflow-execution-duration-metrics.service.ts
- Prometheus Histogram 规范：
  https://prometheus.io/docs/concepts/metric_types/#histogram
