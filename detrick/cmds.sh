#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 14:14
# Context: Dify 压测时 Langfuse 日志同步滞后 1-2 小时，定位是发送端 (Dify API/Worker OTel Exporter) / 网络 / 接收端 (Langfuse 服务) 哪个环节阻塞。第一轮广撒网。
# Cmds: 4 条

# 1. 所有容器状态 + 资源占用快照（找重启/OOM/CPU 或内存打满）
docker-compose ps --format "table {{.Name}}\t{{.Status}}" 2>&1 | head -30 && echo "===STATS===" && docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>&1 | head -30

# 2. Dify API/Worker 最近 1000 行日志中 Langfuse/OTel 相关（找发送报错、重试、超时、批量堆积、队列满）
docker-compose logs --tail=1000 api worker 2>&1 | grep -iE 'langfuse|otel|opentelemetry|trace|exporter' | tail -30

# 3. Dify API 容器内 Langfuse/OTel 环境变量配置（确认 endpoint / batch size / 超时 / 异步队列设置）
docker-compose exec -T api env 2>&1 | grep -iE 'langfuse|otel|trace|exporter' | head -25

# 4. 最近 30 分钟所有服务日志中 Langfuse 相关错误/警告（消费端报错、慢查询、消费滞后、丢消息）
docker-compose logs --since 30m 2>&1 | grep -iE 'langfuse' | grep -iE 'error|warn|slow|lag|queue|timeout|drop|429|500|503' | tail -20
