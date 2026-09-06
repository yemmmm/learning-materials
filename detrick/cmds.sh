#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 18:00
# Context: curl 用的 key 不对（401），外部库里也没找到 rbac 业务表。本轮查：①rbac 容器完整 DB 环境变量（确定真实库名）②api 容器里真正的 inner key ③rbac 容器挂载（找 config.yaml）
# Cmds: 3 条

# 1. rbac 容器完整环境变量里的 DB 配置（docker inspect，不受容器内缺 shell 影响）
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' $(docker-compose ps -q dify-enterprise-rbac) | grep -iE 'db|database' | head -15

# 2. api 容器所有含 key/token 的环境变量（找真正的 enterprise inner key）
docker-compose exec -T api env | grep -iE 'key|token' | grep -viE 'sentry|public' | head -20

# 3. rbac 容器的挂载点（定位 config.yaml 位置，key 可能写在配置文件里）
docker inspect --format '{{json .Mounts}}' $(docker-compose ps -q dify-enterprise-rbac) | head -c 800
