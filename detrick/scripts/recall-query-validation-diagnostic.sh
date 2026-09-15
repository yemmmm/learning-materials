#!/bin/bash
# === Detrick Troubleshoot: 外部知识库召回页 DatasetQueryListResponse 报错 (round 4 - 修复执行) ===
# Time: 2026-09-15 16:10
# Context: 根因已实锤（dataset_queries.content 旧格式非 JSON 数组，新版 get_queries() else 分支原样包裹致 pydantic 500）；本轮执行数据修复：dry-run 预览 → 带备份写入 → 页面复验。写库操作，执行前自行确认
# Cmds: 4 条。若 curl 不通，用既有传输通道把 fix-recall-query-content.py 放到 /tmp 后跳过第 1 条

# 1. 取修复脚本并拷入 api 容器
curl -fsSL https://raw.githubusercontent.com/yemmmm/learning-materials/master/detrick/scripts/fix-recall-query-content.py -o /tmp/fix_recall.py && docker cp /tmp/fix_recall.py dify-enterprise-3120-api-1:/tmp/ && echo COPIED

# 2. dry-run：只统计将修复的行数，不写库
docker exec dify-enterprise-3120-api-1 python /tmp/fix_recall.py

# 3. 确认第 2 步数字无误后执行修复（自动备份到 dataset_queries_bak_20260915，幂等可重跑）
docker exec -e FIX_RECALL_EXECUTE=1 dify-enterprise-3120-api-1 python /tmp/fix_recall.py

# 4. 页面复验：打开该知识库"召回测试"页确认历史列表正常返回（如仍报错，贴 api 日志最近 30 行）
docker-compose logs --tail=200 --timestamps api 2>&1 | grep -c "validation errors for DatasetQueryListResponse" | tail -1
