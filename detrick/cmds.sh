#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-01 17:20
# Context: agent_backend 调模型返回 Squid 错误页，疑似 HTTP_PROXY 劫持模型域名，查 agent_backend 的代理配置和日志
# Cmds: 3 条

# 1. agent_backend 容器内的代理环境变量（确认 http_proxy 是否存在、NO_PROXY 缺了谁）
docker-compose exec -T agent_backend env 2>&1 | grep -iE 'proxy' | head -10

# 2. 对比 api 容器的代理变量（api 调模型正常与否的参照）
docker-compose exec -T api env 2>&1 | grep -iE 'proxy' | head -10

# 3. agent_backend 自己的日志（看它实际请求的模型地址和失败原因）
docker-compose logs --tail=200 agent_backend 2>&1 | tail -30
