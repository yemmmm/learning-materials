#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-30 22:31
# Context: 上轮确认 minio:9000 从容器内可达，但 ENDPOINT 配的是 10.190.119.190 且 compose 里疑似写了双等号（KEY==value 导致值带前导=）。本轮验证这两个疑点
# Cmds: 2 条

# 1. 用 cat -A 查看 ENDPOINT 变量值的精确字节（行尾有 $，值开头若显示 =http 说明 yaml 里双等号导致值带前导字符）
docker-compose exec -T n8n-main-1 sh -c 'env | grep S3_ENDPOINT | cat -A' 2>&1 | head -3

# 2. 从 main 容器内测试当前配置的宿主机 IP endpoint 是否可达（OK 则 IP 可用，FAIL 则必须换成 minio:9000）
docker-compose exec -T n8n-main-1 sh -c 'wget -q -T 5 -O /dev/null http://10.190.119.190:9000/minio/health/live && echo "10.190.119.190:9000 OK" || echo "10.190.119.190:9000 FAIL"' 2>&1 | tail -3
