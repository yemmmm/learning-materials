# Dify 工作流性能分析方案

## 概述

针对 Dify 工作流执行性能瓶颈分析需求，在 Dify 源码中插入了带特定标识 `[PERF_TIMING]` 的性能计时日志，覆盖工作流调用的完整生命周期。

## 版本信息

- 企业版: 3.7.5 → 3.8.0 升级
  - dify-api/dify-web: `3d2aea11a...` → `7a1f0e32580a963404801ca4e7f53afa88db6aea`
  - enterprise 组件: `0.14.4` → `0.15.0`
  - plugin-daemon: `0.5.0-local` → `0.5.3-local`
  - RELEASE_VERSION: `3.7.5 (Docker)` → `3.8.0 (Docker)`
- 开源版: v1.13.0 (容器运行)

## 日志格式

所有性能日志使用 `[PERF_TIMING]` 前缀，格式为 key=value 对，用 ` | ` 分隔：

```
[PERF_TIMING] event=<事件名> | workflow_id=<ID> | workflow_run_id=<ID> | <其他字段>
```

### 日志事件类型

| event | 位置 | 说明 |
|-------|------|------|
| task_enqueue | app_generate_service.py | 请求进入 Celery 队列 |
| task_dequeue | workflow_execute_task.py | Celery 开始处理任务 |
| graph_start | PerformanceTimingLayer | 工作流图开始执行 |
| graph_run_started | PerformanceTimingLayer | 图运行启动 |
| node_start | PerformanceTimingLayer | 节点开始执行 |
| node_succeeded | PerformanceTimingLayer | 节点执行成功 (含 elapsed) |
| node_failed | PerformanceTimingLayer | 节点执行失败 (含 elapsed) |
| llm_invoke_completed | nodes/llm/node.py | LLM 调用完成 (含 latency, TTFT, 生成时间, token 数) |
| graph_run_succeeded | PerformanceTimingLayer | 图运行成功 (含总耗时) |
| graph_run_failed | PerformanceTimingLayer | 图运行失败 |
| graph_end | PerformanceTimingLayer | 图执行结束 |

### LLM 节点特有字段

- `latency`: LLM 调用总延迟
- `time_to_first_token`: 首 token 时间 (TTFT)
- `time_to_generate`: token 生成时间
- `prompt_tokens`, `completion_tokens`, `total_tokens`: token 使用量

## 修改的文件

### 1. 新增文件

#### `api/dify_graph/graph_engine/layers/performance_timing.py`

新建 PerformanceTimingLayer，继承 GraphEngineLayer，通过 `on_graph_start` / `on_event` / `on_graph_end` / `on_node_run_start` / `on_node_run_end` 钩子记录各阶段高精度计时日志。

```python
"""
Performance timing layer for GraphEngine.
"""
import logging
import time
from typing import final

from typing_extensions import override

from dify_graph.graph_events import (
    GraphEngineEvent, GraphRunFailedEvent, GraphRunPartialSucceededEvent,
    GraphRunStartedEvent, GraphRunSucceededEvent,
    NodeRunFailedEvent, NodeRunStartedEvent, NodeRunSucceededEvent,
)
from dify_graph.nodes.base.node import Node
from .base import GraphEngineLayer

logger = logging.getLogger("GraphEngine.PerformanceTiming")


@final
class PerformanceTimingLayer(GraphEngineLayer):

    def __init__(self) -> None:
        super().__init__()
        self._graph_start_time: float | None = None
        self._node_start_times: dict[str, float] = {}
        self._node_count = 0

    @override
    def on_graph_start(self) -> None:
        self._graph_start_time = time.perf_counter()
        logger.info(
            "[PERF_TIMING] event=graph_start | workflow_id=%s | timestamp=%.6f",
            self.graph_runtime_state.workflow_id, self._graph_start_time,
        )

    @override
    def on_event(self, event: GraphEngineEvent) -> None:
        workflow_id = self.graph_runtime_state.workflow_id
        ts = time.perf_counter()

        if isinstance(event, GraphRunStartedEvent):
            logger.info(
                "[PERF_TIMING] event=graph_run_started | workflow_id=%s | timestamp=%.6f",
                workflow_id, ts,
            )
        elif isinstance(event, GraphRunSucceededEvent):
            elapsed = ts - self._graph_start_time if self._graph_start_time else 0
            logger.info(
                "[PERF_TIMING] event=graph_run_succeeded | workflow_id=%s | elapsed=%.6f | node_count=%d",
                workflow_id, elapsed, self._node_count,
            )
        elif isinstance(event, NodeRunStartedEvent):
            self._node_start_times[event.node_id] = ts
            logger.info(
                "[PERF_TIMING] event=node_start | workflow_id=%s | node_id=%s | "
                "node_type=%s | node_title=%s | timestamp=%.6f",
                workflow_id, event.node_id, event.node_type, event.node_title, ts,
            )
        elif isinstance(event, NodeRunSucceededEvent):
            start_ts = self._node_start_times.pop(event.node_id, None)
            elapsed = ts - start_ts if start_ts else 0
            self._node_count += 1
            logger.info(
                "[PERF_TIMING] event=node_succeeded | workflow_id=%s | node_id=%s | "
                "node_type=%s | elapsed=%.6f | timestamp=%.6f",
                workflow_id, event.node_id, event.node_type, elapsed, ts,
            )
        elif isinstance(event, NodeRunFailedEvent):
            start_ts = self._node_start_times.pop(event.node_id, None)
            elapsed = ts - start_ts if start_ts else 0
            logger.info(
                "[PERF_TIMING] event=node_failed | workflow_id=%s | node_id=%s | "
                "node_type=%s | elapsed=%.6f | error=%s",
                workflow_id, event.node_id, event.node_type, elapsed, event.error,
            )
        # ... GraphRunPartialSucceededEvent / GraphRunFailedEvent 同理

    @override
    def on_graph_end(self, error: Exception | None) -> None:
        ts = time.perf_counter()
        total_elapsed = ts - self._graph_start_time if self._graph_start_time else 0
        logger.info(
            "[PERF_TIMING] event=graph_end | workflow_id=%s | total_elapsed=%.6f | "
            "node_count=%d | has_error=%s",
            self.graph_runtime_state.workflow_id, total_elapsed,
            self._node_count, error is not None,
        )

    @override
    def on_node_run_start(self, node: Node) -> None:
        self._node_start_times[node.id] = time.perf_counter()

    @override
    def on_node_run_end(self, node, error=None, result_event=None) -> None:
        pass  # 计时已在 on_event 中通过事件完成
```

> **容器版 (v1.13.0) 差异**: 文件路径为 `/app/api/core/workflow/graph_engine/layers/performance_timing.py`，导入路径从 `dify_graph.*` 改为 `core.workflow.*`。详见 `source-changes/performance_timing_container_v1.13.py`。

---

### 2. 修改文件 — 具体代码变更

#### 2.1 `api/dify_graph/graph_engine/layers/__init__.py`

**变更**: 新增 `PerformanceTimingLayer` 的导入和导出。

```diff
 from .base import GraphEngineLayer
 from .debug_logging import DebugLoggingLayer
 from .execution_limits import ExecutionLimitsLayer
+from .performance_timing import PerformanceTimingLayer

 __all__ = [
     "DebugLoggingLayer",
     "ExecutionLimitsLayer",
     "GraphEngineLayer",
+    "PerformanceTimingLayer",
 ]
```

---

#### 2.2 `api/core/workflow/workflow_entry.py`

**变更 (1)**: 导入行追加 `PerformanceTimingLayer`。

```diff
-from dify_graph.graph_engine.layers import DebugLoggingLayer, ExecutionLimitsLayer
+from dify_graph.graph_engine.layers import (
+    DebugLoggingLayer,
+    ExecutionLimitsLayer,
+    PerformanceTimingLayer,
+)
```

**变更 (2)**: 在 `__init__` 中注册新层（位于 `LLMQuotaLayer` 之后、`ObservabilityLayer` 之前）。

```diff
         self.graph_engine.layer(LLMQuotaLayer())

+        # Add performance timing layer for workflow performance analysis
+        self.graph_engine.layer(PerformanceTimingLayer())
+
         # Add observability layer when OTel is enabled
```

---

#### 2.3 `api/tasks/app_generate/workflow_execute_task.py`

**变更 (1)**: 新增 `import time`。

```diff
 import logging
+import time
 import uuid
```

**变更 (2)**: 在 Celery 任务函数入口添加出队时间日志。

```diff
 @shared_task(queue=WORKFLOW_BASED_APP_EXECUTION_QUEUE)
 def workflow_based_app_execution_task(
     payload: str,
 ) -> Generator[Mapping[str, Any] | str, None, None] | Mapping[str, Any] | None:
+    dequeue_ts = time.perf_counter()
     exec_params = AppExecutionParams.model_validate_json(payload)

+    logger.info(
+        "[PERF_TIMING] event=task_dequeue | workflow_id=%s | workflow_run_id=%s | "
+        "app_id=%s | timestamp=%.6f",
+        exec_params.workflow_id,
+        exec_params.workflow_run_id,
+        exec_params.app_id,
+        dequeue_ts,
+    )
+
     logger.info("workflow_based_app_execution_task run with params: %s", exec_params)
```

---

#### 2.4 `api/services/app_generate_service.py`

**变更 (1)**: 新增 `import time`。

```diff
 import logging
 import threading
+import time
 import uuid
```

**变更 (2)**: 在 Celery 任务入队前记录入队时间（仅 Workflow 模式，约第 216 行）。

```diff
                     def on_subscribe():
+                        enqueue_ts = time.perf_counter()
+                        logger.info(
+                            "[PERF_TIMING] event=task_enqueue | workflow_id=%s | "
+                            "workflow_run_id=%s | app_id=%s | timestamp=%.6f",
+                            workflow.id,
+                            payload.workflow_run_id,
+                            app_model.id,
+                            enqueue_ts,
+                        )
                         workflow_based_app_execution_task.delay(payload_json)
```

---

#### 2.5 `api/dify_graph/nodes/llm/node.py`

**变更**: 在 `handle_invoke_result()` 中，LLM 调用完成后、`yield ModelInvokeCompletedEvent` 之前，插入 LLM 计时日志（约第 519 行）。LLM 的 latency / time_to_first_token / time_to_generate 在原代码中已计算，此处仅追加日志输出。

```diff
         # Calculate streaming metrics
         end_time = time.perf_counter()
         total_duration = end_time - start_time
         usage.latency = round(total_duration, 3)
         if has_content and first_token_time:
             gen_ai_server_time_to_first_token = first_token_time - start_time
             llm_streaming_time_to_generate = end_time - first_token_time
             usage.time_to_first_token = round(gen_ai_server_time_to_first_token, 3)
             usage.time_to_generate = round(llm_streaming_time_to_generate, 3)

+        logger.info(
+            "[PERF_TIMING] event=llm_invoke_completed | node_id=%s | node_type=%s | "
+            "model=%s | latency=%.6f | time_to_first_token=%.6f | "
+            "time_to_generate=%.6f | prompt_tokens=%d | completion_tokens=%d | "
+            "total_tokens=%d",
+            node_id,
+            node_type.value if hasattr(node_type, 'value') else str(node_type),
+            model,
+            usage.latency,
+            usage.time_to_first_token if usage.time_to_first_token else 0,
+            usage.time_to_generate if usage.time_to_generate else 0,
+            usage.prompt_tokens,
+            usage.completion_tokens,
+            usage.total_tokens,
+        )
+
         yield ModelInvokeCompletedEvent(
```

---

### 3. 变更汇总

| # | 文件 | 变更类型 | 说明 |
|---|------|---------|------|
| 1 | `layers/performance_timing.py` | **新增** | PerformanceTimingLayer 完整实现 |
| 2 | `layers/__init__.py` | 2 行 | 导入 + 导出新层 |
| 3 | `core/workflow/workflow_entry.py` | 3 行 | 导入 + 注册层到 GraphEngine |
| 4 | `tasks/.../workflow_execute_task.py` | 10 行 | import time + 出队时间日志 |
| 5 | `services/app_generate_service.py` | 9 行 | import time + 入队时间日志 |
| 6 | `nodes/llm/node.py` | 14 行 | LLM 调用完成后输出计时日志 |

> **容器版 (v1.13.0) 适配**: 上述路径中的 `dify_graph.*` 需替换为 `core.workflow.*`，`NodeType` 导入路径不同，其余逻辑一致。详见 `source-changes/performance_timing_container_v1.13.py` 和 `scripts/deploy_to_container.py`。

## 脚本说明

### collect_perf_logs.py

从 Docker 容器收集 `[PERF_TIMING]` 日志。

```bash
# 从运行中的容器收集
python3 collect_perf_logs.py --output perf_logs.json

# 收集最近1小时的日志
python3 collect_perf_logs.py --since 1h --output recent.json

# 指定容器
python3 collect_perf_logs.py --containers docker-api-1 docker-worker-1

# 从日志文件读取
python3 collect_perf_logs.py --file /var/log/dify.log
```

兼容 Python 3.6+，无第三方依赖。

### analyze_perf_logs.py

分析收集到的性能日志，生成报告和 CSV。

```bash
# 生成文本报告
python3 analyze_perf_logs.py perf_logs.json

# 输出报告到文件
python3 analyze_perf_logs.py perf_logs.json --report report.txt

# 同时生成 CSV (用于进一步分析)
python3 analyze_perf_logs.py perf_logs.json --csv perf_data

# 只显示最慢的5个运行
python3 analyze_perf_logs.py perf_logs.json --top 5
```

输出：
- 文本报告: 各阶段耗时统计 (Avg/Min/Max)
- `*_summary.csv`: 每次运行的总览数据
- `*_nodes.csv`: 每个节点的耗时
- `*_llm.csv`: LLM 调用详细指标

兼容 Python 3.6+，无第三方依赖。

## 部署方式

### 容器环境 (Docker)

```bash
# 1. 复制文件到容器
docker cp performance_timing.py docker-api-1:/app/api/core/workflow/graph_engine/layers/

# 2. 执行修改脚本 (参考 source-changes/ 目录下的完整修改)
docker exec -u root docker-api-1 python3 /tmp/deploy.py

# 3. 重启容器
docker compose restart api worker worker_beat
```

### 源码环境

直接修改源码文件后重启服务即可。

## 性能分析流程

1. **部署** instrumentation 代码到 Dify 容器
2. **执行** 工作流 (可通过压测工具触发)
3. **收集** 日志: `python3 collect_perf_logs.py --since 1h`
4. **分析** 日志: `python3 analyze_perf_logs.py perf_logs.json --report report.txt --csv data`
5. **查看** 报告，定位瓶颈阶段

### 关键指标

- **Queue Wait Time**: 任务在 Celery 队列中的等待时间
  - 如果此值高 → 增加 worker 数量或优化队列配置
- **Node elapsed**: 每个节点的处理时间
  - 对比不同节点找到慢节点
- **LLM TTFT**: 大模型首 token 时间
  - 高 TTFT → 模型服务响应慢或 prompt 过长
- **LLM time_to_generate**: token 生成阶段耗时
  - 与 completion_tokens 对比计算生成速度 (tokens/s)
- **Total elapsed**: 工作流总执行时间

## 注意事项

1. 日志级别需要设置为 INFO 或更低才能看到 PERF_TIMING 日志
2. 容器重启后，直接写入容器的文件会丢失，需要使用 volume 挂载或重新部署
3. Python 3.6 环境只能使用标准库，脚本已确保兼容
4. 源码版 (`dify_graph.*`) 和容器版 (`core.workflow.*`) 的命名空间不同，需使用对应版本
