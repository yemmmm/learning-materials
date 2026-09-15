# 只读探针：确认 dataset_queries.content 中非 JSON-list 开头的记录（召回历史接口 500 根因）
# 用法：拷入 api 容器后 python 执行；仅 SELECT，无写操作。
# 输出约 10 行。
from app_factory import create_app

app = create_app()
with app.app_context():
    from sqlalchemy import text

    from extensions.ext_database import db

    total, bad = db.session.execute(text(
        "select count(*),"
        " count(*) filter (where substring(coalesce(content,'') from 1 for 1) <> '[')"
        " from dataset_queries"
    )).one()
    print(f"total={total} not_json_list={bad}")

    rows = db.session.execute(text(
        "select id, source, substring(coalesce(content,'<NULL>') from 1 for 60) as head"
        " from dataset_queries"
        " where substring(coalesce(content,'') from 1 for 1) <> '['"
        " order by id desc limit 8"
    )).all()
    for r in rows:
        print(dict(r._mapping))
    print("PROBE_DONE")
