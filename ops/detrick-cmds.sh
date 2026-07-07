#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-07 14:59
# Context: dashboard PromQL 已修，但用户重启 grafana 后仍无数据。本轮验证三层：(1) grafana 容器是否真的读到了新 JSON、(2) provisioning 是否加载成功、(3) Grafana → Prometheus 数据源 proxy 是否真的能查到数据
# Cmds: 3 条

# 1. 看 Grafana 日志（找 dashboard provisioning 错误、数据源健康错误、PromQL 查询错误；每行带时间戳）
docker-compose logs --tail=120 grafana 2>&1 | grep -iE 'error|warn|provision|dashboard|datasource|fail|migration' | tail -30

# 2. 验证 grafana 容器内 dashboard JSON 是否真的包含修复后的 PromQL（grep 出现 execution_duration 说明文件是新版；若仍是 workflow_duration/failed_total 说明 git pull 没生效或挂载有问题）
docker exec n8n-grafana grep -oE 'n8n_workflow_(execution_)?(duration_seconds|failed_total)' /var/lib/grafana/dashboards/n8n-ha-overview.json 2>&1 | head -5

# 3. 通过 Grafana 数据源代理调用 Prometheus（这是 Grafana UI 查询走的真实路径；如果这条返回 401/403，说明默认 admin/admin 改过；如果返回 Prometheus 数据，说明数据源完全 OK）
docker exec n8n-grafana wget -qO- --user=admin --password=admin 'http://localhost:3000/api/datasources/proxy/uid/Prometheus/api/v1/query?query=up' 2>&1 | head -c 400
