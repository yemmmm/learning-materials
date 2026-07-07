#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-07 11:39
# Context: 上轮确认 Grafana→Prometheus 网络通、有数据流入；本轮精确验证 dashboard 依赖的 n8n_workflow_* 业务指标是否真的被 n8n 暴露并被 Prometheus 抓到（高度怀疑这些指标默认没开）
# Cmds: 3 条

# 1. 完整列出 n8n-main-1 /metrics 暴露的所有指标名（不 head，看是否有 n8n_workflow_* 系列；如果输出里完全没有 n8n_workflow，那 dashboard 大部分 panel 必然无数据）
docker exec n8n-main-1 wget -qO- http://localhost:5678/metrics 2>&1 | grep -oE '^n8n_[a-z_]+' | sort -u

# 2. 从 Prometheus 侧反查：查所有 n8n_workflow 开头的 metric 名（直接在 Prometheus 数据层确认 workflow 指标是否存在）
docker exec n8n-prometheus wget -qO- 'http://localhost:9090/api/v1/label/__name__/values' 2>&1 | tr ',' '\n' | grep -E 'n8n_workflow|traefik_service' | head -20

# 3. 看 n8n-main-1 容器内实际生效的 N8N_METRICS* 环境变量（确认 compose 配置是否真的传进容器、是否漏开 workflow 指标开关）
docker exec n8n-main-1 env 2>&1 | grep -i '^N8N_METRICS' | head -10
