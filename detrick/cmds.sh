#!/bin/bash
# === Detrick Troubleshoot Round 5 ===
# Time: 2026-08-18 17:45
# Context: DIFY_ENDPOINT=http://api:5001 配置正确；401 前无任何报错日志（只有 GetCurrentWorkspace 成功记录）。
#          上轮 api 侧 INNER_API_KEY md5、连通性探测、api 日志 inner 记录三处输出被截断，本轮补齐。
#          新线索：企业服务写操作权限依赖"应用编辑者(AppEditor)同步数据"，同步断链也会导致 Update 401。
# Cmds: 3 条（均为上轮截断项补跑）

# 1. 两侧 INNER_API_KEY 指纹比对（两条 md5 相同=匹配；上轮 api 侧输出被截断）
echo "ent INNER_API_KEY: $(docker-compose exec -T dify-enterprise printenv DIFY_INNER_API_KEY | md5sum | cut -d' ' -f1)"
echo "api INNER_API_KEY: $(docker exec $(docker-compose ps -q api) printenv INNER_API_KEY | md5sum | cut -d' ' -f1)"

# 2. 企业服务容器内探测回调地址连通性（上轮未贴；连不上=回调链路断）
docker-compose exec -T dify-enterprise sh -c 'wget -qO- -T 5 http://api:5001/health 2>&1 || curl -s -m 5 http://api:5001/health 2>&1' 2>&1 | head -5

# 3. api 日志中 inner 请求记录（enterprise→api 的回调有没有到达、状态码；上轮未贴）
docker-compose logs --tail=1000 api 2>&1 | grep -iE 'inner' | tail -10

# ===== 另外请完成两个零成本对照实验（不需要命令，结果直接决定结论）=====
# 实验 A：用 admin 新建一个普通应用（chatbot，非 Agent），打开"访问权限"尝试修改：
#         成功 → Agent 应用类型的权限同步 bug；失败 → 环境链路问题
# 实验 B：浏览器 F12 → Network，重放失败的 access-mode/whitelist 请求，
#         贴出：完整请求 URL、请求方法(PUT/POST?)、响应 body 全文
