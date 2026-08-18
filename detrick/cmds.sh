#!/bin/bash
# === Detrick Troubleshoot Round 15 ===
# Time: 2026-08-18 23:45
# Context: /socket.io 路由正常(200)、api_websocket 健康。工作流画布仍全员卡"同步数据中"。
#          需要定位卡住的到底是 WS 连接还是某个 REST 请求（draft 同步）。
#          操作顺序：先打开一个工作流画布让它卡住 → 保持页面不关 → 立刻执行命令。
# Cmds: 2 条 + F12 抓取

# 1. 画布卡住状态下，api_websocket 是否有新连接/活动（对比打开画布前后的日志变化）
docker-compose logs --tail=30 api_websocket 2>&1 | tail -12

# 2. 主 api 服务中 workflow/draft/sync 相关请求有无报错或长时间处理
docker-compose logs --tail=300 api 2>&1 | grep -iE 'draft|sync|workflow|socket' | grep -iE 'error|fail|timeout|500|401|403' | tail -10

# ===== F12 抓取（画布卡住时，最关键证据）=====
# 浏览器 F12 → Network：
#   a. 筛选 "WS"：socket.io 连接状态是 101（成功）还是一直 pending/failed？
#   b. 筛选 "Fetch/XHR"：找到一直处于 pending（转圈）的那个请求，贴出 URL + Method + 状态
#   c. Console 页签有无红色报错，一并贴出
