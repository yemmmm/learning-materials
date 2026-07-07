#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-07 15:10
# Context: Grafana 日志暴露根因：provisioning.datasources / dashboards 目录 permission denied，导致 prometheus.yml 没被加载、Grafana 里没建 Prometheus 数据源。本轮验证权限链路（宿主机权限 + 容器内权限 + Grafana 用户 uid）
# Cmds: 3 条

# 1. 看 Grafana provisioning 完整错误（不截断关键消息，特别是 datasource provisioning 的完整错误）
docker-compose logs --tail=200 grafana 2>&1 | grep -iE 'provisioning\.datasources|provisioning\.dashboard|permission denied|can.t read|failed to read' | head -20

# 2. 看宿主机上 provisioning 相关目录和文件的所有者 + 权限（重点：目录是否可被 grafana 容器内 uid 472 读取）
ls -la config/grafana/provisioning/ config/grafana/provisioning/dashboards/ config/grafana/provisioning/datasources/ 2>&1

# 3. 看容器内 grafana 进程的 uid + 它视角下 provisioning 文件的权限（最关键 —— 这是实际报错路径）
docker exec n8n-grafana sh -c 'id; ls -la /etc/grafana/provisioning/ /etc/grafana/provisioning/datasources/ /etc/grafana/provisioning/dashboards/' 2>&1 | head -25
