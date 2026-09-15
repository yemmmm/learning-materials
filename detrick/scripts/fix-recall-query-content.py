# 修复脚本：dataset_queries.content 旧格式导致召回历史接口 500（根因见 diagnoses/recall-query-validation.md）
# 逻辑：只改"顶层非 JSON 数组"的 content（数字/{'/"/-/true|false|null 开头），包装为
#       [{"content_type":"text","content":<原文>}]，历史记录恢复正常展示。
# 安全：默认 dry-run 只统计；FIX_RECALL_EXECUTE=1 才写库。写库前逐行备份到
#       dataset_queries_bak_20260915（幂等，不重复备份）；修复后行以 [ 开头，重跑无副作用。
# 用法：docker cp 进 api 容器后 python 执行；输出约 6 行。
import os
import sys

import sqlalchemy as sa
from sqlalchemy.engine import URL

url = os.environ.get("SQLALCHEMY_DATABASE_URI")
if not url:
    url = URL.create(
        "postgresql+psycopg2",
        username=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        database=os.environ["DB_DATABASE"],
    )

BAK = "dataset_queries_bak_20260915"
COND = (
    "substring(coalesce(content,'') from 1 for 1) in ('{','\"','-')"
    " or substring(coalesce(content,'') from 1 for 1) between '0' and '9'"
    " or content ~ '^(true|false|null)$'"
)

engine = sa.create_engine(url)
with engine.connect() as c:
    n = c.execute(sa.text(f"select count(*) from dataset_queries where {COND}")).scalar()
    print(f"rows_to_fix={n}")
    if os.environ.get("FIX_RECALL_EXECUTE") != "1":
        print("DRY_RUN_ONLY (set FIX_RECALL_EXECUTE=1 to apply)")
        sys.exit(0)

with engine.begin() as c:
    c.execute(sa.text(f"create table if not exists {BAK} as select * from dataset_queries where false"))
    c.execute(sa.text(
        f"insert into {BAK} select * from dataset_queries d where {COND}"
        f" and not exists (select 1 from {BAK} b where b.id = d.id)"
    ))
    r = c.execute(sa.text(
        "update dataset_queries d"
        " set content = '[{\"content_type\":\"text\",\"content\":' || to_json(d.content)::text || '}]'"
        f" where {COND}"
    ))
    print(f"updated={r.rowcount}")
    rows = c.execute(sa.text(
        "select id, substring(content from 1 for 80) as fixed_head from dataset_queries"
        " where substring(content from 1 for 1) = '[' order by id desc limit 3"
    )).all()
    for row in rows:
        print(dict(row._mapping))
print("FIX_DONE")
