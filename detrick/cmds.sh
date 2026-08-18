#!/bin/bash
# === Detrick Troubleshoot Round 6 ===
# Time: 2026-08-18 18:20
# Context: INNER_API_KEY 一致（排除密钥问题）；401 为企业服务内部权限判定拒绝。
#          新假设：RESOURCE_GROUP_ENABLED=true 时，资源组准入控制拒绝了未被纳入资源组的
#          Agent 应用写操作（报错措辞 "unauthorized to access this resource" 吻合，
#          且可能同时解释"owner 看不到功能入口"和"工作流同步卡住"）。
#          本轮目标：确认资源组开关状态 + rbac 服务健康 + 资源组相关日志。
# Cmds: 3 条

# 1. 企业服务容器内资源组/日志相关环境变量的实际值（RESOURCE_GROUP_ENABLED 是否为 true）
docker-compose exec -T dify-enterprise sh -c 'printenv | grep -E "^(RESOURCE_GROUP_ENABLED|WEBAPP_PUBLIC_ACCESS_ENABLED|LOG_LEVEL|ENTERPRISE_LICENSE_MODE)="' 2>&1 | head -6

# 2. rbac 容器状态与错误日志（上轮一直没贴到；服务名不同请替换）
docker-compose ps 2>&1 | grep -iE 'rbac' | head -3
docker-compose logs --tail=200 dify-enterprise-rbac 2>&1 | grep -iE 'error|denied|unauthorized|fail|panic' | tail -10

# 3. 企业服务日志中资源组/准入相关记录（有没有 resolve/admission 被拒的痕迹）
docker-compose logs --tail=3000 dify-enterprise 2>&1 | grep -iE 'resource.?group|admission|resolve.?request|release' | tail -10
