#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-07 06:00
# Context: 单点修复已验证成功（allowed:true + 页面正常打开）。本轮批量修复：对该租户全部 app 逐个执行官方枚举任务。为防长命令截断，先逐行写脚本文件再执行
# Cmds: 10 条（全部按顺序执行，1-9 是写脚本，10 是运行）

# 1-9. 逐行写入修复脚本（每行一条，逐条粘贴执行）
echo "import os" > /tmp/fix_rbac.py
echo "from app_factory import create_app" >> /tmp/fix_rbac.py
echo "wsgi, app = create_app(); app.app_context().push()" >> /tmp/fix_rbac.py
echo "from extensions.ext_database import db; from models.model import App" >> /tmp/fix_rbac.py
echo "from tasks.initialize_created_app_rbac_access_task import initialize_created_app_rbac_access_task as t" >> /tmp/fix_rbac.py
echo "T=os.environ['T']; A=os.environ['A']" >> /tmp/fix_rbac.py
echo "ids=[str(r[0]) for r in db.session.query(App.id).filter(App.tenant_id==T).all()]; print(len(ids),'apps found')" >> /tmp/fix_rbac.py
echo "[t.apply(args=(T,A,i)) for i in ids]; print('all-done')" >> /tmp/fix_rbac.py

# 10. 运行（对租户内全部 app 执行，幂等、对新应用无害；app 多时可能跑几分钟）
T=e823b48d-382f-43cb-9574-410948f53315; A=dc81582c-3934-4d8f-b034-9cb7809dce2b; docker-compose exec -T -e T -e A api sh -c 'cd /app/api && python -' < /tmp/fix_rbac.py

# 收尾：跑完确认无误后删除临时脚本
rm -f /tmp/fix_rbac.py
