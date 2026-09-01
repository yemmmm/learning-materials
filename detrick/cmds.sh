#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-01 17:50
# Context: 模型域名 lp19dksfai07vm.bmwgroup.net 在 Squid 内容器 DNS 被解析成公网 IPv6，对比宿主机/容器解析差异
# Cmds: 3 条

# 1. 宿主机上该域名解析结果（正确的内网 IP 应该是什么）
getent hosts lp19dksfai07vm.bmwgroup.net | head -3

# 2. ssrf_proxy 容器内解析结果（预期会看到错误的公网 IPv6）
docker-compose exec -T ssrf_proxy getent hosts lp19dksfai07vm.bmwgroup.net 2>&1 | head -3

# 3. api 容器内解析结果（确认 api 是否也被污染）
docker-compose exec -T api getent hosts lp19dksfai07vm.bmwgroup.net 2>&1 | head -3
