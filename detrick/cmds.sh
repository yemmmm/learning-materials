#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-06 00:13
# Context: 已确认 dify-sandbox 0.2.12 源码机制：执行时 chroot 进 /var/sandbox/sandbox-python，根目录内容靠 python_lib_path 配置硬链接进去，默认列表是 python3.10 路径而重打包镜像是 3.12；上轮 404 是因为正确路由是 /v1/sandbox/run。本轮拿原始错误 JSON + 查沙箱根目录
# Cmds: 4 条
# 注意: 在 dify 部署目录下执行；命令 1 的两行在同一个终端会话里先后执行

# 1. 用正确路径直接调 sandbox 执行接口（返回 JSON 里是原始报错）
B='{"language":"python3","code":"print(1)"}'
docker-compose exec -T api curl -s -X POST http://sandbox:8194/v1/sandbox/run -H "X-Api-Key: dify-sandbox" -H "Content-Type: application/json" -d "$B"

# 2. 看沙箱根目录里实际有什么（chroot 后用户代码只能看到这个目录）
docker-compose exec -T sandbox ls /var/sandbox/sandbox-python/ 2>&1 | head -15

# 3. 检查 python3 是不是软链及指向（软链断链会导致 exec 报 no such file）
docker-compose exec -T sandbox ls -la /usr/local/bin/python3 2>&1

# 4. 查 3.12 的 stdlib 实际路径（修复时要写进 python_lib_path 配置）
docker-compose exec -T sandbox /usr/local/bin/python3 -c "import json,sys;print(json.__file__);print(sys.version)" 2>&1
