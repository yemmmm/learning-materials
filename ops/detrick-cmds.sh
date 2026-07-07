#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-07 15:20
# Context: 根因已锁定 —— config/grafana/provisioning/ 下目录权限 750 owner=qqaiuto group=docker，容器内 grafana uid=472 gid=0 既不是 owner 也不在 group，走 others 权限完全读不到。修复权限并重启 grafana，看 provisioning 日志确认
# Cmds: 3 条

# 1. 修复权限：给 provisioning 和 dashboards 目录及其下文件加 others 可读+目录可执行（a+rX 大写 X 表示只对目录加 x，文件不加）
chmod -R a+rX config/grafana/provisioning/ config/grafana/dashboards/ && ls -la config/grafana/provisioning/

# 2. 重启 grafana 让 provisioning 重新加载配置
docker-compose restart grafana

# 3. 看 provisioning 日志，应出现 "saved datasource" / "inserted dashboard" 类消息，且无 "permission denied"
docker-compose logs --tail=80 grafana 2>&1 | grep -iE 'provisioning|datasource|dashboard|error|permission' | tail -25
