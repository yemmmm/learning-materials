# 按知识库统计旧格式召回记录（召回历史 500 雷区分布）

关联问题：[diagnoses/recall-query-validation.md](../diagnoses/recall-query-validation.md)。
背景：新版读取端 `get_queries()` 只认 JSON 数组格式的 `dataset_queries.content`；不以 `[` 开头的记录中，"合法 JSON 非 list"的（数字/`{`/引号开头）会触发召回历史接口 500。本查询按知识库分组列出雷区，并区分内部库（`vendor`）与外部库（`external`）。

- 库：Dify 主库（外部 PostgreSQL），表 `dataset_queries`、`datasets`
- 版本验证范围：dify-ee 3.12.1 现场探针同条件已验证可执行
- 性质：只读 SELECT

```sql
select d.provider, q.dataset_id, count(*) as bad_rows
from dataset_queries q join datasets d on d.id = q.dataset_id
where substring(coalesce(q.content,'') from 1 for 1) <> '['
group by d.provider, q.dataset_id
order by bad_rows desc limit 10;
```

解读：

- `provider=external` 且 `bad_rows>0`：持续复发区（写入端仍产旧格式），修复优先；
- `provider=vendor` 且 `bad_rows>0`：存量雷区（新版写入端已改数组，不再新增），清洗即可；
- 总量应与探针 `not_json_list` 统计一致；`bad_rows` 中仅"数字/`{`/引号/`-`/true|false|null 开头"的子集真正触发 500，纯文本行只是旧格式不炸（见诊断文档）。
