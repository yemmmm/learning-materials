#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 05:00
# Context: check-access 已 allowed:true，但页面仍报错。本轮定位页面报错的真实来源：是别的 app/scene 被拒，还是 api 层缓存
# Cmds: 2 条（先在页面上刷新复现一次报错，再执行命令）

# 1. 看最近 10 分钟 rbac 拒绝日志（如有新拒绝，看 resource_id/scene 是什么；没有新拒绝说明报错不来自 RBAC）
docker-compose logs --since 10m dify-enterprise-rbac 2>&1 | grep 'check-access denied' | tail -5

# 2. 看 api 容器最近的权限类错误（定位非 RBAC 的报错来源）
docker-compose logs --since 10m api 2>&1 | grep -iE 'forbidden|permission|403' | tail -10
