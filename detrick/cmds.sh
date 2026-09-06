#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 07:00
# Context: 上轮 exec -e 传变量失败（KeyError T）。本轮重写脚本：不依赖环境变量，遍历【全部租户】的全部 app，每租户自动用 owner 作操作者执行官方枚举任务
# Cmds: 15 条（1-14 逐行写脚本，15 运行，16 清理）

# 1-14. 逐行写入修复脚本（每行一条，逐条粘贴执行）
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

# 15. 运行（全部租户全部 app，幂等无害；量大可能跑较久，每个租户会打印一行进度）
docker-compose exec -T api sh -c 'cd /app/api && python -' < /tmp/fix_all.py

# 16. 确认 all-done 后清理临时脚本
rm -f /tmp/fix_all.py /tmp/fix_rbac.py
