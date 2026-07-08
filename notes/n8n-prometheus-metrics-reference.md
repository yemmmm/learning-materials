# n8n Prometheus Metrics 完整参考

> 适用版本：n8n 2.x（基于源码 `packages/cli/src/metrics/prometheus/`）
>
> 启用方式：设置 `N8N_METRICS=true`，按需开启 `N8N_METRICS_INCLUDE_*` 子开关。
> Metrics 端点：`GET /metrics`（main 和 worker 实例均可暴露）
>
> 默认前缀：`n8n_`（可用 `N8N_METRICS_PREFIX` 修改）

---

## 一、环境变量开关一览

| 变量 | 默认 | 说明 |
|------|------|------|
| `N8N_METRICS` | `false` | 总开关，启用 `/metrics` 端点 |
| `N8N_METRICS_PREFIX` | `n8n_` | 指标名前缀 |
| `N8N_METRICS_INCLUDE_DEFAULT_METRICS` | `true` | Node.js / 进程级默认指标 |
| `N8N_METRICS_INCLUDE_CACHE_METRICS` | `false` | 缓存命中/未命中 |
| `N8N_METRICS_INCLUDE_MESSAGE_EVENT_BUS_METRICS` | `false` | 事件总线 |
| `N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL` | `false` | **在 workflow 指标上加 `workflow_id` 标签** |
| `N8N_METRICS_INCLUDE_NODE_TYPE_LABEL` | `false` | 在 node 指标上加节点类型标签 |
| `N8N_METRICS_INCLUDE_CREDENTIAL_TYPE_LABEL` | `false` | 在 credential 指标上加凭据类型 |
| `N8N_METRICS_INCLUDE_API_ENDPOINTS` | `false` | 暴露 REST API 端点指标 |
| `N8N_METRICS_INCLUDE_API_PATH_LABEL` | `false` | API 路径标签 |
| `N8N_METRICS_INCLUDE_API_METHOD_LABEL` | `false` | HTTP 方法标签 |
| `N8N_METRICS_INCLUDE_API_STATUS_CODE_LABEL` | `false` | HTTP 状态码标签 |
| `N8N_METRICS_INCLUDE_QUEUE_METRICS` | `false` | BullMQ 队列指标 |
| `N8N_METRICS_QUEUE_METRICS_INTERVAL` | `20` | 队列指标刷新间隔（秒） |
| `N8N_METRICS_INCLUDE_SSRF_METRICS` | `false` | SSRF 防护指标 |
| `N8N_METRICS_INCLUDE_DNS_CACHE_METRICS` | `false` | DNS 缓存指标 |
| `N8N_METRICS_INCLUDE_WORKFLOW_STATISTICS` | `true` | 工作流/用户/凭据总数（实例级） |
| `N8N_METRICS_INCLUDE_WORKFLOW_INFO` | `false` | **暴露 workflow_id → name 映射 Gauge**（n8n ≥ 2.28） |
| `N8N_METRICS_WORKFLOW_STATISTICS_INTERVAL` | `60` | 统计缓存 TTL（秒） |
| `N8N_METRICS_ACTIVE_WORKFLOW_COUNT_INTERVAL` | `60` | 活跃工作流计数缓存 TTL（秒） |
| `N8N_METRICS_WORKFLOW_INFO_METRIC_INTERVAL` | `300` | workflow_info 缓存 TTL（秒） |

---

## 二、Metrics 完整清单（按采集器分组）

### 1. 工作流执行耗时（核心，支持 per-workflow 维度）

**前置：默认启用**；要按工作流维度拆分必须加 `N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL=true`。

| 指标 | 类型 | 标签 | 说明 |
|------|------|------|------|
| `n8n_workflow_execution_duration_seconds` | Histogram | `status` (success/failed), `mode` (manual/trigger/webhook/...), 可选 `workflow_id` | 工作流执行耗时直方图，bucket: 5ms ~ 600s |
| `n8n_workflow_execution_duration_seconds_bucket` |  |  | Histogram bucket 计数 |
| `n8n_workflow_execution_duration_seconds_count` |  |  | **总执行次数**（配合 `workflow_id` 即可做 per-workflow 计数） |
| `n8n_workflow_execution_duration_seconds_sum` |  |  | 总耗时累加 |

**派生 PromQL：**
```promql
# 每个工作流近 5 分钟的执行速率
sum by (workflow_id) (rate(n8n_workflow_execution_duration_seconds_count{workflow_id!=""}[5m]))

# 每个工作流启动以来的总执行次数
sum by (workflow_id) (n8n_workflow_execution_duration_seconds_count{workflow_id!=""})

# 每个工作流 P95 耗时
histogram_quantile(0.95, sum by (le, workflow_id) (rate(n8n_workflow_execution_duration_seconds_bucket{workflow_id!=""}[5m])))

# 成功率
sum by (workflow_id) (rate(n8n_workflow_execution_duration_seconds_count{status="success"}[5m]))
  /
sum by (workflow_id) (rate(n8n_workflow_execution_duration_seconds_count[5m]))
```

### 2. 工作流元信息（ID → 名称映射）

**前置：`N8N_METRICS_INCLUDE_WORKFLOW_INFO=true`（n8n ≥ 2.28.0）**

| 指标 | 类型 | 标签 | 说明 |
|------|------|------|------|
| `n8n_workflow_info` | Gauge | `workflow_id`, `workflow_name` | 值恒为 1，用于 ID → 名称映射 |

**Grafana 用法：** 在 legend 中用 `{{workflow_name}}` 替代 `{{workflow_id}}`，或在 dashboard 变量中用 `label_values(n8n_workflow_info, workflow_name)` 做下拉筛选。

### 3. 活跃工作流计数（默认启用）

| 指标 | 类型 | 标签 | 说明 |
|------|------|------|------|
| `n8n_active_workflow_count` | Gauge | — | 当前 active 状态的工作流总数 |

### 4. 实例级统计（前置：`includeWorkflowStatistics` 默认 true）

**注意：这些都是全局总数，不能按工作流拆分。**

| 指标 | 类型 | 说明 |
|------|------|------|
| `n8n_production_executions` | Gauge | 生产环境执行总数（成功 + 失败） |
| `n8n_production_root_executions` | Gauge | 生产环境根工作流执行总数（不含子工作流） |
| `n8n_manual_executions` | Gauge | 手动执行总数 |
| `n8n_workflows` | Gauge | 工作流总数 |
| `n8n_credentials` | Gauge | 凭据总数 |
| `n8n_users` | Gauge | 用户总数 |
| `n8n_enabled_users` | Gauge | 启用状态用户总数 |

### 5. 队列（BullMQ）指标

**前置：`N8N_METRICS_INCLUDE_QUEUE_METRICS=true`；仅 main 实例 + queue 模式下生效。**

| 指标 | 类型 | 说明 |
|------|------|------|
| `n8n_scaling_mode_queue_jobs_waiting` | Gauge | 当前等待被消费的作业数 |
| `n8n_scaling_mode_queue_jobs_active` | Gauge | 当前正在被 worker 处理的作业数 |
| `n8n_scaling_mode_queue_jobs_completed` | Counter | 自实例启动以来累计完成的作业数 |
| `n8n_scaling_mode_queue_jobs_failed` | Counter | 自实例启动以来累计失败的作业数 |

### 6. REST API 端点指标

**前置：`N8N_METRICS_INCLUDE_API_ENDPOINTS=true`；可用 `INCLUDE_API_PATH_LABEL` / `INCLUDE_API_METHOD_LABEL` / `INCLUDE_API_STATUS_CODE_LABEL` 控制标签维度。**

| 指标 | 类型 | 标签（视开关） | 说明 |
|------|------|------|------|
| `n8n_api_http_request_duration_seconds` | Histogram | `path`, `method`, `status_code` | REST API 请求耗时直方图 |

**典型用例：**
```promql
# P95 API 响应时间（按路径）
histogram_quantile(0.95, sum by (le, path) (rate(n8n_api_http_request_duration_seconds_bucket[5m])))

# 4xx/5xx 错误率
sum by (path) (rate(n8n_api_http_request_duration_seconds_count{status_code=~"4..|5.."}[5m]))
```

### 7. Webhook & Form 指标（默认启用）

| 悉标 | 类型 | 标签 | 说明 |
|------|------|------|------|
| `n8n_webhook_request_seconds` | Histogram | `webhook_id`, `workflow_id` (可选) | Webhook 请求处理耗时 |
| `n8n_form_request_seconds` | Histogram | `form_id`, `workflow_id` (可选) | Form 提交处理耗时 |

### 8. 执行数据大小（默认启用）

| 指标 | 类型 | 说明 |
|------|------|------|
| `n8n_execution_data_size_bytes` | Histogram | 单次执行产生的数据大小，bucket: 1KiB ~ 1GiB |
| `n8n_execution_data_binary_size_bytes` | Histogram | 二进制数据大小 |

### 9. 缓存指标

**前置：`N8N_METRICS_INCLUDE_CACHE_METRICS=true`**

| 指标 | 类型 | 标签 | 说明 |
|------|------|------|------|
| `n8n_cache_hits_total` | Counter | `cache` | 缓存命中次数 |
| `n8n_cache_misses_total` | Counter | `cache` | 缓存未命中次数 |

**派生：** `rate(hits[5m]) / (rate(hits[5m]) + rate(misses[5m]))` → 命中率

### 10. 消息/事件总线指标

**前置：`N8N_METRICS_INCLUDE_MESSAGE_EVENT_BUS_METRICS=true`**

| 指标 | 类型 | 标签 | 说明 |
|------|------|------|------|
| `n8n_eventbus_messages_total` | Counter | `event_name` | 事件总线消息计数 |

### 11. 数据库连接池（默认启用）

| 指标 | 类型 | 说明 |
|------|------|------|
| `n8n_db_pool_size` | Gauge | 连接池当前大小 |
| `n8n_db_pool_available` | Gauge | 空闲连接数 |
| `n8n_db_pool_waiting` | Gauge | 等待获取连接的请求数 |

### 12. 实例角色 & 版本（默认启用）

| 指标 | 类型 | 标签 | 说明 |
|------|------|------|------|
| `n8n_instance_role` | Gauge | `role` (main/worker) | 值为 1，标识实例角色 |
| `n8n_version` | Gauge | `version`, `commit_hash` | 值为 1，标识版本 |

### 13. Token Exchange 指标（默认启用）

| 指标 | 类型 | 说明 |
|------|------|------|
| `n8n_token_exchange_*` | Counter/Gauge | OAuth token 交换相关 |

### 14. SSRF 防护

**前置：`N8N_METRICS_INCLUDE_SSRF_METRICS=true`**

| 指标 | 类型 | 说明 |
|------|------|------|
| `n8n_ssrf_*` | Counter | SSRF 检查拦截次数等 |

### 15. DNS 缓存

**前置：`N8N_METRICS_INCLUDE_DNS_CACHE_METRICS=true`**

| 指标 | 类型 | 说明 |
|------|------|------|
| `n8n_dns_cache_hits_total` | Counter | DNS 缓存命中 |
| `n8n_dns_cache_misses_total` | Counter | DNS 缓存未命中 |

### 16. PSS（Process Startup Snapshot）

| 指标 | 类型 | 说明 |
|------|------|------|
| `n8n_pss_*` | Gauge | 进程启动快照相关 |

### 17. 默认 Node.js 指标（默认启用）

**前置：`N8N_METRICS_INCLUDE_DEFAULT_METRICS=true`**

由 `prom-client` 自动采集，包括但不限于：

| 指标 | 说明 |
|------|------|
| `process_cpu_seconds_total` | 进程 CPU 时间 |
| `process_resident_memory_bytes` | 进程物理内存 |
| `process_heap_*` | V8 堆内存 |
| `process_open_fds` | 打开的文件描述符 |
| `nodejs_eventloop_lag_seconds` | 事件循环延迟 |
| `nodejs_active_handles_total` / `nodejs_active_requests_total` | 活动句柄/请求 |
| `nodejs_gc_duration_seconds` | GC 耗时 |

### 18. AI 实例指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `n8n_instance_ai_*` | Gauge | AI 服务相关 |

---

## 三、推荐的最小启用集（per-workflow 监控）

```bash
# .env
N8N_METRICS=true
N8N_METRICS_INCLUDE_QUEUE_METRICS=true
N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL=true       # 解锁 per-workflow 维度
N8N_METRICS_INCLUDE_WORKFLOW_INFO=true           # 解锁 ID → 名称映射 (n8n ≥ 2.28)
```

按需追加：

```bash
N8N_METRICS_INCLUDE_API_ENDPOINTS=true           # REST API 调用监控
N8N_METRICS_INCLUDE_API_PATH_LABEL=true
N8N_METRICS_INCLUDE_API_STATUS_CODE_LABEL=true
N8N_METRICS_INCLUDE_CACHE_METRICS=true           # 排查缓存命中率
```

---

## 四、常用的 per-workflow Grafana 面板 PromQL

| 面板 | PromQL |
|------|--------|
| **Top 10 工作流执行速率** | `topk(10, sum by (workflow_id) (rate(n8n_workflow_execution_duration_seconds_count{workflow_id!=""}[5m])))` |
| **Top 10 工作流总执行次数** | `topk(10, sum by (workflow_id) (n8n_workflow_execution_duration_seconds_count{workflow_id!=""}))` |
| **每个工作流 P95 耗时** | `histogram_quantile(0.95, sum by (le, workflow_id) (rate(n8n_workflow_execution_duration_seconds_bucket{workflow_id!=""}[5m])))` |
| **每个工作流失败率** | `sum by (workflow_id) (rate(n8n_workflow_execution_duration_seconds_count{status="failed"}[5m])) / sum by (workflow_id) (rate(n8n_workflow_execution_duration_seconds_count[5m]))` |
| **Top 10 工作流平均耗时** | `topk(10, sum by (workflow_id) (rate(n8n_workflow_execution_duration_seconds_sum[5m])) / sum by (workflow_id) (rate(n8n_workflow_execution_duration_seconds_count[5m])))` |

---

## 五、注意事项

1. **`N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL` 默认关闭的原因**：高基数标签，工作流多时会让 Prometheus 时间序列爆炸，按需开启。
2. **`workflow_id` 标签是 UUID 字符串**，需要配合 `n8n_workflow_info` Gauge 把 ID 翻译成名称才能给业务方看。
3. **Queue Metrics 只在 main 上输出**，worker 不会暴露这套指标（源码里有 `instanceType === 'main'` 守卫）。
4. **`/metrics` 端点无认证**，生产环境务必通过反向代理限制内网访问，不要直接暴露到公网。
5. **`n8n_workflow_execution_duration_seconds` 在 worker 上才会被观测**（执行发生在 worker），main 实例上抓到的数据较少。多实例部署需要把所有 main + worker 都加进 Prometheus scrape targets。
6. **Workflow Statistics（`n8n_production_executions` 等）是全局聚合**，不能用来做 per-workflow 计数；只能用来做 license/容量层面的大盘。

---

## 六、参考

- 官方文档：https://docs.n8n.io/hosting/configuration/environment-variables/endpoints/
- 监控指引：https://docs.n8n.io/hosting/logging-and-monitoring/monitor-n8n/
- Grafana 示例：https://docs.n8n.io/hosting/logging-and-monitoring/visualize-metrics-with-grafana/
- 源码目录：`packages/cli/src/metrics/prometheus/` （https://github.com/n8n-io/n8n）
