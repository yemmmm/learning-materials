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

**`api/dify_graph/graph_engine/layers/performance_timing.py`** (源码版)
- 新增 GraphEngineLayer 子类 PerformanceTimingLayer
- 在 node_start/node_succeeded/graph_start/graph_end 等事件中记录时间

**容器版路径**: `/app/api/core/workflow/graph_engine/layers/performance_timing.py`
- 适配 v1.13.0 容器的 `core.workflow.*` 命名空间

### 2. 修改文件

| 文件 | 修改内容 |
|------|---------|
| `api/core/workflow/workflow_entry.py` | 导入并注册 PerformanceTimingLayer |
| `api/tasks/app_generate/workflow_execute_task.py` | 添加 task_dequeue 日志 (记录队列出队时间) |
| `api/services/app_generate_service.py` | 添加 task_enqueue 日志 (记录入队时间) |
| `api/dify_graph/nodes/llm/node.py` | 添加 llm_invoke_completed 日志 (记录 LLM 计时指标) |
| `api/dify_graph/graph_engine/layers/__init__.py` | 导出 PerformanceTimingLayer |

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
