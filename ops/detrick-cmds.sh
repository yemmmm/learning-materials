#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-07 11:15
# Context: Grafana dashboards 无数据，从数据链路 Prometheus → n8n /metrics 着手，确认是抓取失败还是 n8n 没开 metrics
# Cmds: 3 条

# 1. 查 Prometheus 各 scrape target 的健康状态和最近一次错误信息（最关键，一眼看出哪些 target 是 DOWN、为什么 DOWN）
docker exec n8n-prometheus wget -qO- 'http://localhost:9090/api/v1/targets' 2>&1 | grep -oE '"scrapeUrl":"[^"]*"|"health":"[^"]*"|"lastError":"[^"]*"' | head -40

# 2. 直连 n8n 主节点 /metrics，确认 n8n 是否真的暴露了 n8n_ 指标（输出空或 404 说明 metrics 端点没数据）
docker exec n8n-main-1 wget -qO- http://localhost:5678/metrics 2>&1 | head -5

# 3. 看 Grafana / Prometheus / n8n 相关容器状态（确认服务都在跑、没在重启）
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.RunningFor}}" 2>&1 | grep -iE 'grafana|prometheus|n8n|traefik|redis' | head -15
