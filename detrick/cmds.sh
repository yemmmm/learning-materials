#!/bin/bash
# === Detrick Troubleshoot Round ===
# Time: 2026-09-08 21:42
# Context: 新问题：无法访问他人创建的Agent；确认当前版本和本次RBAC拒绝原因，尚未判断赋权方式。
# Cmds: 2 条（只读）
# 在服务器当前Compose目录，直接粘贴命令到原shell执行（docker-compose可能是shell函数）。

# 1. 当前Compose容器的服务名及镜像；只看相关服务，最多15行。
docker-compose ps -q | xargs -r docker inspect --format '{{index .Config.Labels "com.docker.compose.service"}} {{.Config.Image}}' | grep -iE 'api|web|enterprise|rbac' | head -15

# 2. 先在浏览器重新打开那个Agent触发拒绝，再立即执行；仅提取权限字段，最多10条。
# 若命令1显示RBAC服务名不同，替换下面的dify-enterprise-rbac。无匹配不能证明权限正常。
docker-compose logs --no-color --since=3m --tail=150 dify-enterprise-rbac 2>&1 | python3 -c '
import sys,re,json
keys="scene|reason|account_id|tenant_id|resource_id|resource_type|account_role_ids|matched_role_ids|whitelist_denial|allowed"
q=chr(34)
pattern=re.compile(q+"("+keys+")"+q+r"\s*:\s*(\[[^\]]*\]|"+q+r"[^"+q+r"]*"+q+r"|true|false|null)")
rows=[]
for line in sys.stdin:
 if not re.search(r"denied|whitelist_denial|unauthorized|forbidden",line,re.I): continue
 fields=dict(pattern.findall(line))
 if fields: rows.append(fields)
for row in rows[-10:]: print(json.dumps(row,ensure_ascii=True))
if not rows: print("NO_MATCH: no extracted RBAC denial; check service name and failed browser request path/status.")
'
