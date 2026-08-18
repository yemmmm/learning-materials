#!/bin/bash
# === Detrick Troubleshoot Round 8 ===
# Time: 2026-08-18 19:40
# Context: 根因确认——RBAC 判定 "account is not in the resource whitelist"：
#          当前账号不在目标应用(94808e1b)的资源白名单表(resource_whitelist_members)中，
#          导致 app_view_layout / app_access_config 等全部 scene 被拒。
#          剩余疑问：a) 白名单为何缺失（agent 应用创建时未写入?）
#                    b) 为何 UI 无法给成员分配角色（写操作同样失败?）
# Cmds: 2 条 + 2 个 UI 实验

# 1. UI 分配角色失败瞬间的三个服务日志（先在页面操作一次"给成员分配角色"，再立刻执行本条）
docker-compose logs --tail=60 dify-enterprise-rbac 2>&1 | grep -iE 'denied|error|fail|warn' | tail -8
docker-compose logs --tail=60 dify-enterprise 2>&1 | grep -E 'ERROR|"status" ?: ?"?4|"status" ?: ?"?5' | tail -8
docker-compose logs --tail=60 api 2>&1 | grep -iE 'ERROR|error' | tail -8

# 2. rbac 服务最近的完整 WARN/ERROR（看白名单相关还有哪些异常）
docker-compose logs --tail=1000 dify-enterprise-rbac 2>&1 | grep -E '"severity":"(WARN|ERROR)"' | tail -10

# ===== UI 实验一（验证白名单缺失是否 agent 应用特有）=====
# 新建一个普通 Chatbot 应用（基础编排，不进工作流页面），打开"访问权限"尝试修改：
#   成功 → 白名单写入仅对 agent 应用失效，属 3.12.0 bug，直接报企业支持
#   失败 → 所有应用白名单数据都有问题（环境/初始化问题）
#
# ===== UI 实验二（F12 抓"分配角色"失败请求）=====
# Console 或企业管理页尝试给成员分配角色，F12 Network 找失败的请求，
# 贴出：URL、方法、状态码、响应 body
