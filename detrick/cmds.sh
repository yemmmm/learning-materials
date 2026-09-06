#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 16:10
# Context: 迁移已覆盖报障租户、绑定已写入（account_role_ids 非空），剩最后一步：确认角色 d36c6ac4 到底是什么角色、为何不含 app_view_layout。本轮查：①用户工作区角色（修正表名 tenant_account_joins）②rbac 服务数据库配置 ③inner api key
# Cmds: 3 条

# 1. 用你的外部数据库客户端执行（表名修正为 tenant_account_joins）：
select tenant_id, role, current from tenant_account_joins where account_id='dc81582c-3934-4d8f-b034-9cb7809dce2b';

# 2. 看 rbac 服务自己的数据库连接配置（角色数据存在 rbac 的库里，找到 DSN 才能直接查角色名）
docker-compose exec -T dify-enterprise-rbac env | grep -iE 'dsn|postgres|mysql|db_' | head -10

# 3. 从 api 容器环境变量里找 inner api key（下一轮带 key 调角色 API）
docker-compose exec -T api env | grep -iE 'inner|rbac|enterprise' | head -15
