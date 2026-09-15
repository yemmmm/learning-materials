# 只读探针 v2：确认 dataset_queries.content 中非 JSON-list 开头的记录（召回历史接口 500 根因）
# 不 import Dify 模块，直接用容器内环境变量连数据库；仅 SELECT，无写操作。输出约 10 行。
import os

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

engine = sa.create_engine(url)
with engine.connect() as c:
    total, bad = c.execute(sa.text(
        "select count(*),"
        " count(*) filter (where substring(coalesce(content,'') from 1 for 1) <> '[')"
        " from dataset_queries"
    )).one()
    print(f"total={total} not_json_list={bad}")

    rows = c.execute(sa.text(
        "select id, source, substring(coalesce(content,'<NULL>') from 1 for 60) as head"
        " from dataset_queries"
        " where substring(coalesce(content,'') from 1 for 1) <> '['"
        " order by id desc limit 8"
    )).all()
    for r in rows:
        print(dict(r._mapping))
print("PROBE_DONE")
