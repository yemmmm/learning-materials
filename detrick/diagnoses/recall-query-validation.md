# 外部知识库召回页 DatasetQueryListResponse 校验失败诊断

状态：根因已定位，待探针确认坏数据样例后做数据修复。影响版本 dify-ee 3.12.1（api/web/worker 同 tag）。

## 现象

召回测试页底部"召回历史"接口 `GET /console/api/datasets/<id>/queries` 持续 500，前端弹 pydantic 校验错误。两类形态交替出现：

- `data.N.queries.0.content_type` / `.content` missing，`input_value={'query_id': 12}`
- `data.N.queries.0` Input should be a valid dictionary，`input_value=123, input_type=int`

任一条坏记录即可让该 dataset 整页历史响应校验失败，因此表现为"持续报错"。

## 证据链

round1 回传（traceback + 镜像 tag）：

- 报错点：`controllers/console/datasets/datasets.py:855` → `return dump_response(DatasetQueryListResponse, response), 200`
- 校验点：`libs/helper.py:213` → `model.model_validate(data, from_attributes=True).model_dump(mode="json")`
- 镜像：`nexus.bmwgroup.net/langgenius/dify-ee-api:3.12.1`（api/worker 同 tag，web 3.12.1），容器 healthy，排除镜像混杂。

本机核对社区版 main 源码（EE 3.12.1 同构）：

- 端点把每行 `DatasetQuery` ORM 包装后交给 pydantic；`queries` 字段来自 `DatasetQuery.get_queries(session)`。
- `get_queries()` 逻辑：`json.loads(self.content)`；解析结果为 list 则补 file_info 后返回；**非 list（dict/裸数字/bool/null/JSON 字符串）走 `else: return [queries]` 原样包裹**；仅 `JSONDecodeError` 才回退为规范 dict。

## 根因

`dataset_queries.content` 历史数据是**纯文本查询词**（旧版格式），新版读取端假设它是 JSON list（`[{"content_type":"text","content":"..."}]`）：

- 纯文本大多数情况 `json.loads` 失败 → 走 fallback → 正常显示，不炸；
- **当查询词本身恰好是合法 JSON 且顶层不是 list**（用户搜过 `123` 这类纯数字词、或形如 `{"query_id":12}` 的文本）→ 解析成功为 int/dict → `else` 分支原样包裹 → pydantic 校验失败 → 500。

两类报错形态与 `else` 分支的两种非 list 值一一对应，判定为官方 3.12.1 读取端缺陷（对旧格式数据缺防御），社区版 main 同样存在该分支行为。

## 写入端同样有缺陷（2026-09-15 补充，决定修复策略）

main 分支（EE 3.12.1 同构）`services/hit_testing_service.py` 有两个写入点：

- 内部知识库 `retrieve()`：`content=json.dumps(dataset_queries)` —— 已写新格式数组；
- **外部知识库 `external_retrieve()`：`content=query` —— 仍写纯文本**，无 content_type 包装。

结论：外部知识库召回测试**新增记录持续产生旧格式数据**，其中"合法 JSON 非 list"的查询词（纯数字最常见）落库即触发读取端 500。仅清洗存量治标不治本，修复必须覆盖增量。

### 修复组合（暂缓执行，方案已备）

| 层 | 方案 | 状态 |
|---|---|---|
| 存量 | `scripts/fix-recall-query-content.py` 清洗脚本（dry-run/备份/幂等） | 已备好未执行 |
| 增量 | DB 触发器兜底（推荐）：BEFORE INSERT 时 content 不以 `[` 开头则包装为规范数组；应用透明、镜像无关、升级不失效。代价：回滚旧版时历史列表显示 JSON 原文 | SQL 预案在下方 |
| 增量备选 | 容器内补丁改 `external_retrieve` 写入格式 | 镜像重建/升级即失效，不推荐 |
| 长线 | 官方 issue：`external_retrieve` 写纯文本 vs `get_queries` 只认数组，main 现状可复现 | 待用户确认后起草 |

触发器预案（外部 DB 执行）：

```sql
create or replace function fix_dataset_query_content() returns trigger as $$
begin
  if substring(coalesce(new.content,'') from 1 for 1) <> '[' then
    new.content := '[{"content_type":"text","content":' || to_json(new.content)::text || '}]';
  end if;
  return new;
end;
$$ language plpgsql;

create trigger trg_fix_dataset_query_content
before insert on dataset_queries
for each row execute function fix_dataset_query_content();
```

## 修复包（已交付，round 4）

脚本 `scripts/fix-recall-query-content.py`（纯 SQLAlchemy 直连，与探针同通道，api 容器内执行）：

- 条件只圈定会触雷的形态：content 以 `{`、`"`、`-`、数字开头，或字面 `true/false/null`（纯文本行走 fallback 不炸，不动）；
- 默认 dry-run 只打印将修复行数；`FIX_RECALL_EXECUTE=1` 才写库；
- 写库前把命中的行逐行备份进 `dataset_queries_bak_20260915`（已存在则不重复备份）；
- 幂等：修复后行以 `[` 开头不再命中条件，重跑无副作用；
- 单事务（engine.begin），失败整体回滚。

如偏好手动 SQL（任意 PG 客户端连外部库执行）：

```sql
-- 预览
select count(*) from dataset_queries
 where substring(coalesce(content,'') from 1 for 1) in ('{','"','-')
    or substring(coalesce(content,'') from 1 for 1) between '0' and '9'
    or content ~ '^(true|false|null)$';
-- 备份（同条件）
create table dataset_queries_bak_20260915 as
  select * from dataset_queries
   where substring(coalesce(content,'') from 1 for 1) in ('{','"','-')
      or substring(coalesce(content,'') from 1 for 1) between '0' and '9'
      or content ~ '^(true|false|null)$';
-- 修复
update dataset_queries
   set content = '[{"content_type":"text","content":' || to_json(content)::text || '}]'
 where substring(coalesce(content,'') from 1 for 1) in ('{','"','-')
    or substring(coalesce(content,'') from 1 for 1) between '0' and '9'
    or content ~ '^(true|false|null)$';
```

## 待办

- [x] 探针确认存在非 JSON 数组 content 记录（round 3 样例行已返回）
- [ ] 回传统计数字与 head 开头形态（可选，不影响修复条件覆盖面）
- [ ] 执行 round 4 修复并页面复验
- [ ] 长期：向官方反馈 get_queries() 对非 list 顶层值缺防御（社区版 main 同样存在）
