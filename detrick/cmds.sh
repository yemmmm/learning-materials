#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-01 18:10
# Context: 对比实验——先后问坏/好 Agent 同一问题，抓 15 分钟窗口内日志排除历史残留
# Cmds: 3 条
# 实验步骤：1)记时间问坏Agent 2)记时间问好Agent 3)立刻执行以下命令

# 1. 15 分钟窗口内 api 的报错/agent 相关日志（看坏 Agent 这次运行有没有再次报 AgentBackendRunFailedError）
docker-compose logs --since 15m api 2>&1 | grep -iE 'error|failed' | tail -20

# 2. agent_backend 窗口内日志（过滤掉 XREAD/XADD 轮询噪音，只留真实事件）
docker-compose logs --since 15m agent_backend 2>&1 | grep -viE 'XREAD|XADD|EXPIRE|GET /runs' | tail -25

# 3. 窗口内 Squid 日志（看两次提问各走了哪个模型域名、结果如何）
docker-compose logs --since 15m ssrf_proxy 2>&1 | grep -E 'CONNECT|POST' | tail -10
