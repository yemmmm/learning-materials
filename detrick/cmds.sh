#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 21:30
# Context: 根因已实锤——旧应用缺少 RBAC whitelist（仅创建时可写入），官方无回填命令。本轮对报障 app 60a56261 单点验证修复：PUT /inner/api/rbac/apps/whitelist scope=all
# Cmds: 3 条（顺序执行，1 必须先跑，变量在同一终端会话内生效）

# 1. 先设置变量（在同一终端里执行，后续命令依赖）
T=e823b48d-382f-43cb-9574-410948f53315; A=dc81582c-3934-4d8f-b034-9cb7809dce2b; I=60a56261-fd3c-47cc-8f63-ad40adee61cf; echo vars-ok

# 2. 读取该应用当前 whitelist（无副作用，验证鉴权头是否通过；返回 JSON 即成功）
docker-compose exec -T api curl -s -H "Enterprise-Api-Secret-Key: difyai123456" -H "X-Inner-Tenant-Id: $T" -H "X-Inner-Account-Id: $A" "http://dify-enterprise-rbac:8086/inner/api/rbac/apps/whitelist?app_id=$I"

# 3. 【修复】将该应用 whitelist 设为 scope=all（等价于新建应用时的默认授权）。执行后用普通账号打开该工作流验证
docker-compose exec -T api curl -s -X PUT -H "Enterprise-Api-Secret-Key: difyai123456" -H "X-Inner-Tenant-Id: $T" -H "X-Inner-Account-Id: $A" -H "Content-Type: application/json" -d '{"scope":"all"}' "http://dify-enterprise-rbac:8086/inner/api/rbac/apps/whitelist?app_id=$I"
