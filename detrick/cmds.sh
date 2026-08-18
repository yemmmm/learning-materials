#!/bin/bash
# === Detrick Troubleshoot Round 9 ===
# Time: 2026-08-18 20:15
# Context: 官方文档：从 <3.11 升级必须跑 flask rbac-migrate-member-roles 等三个迁移，
#          未完成前"成员除 owner 外无任何权限"——与当前症状完全吻合。
#          3.12.0 启动时会自动 seed agent.manage RBAC 权限，seed 失败也会导致同类症状。
#          本轮目标：确认 a) 企业服务启动时 seed 是否成功  b) 迁移命令存在性与状态  c) rbac 初始化有无异常
# Cmds: 3 条（全部只读，不执行任何迁移）

# 1. 企业服务启动日志中 RBAC/agent.manage 权限 seed 是否成功
docker-compose logs dify-enterprise 2>&1 | grep -iE 'seed|agent\.manage|migrat' | tail -15

# 2. api 容器内 RBAC 迁移命令是否存在（只看帮助文档，不执行迁移）
docker-compose exec -T api flask rbac-migrate-member-roles --help 2>&1 | head -15

# 3. rbac 服务启动/初始化日志（bootstrap-owner、policy seed、同步有无异常）
docker-compose logs dify-enterprise-rbac 2>&1 | grep -iE 'bootstrap|migrat|seed|policy|error|fail' | tail -15

# ===== 请同时回答（决定最终定性）=====
# Q1: 这套环境是全新安装的 3.12.0，还是从旧版本升级？（升级前版本？）
# Q2: 升级时是否执行过 flask rbac-migrate-member-roles / rbac-migrate-dataset-permissions /
#     backfill-plugin-auto-upgrade 三个命令？
