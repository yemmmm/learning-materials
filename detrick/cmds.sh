#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-20 16:30
# Context: 上轮重大发现：①命令1 无输出；②命令2 ClickHouse traces/observations/scores 三表 max 时间均为 1970-01-01（**三表全部为空，从未有 trace 写入过**）；③命令4 确认无 langfuse-web 容器。推断：德勤 langfuse web/worker 应用容器没在运行 → Dify 即使发 trace 也连不上 → 表里永远没数据。但用户描述"压测时日志慢同步 1-2 小时" → 与现状矛盾，可能 web/worker 之前在跑、后来挂了，或者用户记忆有误。本轮重点：彻底搞清楚 langfuse web/worker 容器状态（停止了？从未启动？启动失败？）+ 端口监听情况。
# Cmds: 4 条

# 1. langfuse docker-compose 项目下所有服务状态（包括停止的，确认 web/worker 是否存在但被停了）
docker-compose ps -a 2>&1 | head -25

# 2. langfuse docker-compose.yaml 定义的服务清单 + 所有 langfuse 容器（按名字匹配，看 web/worker 是否有但镜像不同名）
docker-compose config --services 2>&1 | head -20
docker ps -a --format "{{.Names}}\t{{.Image}}\t{{.Status}}" 2>&1 | grep -iE 'langfuse' | head -20

# 3. 所有 langfuse 容器（含停止的）详细状态：退出码/错误/启动时间/结束时间（定位 web/worker 为何不在）
docker inspect $(docker ps -aq --filter "name=langfuse") --format '{{.Name}} state={{.State.Status}} exit={{.State.ExitCode}} err={{.State.Error}} started={{.State.StartedAt}} finished={{.State.FinishedAt}}' 2>&1 | head -15

# 4. langfuse web 端口（3001/3000/3030）监听情况 + langfuse docker 网络列表（确认 web/worker 是否在某个网络里跑着）
ss -tlnp 2>&1 | grep -E ':(3001|3000|3030|8123)' | head -10
docker network ls 2>&1 | grep -iE 'langfuse' | head -5
