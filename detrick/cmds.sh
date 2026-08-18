#!/bin/bash
# === Detrick Troubleshoot Round 4 ===
# Time: 2026-08-18 17:10
# Context: 认证正常，仅写操作 401。config.yaml 显示企业服务会回调社区 api
#          （DIFY_ENDPOINT + DIFY_INNER_API_KEY）做权限判定。
#          本轮目标：验证 enterprise→api 回调的地址、密钥、连通性是否正常，
#          并补上轮缺失的 401 上下文日志。
# Cmds: 4 条

# 1. 补上轮关键缺失：401 前后的完整日志上下文（权限判定失败的前置原因）
docker-compose logs --tail=3000 dify-enterprise 2>&1 | grep -B5 -A2 'UpdateWebAppWhitelistSubjects' | tail -40

# 2. 企业服务回调地址实际值 + 两侧 INNER_API_KEY 指纹比对（只出 md5；两行相同=匹配）
docker-compose exec -T dify-enterprise printenv DIFY_ENDPOINT DIFY_CONSOLE_API_URL DIFY_INNER_API_KEY 2>/dev/null | sed -n '1,2p'
echo "ent INNER_API_KEY: $(docker-compose exec -T dify-enterprise printenv DIFY_INNER_API_KEY | md5sum | cut -d' ' -f1)"
echo "api INNER_API_KEY: $(docker exec $(docker-compose ps -q api) printenv INNER_API_KEY | md5sum | cut -d' ' -f1)"

# 3. 从企业服务容器内探测回调地址连通性（连不上=实锤）
docker-compose exec -T dify-enterprise sh -c 'wget -qO- -T 5 "$DIFY_ENDPOINT/health" 2>&1 || curl -s -m 5 "$DIFY_ENDPOINT/health" 2>&1' 2>&1 | head -5

# 4. api 日志中 inner 回调记录（enterprise→api 方向的请求有没有到达、状态码多少）
docker-compose logs --tail=1000 api 2>&1 | grep -iE 'inner' | tail -10
