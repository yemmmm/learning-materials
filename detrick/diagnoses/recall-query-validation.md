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

## 修复方向（待探针确认后执行）

数据修复，不改代码。把顶层非 `[` 开头的 content 包装为规范格式，历史记录可恢复显示：

```sql
-- 先备份坏行
create table dataset_queries_bak_20260915 as
  select * from dataset_queries where substring(coalesce(content,'') from 1 for 1) <> '[';
-- 包装为规范 JSON list
update dataset_queries
  set content = '[{"content_type":"text","content":' || to_json(content)::text || '}]'
  where substring(coalesce(content,'') from 1 for 1) <> '[';
```

注意：数据库为外部库，执行通道待确认；执行前需用户确认。

## 待办

- [ ] 探针回传坏数据样例（round 2，脚本 `scripts/recall-query-bad-content-probe.py`）
- [ ] 确认外部 DB 执行通道与备份落位
- [ ] 执行修复 SQL 并页面复验
