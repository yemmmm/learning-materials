# Jaeger 分布式链路追踪 — Dify 集成实战

> 本文记录在 Docker 环境下使用 Jaeger v2 对 Dify 服务进行分布式链路追踪的完整步骤。

## 背景

Dify 是一个复杂的 LLM 应用开发平台，包含 API、Worker、Beat、Sandbox、Plugin Daemon 等多个微服务。在生产环境中需要追踪跨服务的请求链路，定位性能瓶颈。Dify 内置了 OpenTelemetry SDK，只需启用配置并部署 Jaeger 即可。

## 架构

```
┌──────────────────────────────────┐       OTLP gRPC       ┌──────────────────────────┐
│  Dify 容器 (docker-compose)       │ ─────────────────────▶ │  Jaeger (container)       │
│  ├─ api (Flask, :5001)           │                        │  ├─ Receiver :4317(gRPC)  │
│  ├─ worker (Celery)              │    docker_default      │  ├─ Receiver :4318(HTTP)  │
│  ├─ worker_beat                  │    共享网络              │  ├─ Query UI :16686       │
│  ├─ plugin_daemon                │                        │  ├─ Badger 持久化存储      │
│  └─ sandbox                      │                        │  └─ Zipkin :9411          │
└──────────────────────────────────┘                        └──────────────────────────┘
```

## 关键版本

| 组件 | 版本 | 说明 |
|------|------|------|
| Jaeger | `jaegertracing/jaeger:2.17.0` | v1 已于 2025.12 EOL，使用 v2 |
| 存储 | Badger (嵌入式) | 轻量级，无需外部数据库 |
| 协议 | OTLP/gRPC | 端口 4317 |
| Dify | 1.13.0 | 内置 OpenTelemetry SDK |

## 步骤 1: 创建 Jaeger 配置文件

`docker/jaeger/config.yaml`:

```yaml
service:
  extensions: [jaeger_storage, jaeger_query, healthcheckv2]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger_storage_exporter]

extensions:
  healthcheckv2:
    use_v2: true
    http:
      endpoint: 0.0.0.0:13133
  jaeger_query:
    storage:
      traces: main_store
  jaeger_storage:
    backends:
      main_store:
        badger:
          directories:
            keys: /badger/key
            values: /badger/data
          ephemeral: false
          ttl:
            spans: 720h  # 保留 30 天

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  jaeger_storage_exporter:
    trace_storage: main_store
```

## 步骤 2: 创建 Docker Compose

`docker/jaeger/docker-compose.yaml`:

```yaml
services:
  jaeger_init:
    image: busybox:latest
    command:
      - sh
      - -c
      - |
        mkdir -p /badger/key /badger/data
        chown -R 10001:10001 /badger
        echo "Jaeger Badger storage initialized."
    volumes:
      - jaeger_badger_data:/badger
    restart: "no"

  jaeger:
    image: jaegertracing/jaeger:2.17.0
    container_name: jaeger
    restart: unless-stopped
    command: ["--config", "/etc/jaeger/config.yaml"]
    volumes:
      - ./config.yaml:/etc/jaeger/config.yaml:ro
      - jaeger_badger_data:/badger
    ports:
      - "16686:16686"   # Jaeger UI
      - "4317:4317"     # OTLP gRPC
      - "4318:4318"     # OTLP HTTP
      - "9411:9411"     # Zipkin 兼容
    depends_on:
      jaeger_init:
        condition: service_completed_successfully
    networks:
      - default
      - docker_default   # 共享 Dify 网络

volumes:
  jaeger_badger_data:

networks:
  default:
    driver: bridge
  docker_default:
    external: true       # 使用 Dify 的已有网络
```

> **关键点**: `docker_default` 必须设为 `external: true`，这样才能与 Dify 容器互通。容器名 `jaeger` 作为 hostname 被 Dify 引用。

> **权限陷阱**: Jaeger 容器以 UID 10001 运行。必须用 `jaeger_init` 预先创建目录并 `chown -R 10001:10001`，否则会报 `permission denied`。

## 步骤 3: 修改 Dify .env 配置

```env
# 启用 OpenTelemetry
ENABLE_OTEL=true

# gRPC 协议指向 Jaeger 的 gRPC 端口
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTLP_BASE_ENDPOINT=http://jaeger:4317

# 显式指定 trace/metric 端点（gRPC 模式下实际使用 BASE_ENDPOINT）
OTLP_TRACE_ENDPOINT=http://jaeger:4317
OTLP_METRIC_ENDPOINT=http://jaeger:4317

# 全量采样（开发/调试用，生产环境改为 0.1）
OTEL_SAMPLING_RATE=1.0

# 批处理配置
OTEL_BATCH_EXPORT_SCHEDULE_DELAY=5000
OTEL_MAX_QUEUE_SIZE=2048
OTEL_MAX_EXPORT_BATCH_SIZE=512
```

> **踩坑记录**: Dify 的 `ext_otel.py` 代码中，gRPC 协议使用 `OTLP_BASE_ENDPOINT` 作为 exporter 的 endpoint（见第 81-86 行）。因此 `OTLP_BASE_ENDPOINT` 必须指向 gRPC 端口 4317，而非 HTTP 端口 4318，否则会报 `StatusCode.UNAVAILABLE`。

## 步骤 4: 启动服务

```bash
# 1. 启动 Jaeger
cd docker/jaeger
docker compose up -d

# 2. 重建 Dify 服务（必须 up -d 而非 restart，否则不会读取 .env 变更）
cd /home/yangxiang/deployed-services/dify/docker
docker compose up -d api worker
```

## 步骤 5: 验证

```bash
# 检查 Jaeger 容器状态
docker ps --filter "name=jaeger"
# 预期: jaeger  Up

# 检查 OTEL 环境变量是否注入
docker exec docker-api-1 env | grep OTEL
# 预期: ENABLE_OTEL=true, OTLP_BASE_ENDPOINT=http://jaeger:4317

# 测试连通性
docker exec docker-api-1 python3 -c "
import socket
s = socket.create_connection(('jaeger', 4317), timeout=3)
s.close()
print('OK')
"

# 查看 Jaeger 接收的服务
curl http://localhost:16686/api/services
# 预期: {"data":["jaeger","langgenius/dify"],...}
```

## 使用 Jaeger UI

1. 打开 http://localhost:16686
2. **Service** 下拉选择 `langgenius/dify`
3. 点击 **Find Traces** 查看所有追踪记录
4. 点击任一 Trace ID 进入火焰图视图：
   - 顶部 **Trace Timeline**: Gantt 图形式展示 Span 时间线（即火焰图）
   - 底部 **Span List**: 树形结构展示父子 Span 关系
   - 可展开/折叠 Span 查看详细属性和耗时

## Dify 采集的操作类型 (17+)

| 类别 | 操作示例 |
|------|---------|
| HTTP 请求 | `GET /health`, `GET /console/api/system-features` |
| Celery 任务 | `run/schedule.workflow_schedule_task.poll_workflow_schedules` |
| 数据库 | `connect`, `SELECT dify` |
| Redis | `PUBLISH`, `SET`, `SADD`, `ZADD HSET`, `EVALSHA`, `ZREVRANGEBYSCORE` |

## 常用命令速查

```bash
# Jaeger 生命周期
cd docker/jaeger && docker compose up -d      # 启动
cd docker/jaeger && docker compose down        # 停止（数据保留在 Volume）
docker logs jaeger                             # 查看日志

# Dify 配置变更后重建
cd /home/yangxiang/deployed-services/dify/docker
docker compose up -d api worker

# 批量导入 trace 文件
curl -X POST http://localhost:16686/api/traces -H "Content-Type: application/json" -d @traces.json
```

## 端口速查

| 端口 | 用途 |
|------|------|
| 16686 | Jaeger Web UI |
| 4317 | OTLP gRPC 接收 |
| 4318 | OTLP HTTP 接收 |
| 9411 | Zipkin 兼容端点 |
| 13133 | 健康检查 |

## 资源清理

```bash
# 完全删除（含存储数据）
cd docker/jaeger && docker compose down -v
```

---

> 创建时间: 2026-06-05
