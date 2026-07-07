#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-07 11:31
# Context: 上轮发现 Prometheus targets 5/6 UP、链路通畅，dashboard 数据源配置也正确；本轮验证 dashboard 查询的核心业务指标（n8n_active_workflow_count 等）在 Prometheus 里是否真实存在
# Cmds: 3 条

# 1. 从 Grafana 容器内访问 Prometheus API（验证 Grafana → prometheus:9090 网络是否通、数据源基础是否可用）
docker exec n8n-grafana wget -qO- 'http://prometheus:9090/api/v1/query?query=up' 2>&1 | head -c 500

# 2. 查 Prometheus 里是否有 dashboard 用的核心业务指标（两条 query 一起执行；返回 "result":[] 就说明该指标不存在）
docker exec n8n-prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=n8n_active_workflow_count' 2>&1 | head -c 400 && echo '' && docker exec n8n-prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=n8n_workflow_failed_total' 2>&1 | head -c 400

# 3. 列出 n8n-main-1 /metrics 暴露的所有 n8n_ 指标名（看只有 process_* 系统指标，还是包含 workflow/active_workflow 等业务指标）
docker exec n8n-main-1 wget -qO- http://localhost:5678/metrics 2>&1 | grep -oE '^n8n_[a-z_]+' | sort -u | head -30
