#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 00:06
# Context: 根因基本定位——新版 Go 版 dify-sandbox 在隔离沙箱根目录执行代码，python_path 默认值是 /opt/python/bin/python3；用户自定义过 python_path=/usr/local/bin/python3 导致沙箱内找不到；注释掉后未重启容器，旧配置仍在生效。本轮验证并修复
# Cmds: 4 条
# 注意: 在 dify 部署目录下执行；命令 3 执行完后，去 Dify 界面重新跑一次 code 节点验证

# 1. 确认 sandbox 镜像版本（确认是否为 Go 重写的新版 0.3.x+）
docker inspect --format '{{.Config.Image}}' $(docker-compose ps -q sandbox)

# 2. 确认默认解释器路径 /opt/python/bin/python3 在容器内存在
docker-compose exec -T sandbox ls -l /opt/python/bin/python3 2>&1 | head -5

# 3. 重启 sandbox 让注释掉 python_path 的配置生效（改配置文件不会热加载）
docker-compose restart sandbox

# 4. 重启后确认服务正常起来（状态 Up、无报错）
docker-compose ps sandbox 2>&1 | head -5; docker-compose logs --tail=20 sandbox 2>&1 | tail -10
