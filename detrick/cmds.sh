#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 02:00
# Context: 登录接口返回空，怀疑 N 地址/端口不对。本轮：①看 nginx 实际端口 ②带状态码重试登录
# Cmds: 2 条（顺序执行）

# 1. 看 dify 相关容器的端口映射（确认控制台 nginx 是哪个端口）
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -iE 'nginx|gateway|api' | head -10

# 2. 带响应头重试登录（能看到 HTTP 状态码和错误；E/P 换成 admin 邮箱密码，端口按命令 1 结果改 N）
N=http://localhost; E='admin@example.com'; P='password-here'; curl -si -X POST -H "Content-Type: application/json" -d "{\"email\":\"$E\",\"password\":\"$P\",\"remember_me\":true}" "$N/console/api/login" 2>&1 | head -25
