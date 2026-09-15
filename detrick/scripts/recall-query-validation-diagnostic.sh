#!/bin/bash
# === Detrick Troubleshoot: 外部知识库召回页 DatasetQueryListResponse 报错 (round 3) ===
# Time: 2026-09-15 15:55
# Context: round2 探针因 EE 容器无 app_factory 模块失败；v2 探针改为纯 SQLAlchemy 直连（从容器 env 取 SQLALCHEMY_DATABASE_URI 或 DB_* 变量拼 URL），不 import 任何 Dify 模块
# Cmds: 2 条（只读；若第 1 条 curl 失败说明无 GitHub 通道，改用既有文件传输通道把 recall-query-bad-content-probe.py 放到服务器 /tmp 后只跑第 2 条）

# 1. 取 v2 探针脚本并拷入 api 容器
curl -fsSL https://raw.githubusercontent.com/yemmmm/learning-materials/master/detrick/scripts/recall-query-bad-content-probe.py -o /tmp/recall_probe.py && docker cp /tmp/recall_probe.py dify-enterprise-3120-api-1:/tmp/ && echo COPIED

# 2. 执行只读探针：统计 content 非 JSON-list 记录总数 + 最近 8 条样例
docker exec dify-enterprise-3120-api-1 python /tmp/recall_probe.py
