#!/bin/bash
# ============================================================================
# fix-rbac-workflow-access.sh
# Dify 企业版 3.12.x 「旧应用工作流访问授权」修复脚本
#
# 【适用范围 / SCOPE】
#   版本 : Dify Enterprise 3.12.x（3.12.0 实测验证通过；3.12.1 同架构）
#   症状 : 升级前创建的应用，非 owner 成员打开工作流被拒，rbac 容器日志出现
#          check-access denied: scene=app_view_layout,
#          reason="account is not in the resource whitelist"，
#          且 matched_role_ids 非空（角色绑定正常）
#   根因 : 应用 RBAC whitelist 仅在"创建应用时"写入，<3.11 升级上来的旧应用
#          没有该数据；官方无回填命令。scope=all 是成员快照，必须走 console
#          API 保存才会触发成员枚举任务给全员写授权（inner API 不触发）
#
# 【不适用（先判别再决定是否用本脚本）】
#   1. matched_role_ids 为空数组 → 是成员-角色绑定 bug，先跑：
#      docker-compose exec -T api flask rbac-migrate-member-roles
#      （幂等可反复执行；若报 WORKSPACE_ALREADY_HAS_OWNER 需先处理双 owner）
#   2. 报障账号是 normal 角色 → normal 仅 app.acl.monitor，无
#      app.acl.view_layout，进不了工作流属【设计行为】，需换角色或给角色加权限
#   3. 新建 Agent 应用他人访问被拒 → Agent 默认范围是"特定成员"（设计行为），
#      在应用的企业访问控制里改范围即可
#   判别方法：docker-compose logs --tail=100 dify-enterprise-rbac | grep denied
#
# 【前置条件】
#   - 在 compose 项目目录（如 /global/dockerdata/dify-enterprise-3.12.0）执行
#   - docker-compose V1（带连字符）
#   - single / verify 模式需管理员 console token：控制台 F12 → Network →
#     任一请求 → Request Headers → 复制 Authorization: Bearer 后的整串
#
# 【用法】
#   bash fix-rbac-workflow-access.sh single <APP_ID> <CONSOLE_URL> <TOKEN>
#       修单个应用：console API 重存 whitelist scope=all（触发成员枚举）
#   bash fix-rbac-workflow-access.sh verify <APP_ID> <ACCOUNT_ID>
#       验证：inner API check-access，allowed:true 即修复成功
#   bash fix-rbac-workflow-access.sh batch
#       全量回填：遍历全部租户全部 app，逐个执行官方枚举任务
#       initialize_created_app_rbac_access_task（幂等，对新应用无害）
#
# 【注意】
#   - 本脚本在德勤服务器上经 MobaXterm 粘贴时，建议先粘贴到文件再执行，
#     避免长命令/多行粘贴被静默截断
#   - batch 模式每个租户打印一行进度，应用多时可能跑数分钟
# ============================================================================

set -u
MODE="${1:-}"

usage() { sed -n '2,50p' "$0" | grep -E '^#   (版本|症状|用法|.- )|^#   (single|verify|batch)' ; echo "模式: single|verify|batch"; exit 1; }

inner_check() {
  # 用法: inner_check <TENANT_ID> <ACCOUNT_ID> <APP_ID>
  K='Enterprise-Api-Secret-Key: difyai123456'
  U='http://dify-enterprise-rbac:8086/inner/api/rbac'
  docker-compose exec -T api curl -s -X POST \
    -H "$K" -H "X-Inner-Tenant-Id: $1" -H "X-Inner-Account-Id: $2" \
    -H "Content-Type: application/json" \
    -d "{\"account_id\":\"$2\",\"tenant_id\":\"$1\",\"scene\":\"app_view_layout\",\"resource_type\":\"app\",\"resource_id\":\"$3\"}" \
    "$U/check-access"
}

case "$MODE" in
single)
  [ $# -ne 4 ] && usage
  I="$2"; N="$3"; T="$4"
  echo "[1/3] console API 重存 whitelist scope=all（会触发成员枚举任务）..."
  curl -s -X PUT -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
    -d '{"scope":"all"}' "$N/console/api/workspaces/current/rbac/apps/$I/whitelist"
  echo; echo "[2/3] 等待 20s 异步枚举任务写入授权..."; sleep 20
  echo "[3/3] 完成。请让报障成员刷新页面验证；或用 verify 模式复核。"
  ;;
verify)
  [ $# -ne 3 ] && usage
  I="$2"; A="$3"
  # tenant_id 取应用归属租户：从 api 库查 App 表
  T=$(docker-compose exec -T db psql -U postgres -d dify -At \
    -c "select tenant_id from apps where id='$I'" 2>/dev/null | tr -d '[:space:]')
  [ -z "$T" ] && { echo "查不到 app 的 tenant_id（db 服务或库名不对？）"; exit 1; }
  echo "tenant=$T account=$A app=$I"
  inner_check "$T" "$A" "$I"; echo
  ;;
batch)
  echo "[1/2] 写入回填脚本 /tmp/fix_all.py（逐行写入，防粘贴截断）..."
  echo "from app_factory import create_app" > /tmp/fix_all.py
  echo "wsgi, app = create_app(); app.app_context().push()" >> /tmp/fix_all.py
  echo "from extensions.ext_database import db" >> /tmp/fix_all.py
  echo "from models.model import App" >> /tmp/fix_all.py
  echo "from models.account import TenantAccountJoin" >> /tmp/fix_all.py
  echo "from tasks.initialize_created_app_rbac_access_task import initialize_created_app_rbac_access_task as t" >> /tmp/fix_all.py
  echo "ts=[r[0] for r in db.session.query(App.tenant_id).distinct().all()]; print(len(ts),'tenants')" >> /tmp/fix_all.py
  echo "for tn in ts:" >> /tmp/fix_all.py
  echo "  o=db.session.query(TenantAccountJoin.account_id).filter(TenantAccountJoin.tenant_id==tn, TenantAccountJoin.role=='owner').first()" >> /tmp/fix_all.py
  echo "  op=str(o[0]) if o else ''" >> /tmp/fix_all.py
  echo "  ids=[str(r[0]) for r in db.session.query(App.id).filter(App.tenant_id==tn).all()]" >> /tmp/fix_all.py
  echo "  print(tn, len(ids), 'apps, owner', op)" >> /tmp/fix_all.py
  echo "  for i in ids: t.apply(args=(tn, op, i))" >> /tmp/fix_all.py
  echo "print('all-done')" >> /tmp/fix_all.py
  echo "[2/2] 执行（全部租户全部 app，幂等无害）..."
  docker-compose exec -T api sh -c 'cd /app/api && python -' < /tmp/fix_all.py
  echo "收尾：rm -f /tmp/fix_all.py（确认 all-done 后执行）"
  ;;
*)
  usage
  ;;
esac
