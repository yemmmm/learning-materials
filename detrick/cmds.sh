#!/bin/bash
# === Detrick Troubleshoot Round 1 ===
# Time: 2026-08-18 15:40
# Context: Dify 3.12.0 企业版，console 选择 web 应用访问权限时报 401，
#          接口 /console/api/enterprise/webapp/app/access-mode 经 Caddy 转发到 dify-enterprise:8082。
#          本轮目标：看企业服务日志中该接口的确切报错原因 + 比对 api 与 dify-enterprise 的镜像版本/密钥/数据源是否一致。
#          注：若 compose 里服务名不是 dify-enterprise / api，先用 docker-compose ps 确认再替换。
# Cmds: 4 条（本轮广撒网定位层级）

# 1. 企业服务日志中该接口的报错（拿确切 reason：token not found / unauthorized / license）
docker-compose logs --tail=500 dify-enterprise 2>&1 | grep -iE 'GetWebAppAccessMode|access-mode|UNAUTHORIZED|token not found' | tail -20

# 2. api 与 dify-enterprise 的镜像版本是否一致（版本偏差会导致 token 校验方式不匹配）
docker inspect --format '{{.Name}}  {{.Config.Image}}  {{.State.StartedAt}}' $(docker-compose ps -q api dify-enterprise) 2>&1 | head -5

# 3. 比对两侧密钥指纹（只输出 md5，不泄露明文；两行 md5 相同=MATCH）
echo "api SECRET_KEY:        $(docker exec $(docker-compose ps -q api) printenv SECRET_KEY | md5sum | cut -d' ' -f1)"
echo "ent DIFY_SECRET_KEY:   $(docker exec $(docker-compose ps -q dify-enterprise) printenv DIFY_SECRET_KEY | md5sum | cut -d' ' -f1)"

# 4. 比对两侧数据源（DB/Redis 是否指向同一实例；enterprise 缺 DB_HOST 说明 compose 漏注入社区库变量）
echo "--- api ---"
docker exec $(docker-compose ps -q api) printenv 2>/dev/null | grep -E '^(DB_HOST|DB_DATABASE|DB_PORT|REDIS_HOST)=' | sort
echo "--- dify-enterprise ---"
docker exec $(docker-compose ps -q dify-enterprise) printenv 2>/dev/null | grep -E '^(DB_HOST|DB_DATABASE|DB_PORT|REDIS_HOST|DIFY_SECRET_KEY)=' | sed 's/DIFY_SECRET_KEY=.*/DIFY_SECRET_KEY=<见上md5>/' | sort
