#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-05 23:56
# Context: sandbox 收到 run 请求且返回 200、日志无报错——怀疑错误藏在响应 JSON 体里（sandbox 执行失败仍返回 200），本轮直接手动调用 sandbox run 接口拿原始错误
# Cmds: 4 条
# 注意: 在 dify 部署目录下执行；命令 3 的两行要在同一个终端会话里先后执行

# 1. 看 api 侧代码执行相关环境变量全貌（确认 API_KEY 用哪个值）
docker-compose exec -T api printenv | grep -iE 'CODE_EXEC|SANDBOX' | head -10

# 2. 看 sandbox 容器自身的环境变量（API_KEY / 是否有 PYTHON 相关配置）
docker-compose exec -T sandbox printenv | grep -iE 'API_KEY|PYTHON|SANDBOX' | head -10

# 3. 手动调一次 sandbox 执行接口（两行连着执行，返回的 JSON 里就是原始报错）
K=dify-sandbox
docker-compose exec -T api curl -s -X POST http://sandbox:8194/v1/run -H "X-Api-Key: $K" -H "Content-Type: application/json" -d '{"language":"python3","code":"print(1)"}'

# 4. 看 sandbox 完整配置文件（上一轮 grep 可能过滤太多，这轮看全貌）
docker-compose exec -T sandbox cat /app/conf/config.yaml 2>&1 | head -40
