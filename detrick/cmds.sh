#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-05 23:38
# Context: Dify code 节点报错找不到 /usr/local/bin/python3，但用户进 sandbox 容器能看到该文件——确认 API 实际调用的是哪个 sandbox、其配置的 python 路径与可执行性
# Cmds: 4 条
# 注意: docker-compose 命令需在 dify 部署目录（含 docker-compose.yaml 的目录）下执行

# 1. 列出服务器上所有 sandbox 相关容器（查是否存在多个/旧 sandbox，API 可能调的是另一个）
docker ps -a --format "{{.Names}}|{{.Image}}|{{.Status}}" | grep -i sandbox | head -10

# 2. 查当前 compose 项目 sandbox 容器内生效的 python 路径配置（env_path 指向哪里）
docker-compose exec -T sandbox cat /app/conf/config.yaml 2>&1 | grep -A5 -iE 'python|worker' | head -20

# 3. 在 sandbox 容器内实际执行该路径（文件存在不等于可执行，看权限/软链/报错）
docker-compose exec -T sandbox sh -c 'ls -l /usr/local/bin/python*; /usr/local/bin/python3 -V' 2>&1 | head -10

# 4. 查 sandbox 最近日志中与 python 相关的完整报错（拿到原始错误栈）
docker-compose logs --tail=300 sandbox 2>&1 | grep -iE 'python|no such|error' | tail -20
