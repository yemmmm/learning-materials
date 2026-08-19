#!/bin/bash
# === Detrick Troubleshoot Round 21（强制修复 web 的 Socket URL）===
# Time: 2026-08-19 11:00
# Context: 网关经真实域名握手已返回 200，api_websocket 路由正确；浏览器仍请求
#          ws://console.dify.local，需定位旧值来源并强制让 web 使用生产域名的 wss 地址。
# Cmds: 3 条

# 1. 定位旧值来自宿主机导出变量、配置文件还是现有容器（只显示 Socket URL，不显示其他环境变量）
printf 'host_shell='; printenv NEXT_PUBLIC_SOCKET_URL 2>/dev/null || echo '<unset>'
grep -nH '^NEXT_PUBLIC_SOCKET_URL=' .env envs/core-services/web.env 2>/dev/null | head -10
docker-compose config 2>/dev/null | grep -n 'NEXT_PUBLIC_SOCKET_URL:' | head -5
docker-compose exec -T web sh -c 'printf "container="; printenv NEXT_PUBLIC_SOCKET_URL' 2>&1 | head -3

# 2. 强制修复：备份并更新 .env；在子 shell 中清除宿主机同名变量，避免它覆盖 .env，然后只重建 web
BACKUP_FILE=".env.before-round21-$(date +%Y%m%d-%H%M%S)"
cp -p .env "$BACKUP_FILE"
if grep -q '^NEXT_PUBLIC_SOCKET_URL=' .env; then
  sed -i 's|^NEXT_PUBLIC_SOCKET_URL=.*|NEXT_PUBLIC_SOCKET_URL=wss://lp19dksfai18vm.bmwgroup.net|' .env
else
  printf '\nNEXT_PUBLIC_SOCKET_URL=wss://lp19dksfai18vm.bmwgroup.net\n' >> .env
fi
(unset NEXT_PUBLIC_SOCKET_URL; docker-compose up -d --force-recreate --no-deps web) 2>&1 | tail -12
echo "backup=$BACKUP_FILE"
docker-compose exec -T web sh -c 'printf "container_after="; printenv NEXT_PUBLIC_SOCKET_URL' 2>&1 | head -3

# 3. 浏览器必须丢弃旧前端缓存后复验；新请求必须是 wss://lp19dksfai18vm.bmwgroup.net/socket.io/...
echo '浏览器 F12 -> Network 勾选 Disable cache -> 长按刷新按钮选 Empty Cache and Hard Reload'
echo '重新打开工作流后，回贴：是否仍“同步数据中”、socket.io Request URL、以及第 1/2 条完整输出'
