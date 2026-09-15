#!/bin/bash
# === Detrick Troubleshoot: 外部知识库召回页 DatasetQueryListResponse 报错 (round 2) ===
# Time: 2026-09-15 15:45
# Context: round2 已确认 3.12.1 EE 代码路径 DatasetQuery.get_queries() 对 content 的 else 分支原样包裹非 list 值；本轮用只读探针确认坏数据样例（预期看到裸数字如 123、或 {"query_id":12} 开头的 content）
# Cmds: 2 条（只读；若第 1 条 curl 失败说明无 GitHub 通道，改用既有文件传输通道把 recall-query-bad-content-probe.py 放到服务器 /tmp 后只跑第 2 条）

# 1. 取探针脚本并拷入 api 容器
curl -fsSL https://raw.githubusercontent.com/yemmmm/learning-materials/master/detrick/scripts/recall-query-bad-content-probe.py -o /tmp/recall_probe.py && docker cp /tmp/recall_probe.py dify-enterprise-3120-api-1:/tmp/ && echo COPIED

# 2. 执行只读探针：统计 content 非 JSON-list 记录总数 + 最近 8 条样例
docker exec dify-enterprise-3120-api-1 python /tmp/recall_probe.py
