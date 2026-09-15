#!/bin/bash
# === Detrick Troubleshoot: 外部知识库召回页 DatasetQueryListResponse 报错 ===
# Time: 2026-09-15 15:17
# Context: 召回测试页历史接口持续 500，pydantic 报 queries 元素缺 content/content_type、甚至为裸 int；本轮定位响应数据在哪个文件构造、为何缺字段
# Cmds: 3 条（全部只读，无写操作）。在 docker-compose.yaml 所在目录执行。

# 1. api/web/worker 容器镜像 tag 与状态（确认版本是否混杂、是否有半升级迹象）
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep -iE "NAMES|api|web|worker" | head -8

# 2. api 日志中的完整报错堆栈（定位构造 queries 的代码文件与行号）
docker-compose logs --tail=500 --timestamps api 2>&1 | grep -B6 -A26 "validation errors for DatasetQueryListResponse" | tail -42

# 3. dataset_query_contents 表结构（新版代码从该表取 content/content_type，确认表是否存在、字段是否齐全）
docker-compose exec -T db psql -U postgres -d dify -c "\d dataset_query_contents" 2>&1 | head -14
