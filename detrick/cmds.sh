#!/bin/bash
# === Detrick Troubleshoot Round 3 ===
# Time: 2026-08-18 16:35
# Context: 已确认认证正常（多个 console 端企业接口 200），仅写操作 UpdateWebAppWhitelistSubjects
#          返回 401 ErrUnauthorized。用户角色 admin，且 agent 应用为其本人创建。
#          本轮目标：抓 401 前后的完整日志上下文 + 检查 rbac 服务健康 + 企业服务配置。
# Cmds: 3 条

# 1. 401 前后的完整日志上下文（权限判定失败时通常有前置日志说明原因）
docker-compose logs --tail=3000 dify-enterprise 2>&1 | grep -B5 -A2 'UpdateWebAppWhitelistSubjects' | tail -40

# 2. rbac 服务状态与错误日志（企业权限判定可能依赖它；服务名不同请替换）
docker-compose ps 2>&1 | grep -iE 'NAME|rbac|enterprise' | head -8
docker-compose logs --tail=200 dify-enterprise-rbac 2>&1 | grep -iE 'error|denied|unauthorized|fail|panic' | tail -10

# 3. 企业服务配置文件（看日志级别能否调到 debug，以及权限/rbac 相关配置项）
docker-compose exec -T dify-enterprise sh -c 'cat /app/config.yaml 2>/dev/null || cat /config.yaml 2>/dev/null' 2>&1 | head -40
