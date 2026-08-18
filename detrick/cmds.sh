#!/bin/bash
# === Detrick Troubleshoot Round 7 ===
# Time: 2026-08-18 19:00
# Context: 根因已锁定：rbac 服务 check-access 拒绝（已见 app_view_layout denied）。
#          写操作对应权限项 app_access_config。需确认被拒 scene 全集，
#          并在企业管理后台核对用户角色权限分配。
# Cmds: 2 条 + 1 个后台核对步骤

# 1. rbac 拒绝记录按 scene 统计（确认 app_access_config / app_view_layout 等被拒范围）
docker-compose logs --tail=3000 dify-enterprise-rbac 2>&1 | grep 'check-access denied' | grep -oE '"scene" ?: ?"[^"]+"' | sort | uniq -c | sort -rn | head -10

# 2. 最近 10 条该账号的 check-access 明细（时间戳与 console 操作对齐，确认 401 对应 app_access_config 被拒）
docker-compose logs --tail=3000 dify-enterprise-rbac 2>&1 | grep 'check-access' | grep '78e64483' | tail -10

# ===== 后台核对（非命令，决定修复方式）=====
# 登录企业管理后台（dify-enterprise-frontend 对应的 ENTERPRISE_URL 域名，
# 即 Caddyfile 中 CADDY_ENTERPRISE_SITE_ADDR 那个站点）→ 「成员与角色 / Members & Roles」：
#   a. 查看你账号(78e64483)被分配的 RBAC 角色是什么
#   b. 查看该角色的权限项里「应用/App」分类下是否勾选了 访问配置(access config)、
#      查看/编辑 等（对照上面 scene 清单）
#   c. 同时看 owner 账号的角色（解释为什么 owner 看不到功能入口）
