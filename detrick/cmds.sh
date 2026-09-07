#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 11:14
# Context: Dify 添加外部知识库报 missing dataset_id or pipeline_id in request path，怀疑是 Dify 转发给外部知识库服务的请求路径不对，需从 api 日志确认实际请求 URL 和外部服务返回
# Cmds: 3 条
# 注意：在 Dify 的 docker-compose 目录下执行

# 1. 看 api 容器里这个报错的上下文（谁抛的、请求了什么 URL）
docker-compose logs --tail=1000 api 2>&1 | grep -B8 -A8 -i 'missing dataset_id' | tail -40

# 2. 过滤 api 日志中外部知识库相关的请求/错误（看 actual 请求路径和返回码）
docker-compose logs --tail=1000 api 2>&1 | grep -iE 'external_knowledge|/retrieval|dataset_id|pipeline_id' | tail -20

# 3. 报错发生时的完整 ERROR 日志（带 traceback）
docker-compose logs --since 60m api 2>&1 | grep -iE 'error|exception' | tail -20
