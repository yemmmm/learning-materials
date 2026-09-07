# Dify 3.12(EE) 升级后模型凭证不可见排查笔记

- 日期:2026-09-07
- 环境:德勤服务器(主)/本机 dify 1.13.0 EE(代码参照,同一套凭证架构)
- 现象:升级 3.12.0 后,模型列表中点模型的 config 无法选择旧 credential,只能新增;provider 的 manage credential 报 `credential with id xxxxx not found`;但工作流调用原模型正常

## 根因:凭证存储架构变更 + 两条查询路径过滤条件宽严不一致

3.12(本机对应社区版 1.13.0)把模型凭证从 `providers.credentials` JSON 列迁移为独立表:

| 层级 | 新表 | 关联 |
|---|---|---|
| provider 级 | `provider_credentials` | `providers.credential_id` 指向它 |
| model 级 | `provider_model_credentials` | `provider_models.credential_id` 指向它 |

关键代码路径(容器内 `/app/api/`):

1. **运行时(工作流)** — `models/provider.py:96` `Provider.credential` 只按 `id` 查,不过滤 provider_name → 只要 credential_id 还指向那行,模型照常工作。
2. **控制台取凭证** — `core/entities/provider_configuration.py:233-243` `_get_specific_provider_credential` 严格过滤 `ProviderCredential.provider_name == provider记录的名称`,不匹配即抛 `Credential with id {id} not found`。
3. **凭证下拉列表** — `core/provider_manager.py:532` `get_provider_available_credentials` 按 provider_name 两种别名(`openai` / `langgenius/openai/openai`)过滤。

→ **工作流正常 + UI 报 not found + 列表看不见** 同时成立,说明大概率是升级数据迁移后:

- `providers.provider_name` 与 `provider_credentials.provider_name` 形式不一致(一边短名一边全名),或
- `providers.credential_id` 悬空指向不存在的行(迁移只跑了一半 / alembic 未到 head)

## 德勤环境取证命令(每条短单行,MobaXterm 安全)

容器名按实际调整(假设 postgres 容器为 `db_postgres`):

```bash
docker ps --format '{{.Names}}' | grep -i db
docker exec db_postgres psql -U postgres -d dify -c "select version_num from alembic_version"
docker exec db_postgres psql -U postgres -d dify -c "select count(*) from provider_credentials"
docker exec db_postgres psql -U postgres -d dify -c "select provider_name,credential_name from provider_credentials"
docker exec db_postgres psql -U postgres -d dify -c "select provider_name,credential_id from providers where credential_id is not null"
```

悬空引用排查(重点):

```bash
docker exec db_postgres psql -U postgres -d dify -c "select p.provider_name, p.credential_id from providers p where not exists (select 1 from provider_credentials c where c.id = p.credential_id)"
```

名称形式不一致排查(重点):

```bash
docker exec db_postgres psql -U postgres -d dify -c "select p.provider_name as p_name, c.provider_name as c_name from providers p join provider_credentials c on c.id = p.credential_id where p.provider_name <> c.provider_name"
```

按报错里的 id 直查:

```bash
docker exec db_postgres psql -U postgres -d dify -c "select * from provider_credentials where id = 'xxxxx'"
```

MySQL 环境把 `psql -U postgres -d dify -c` 换成 `mysql -uroot -p密码 dify -e`,SQL 不变。

## 修复方向(确认是哪种情况后)

- 名称不一致 → UPDATE `provider_credentials.provider_name` 对齐 `providers.provider_name`(以 UI 正常显示的 provider 全名为准)
- 悬空引用 → 从 `providers.credentials` 旧数据(若有备份库)补插 `provider_credentials` 行并回填 `credential_id`;或界面上重新录入凭证后 switch
- model 级同理排查 `provider_model_credentials`

## 关联

- 德勤终端长粘贴会被静默截断,排查命令必须短小单行(见 detrick 笔记)
- 本机参照实例:dify/docker compose 项目,API 1.13.0,DB 为 db_postgres/dify
