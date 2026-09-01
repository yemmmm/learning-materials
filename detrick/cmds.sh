#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-01 17:05
# Context: Dify Agent 应用配置了 skills/tools/files 但模型感知不到，查工具是否注入请求 + 相关服务日志
# Cmds: 3 条

# 1. 确认各容器状态是否正常（重点看 api / plugin_daemon）
docker-compose ps --format "table {{.Name}}\t{{.Status}}" 2>&1 | head -20

# 2. api 日志中过滤 agent/skill/tool/error 关键词（看有无静默降级或报错）
docker-compose logs --tail=500 api 2>&1 | grep -iE 'agent|skill|tool|error' | tail -30

# 3. plugin_daemon 最近日志（skill/tool 调用要经过它，挂了会静默失效）
docker-compose logs --tail=100 plugin_daemon 2>&1 | tail -30
