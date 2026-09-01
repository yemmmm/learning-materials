#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-01 17:35
# Context: agent_backend 调模型被 ssrf_proxy(Squid) 拒绝，查被拒域名 + Squid ACL 规则 + 配置文件改动时间
# Cmds: 3 条

# 1. Squid 访问日志（看被 DENIED 的请求和目标域名，复现一次 agent 提问后执行最佳）
docker-compose logs --tail=100 ssrf_proxy 2>&1 | tail -30

# 2. Squid 的 ACL 规则（看允许/拒绝了哪些目标）
docker-compose exec -T ssrf_proxy sh -c 'grep -vE "^#|^$" /etc/squid/squid.conf | head -30'

# 3. 配置文件最近修改时间（定位"某个时间点"改了什么）
ls -l .env docker-compose.yaml ssrf_proxy/squid.conf 2>&1 | head -10
