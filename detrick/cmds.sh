#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-08-30 23:07
# Context: 上轮 S3 测试脚本执行崩溃（只看到 Node.js v24.16.0 堆栈尾行），怀疑 NODE_PATH 路径不对找不到 @aws-sdk 模块。本轮修测试工具：定位模块路径 + 看完整报错头
# Cmds: 3 条

# 1. 定位 @aws-sdk/client-s3 在镜像里的实际安装路径（判断 NODE_PATH 应该写什么）
docker-compose exec -T n8n-main-1 sh -c 'ls -d /usr/local/lib/node_modules/n8n/node_modules/@aws-sdk/client-s3 2>/dev/null; ls /usr/local/lib/node_modules 2>/dev/null | head -5; which n8n 2>/dev/null' 2>&1 | head -8

# 2. 重跑测试脚本，这次显示报错头部 8 行（上轮 tail -3 把真正的错误截掉了）
docker-compose exec -T n8n-main-1 sh -c 'NODE_PATH=/usr/local/lib/node_modules/n8n/node_modules node /tmp/s3test.js 2>&1 | head -8'

# 3. 确认上轮 heredoc 写入的脚本内容没被终端截断（应看到 3 行 JS 开头）
docker-compose exec -T n8n-main-1 sh -c 'wc -l /tmp/s3test.js 2>/dev/null; head -2 /tmp/s3test.js 2>/dev/null' 2>&1 | head -5
