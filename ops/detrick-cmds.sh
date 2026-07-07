#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-07-07 10:55
# Context: webhook-receiver 容器反复重启，定位是否为 OOM 或健康检查失败
# Cmds: 3 条

# 1. 所有容器状态概览（名称 + 当前状态 + 启动时长，定位 webhook-receiver 是否在频繁重启）
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.RunningFor}}" 2>&1 | head -20

# 2. webhook-receiver 的重启次数 / 退出码 / OOM 标记（核心判断：是 OOM kill 还是应用退出）
docker inspect --format '{{.Name}} restart={{.RestartCount}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} health={{.State.Health.Status}}' $(docker-compose ps -q webhook-receiver) 2>&1 | head -10

# 3. 最近 200 行日志中的 error/fatal/oom/panic（应用层错误线索）
docker-compose logs --tail=200 webhook-receiver 2>&1 | grep -iE 'error|fatal|oom|panic|exception' | tail -15
