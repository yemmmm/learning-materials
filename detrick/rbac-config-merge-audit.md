# Dify RBAC：历史配置合并审计（2026-09-08）

状态：已复现合并风险，尚未证明生产环境根因。没有修改部署、数据库或合并程序。

## 2026-09-08 服务器回传更新

- 两套环境已回传的 DB_DATABASE、DIFY_DB_NAME、ENTERPRISE_DB_NAME 及分库凭据比较一致。当前证据未支持上文复现实验中的“新增 RBAC 落到默认数据库”在生产发生；不能把实验风险继续当作当前根因。
- 异常环境 shared.env 匹配 3.12.0，仅报告缺 ENABLE_LICENSE_EXPIRY_NOTICE。3.12.1 官方说明该变量只控制到期徽标显示，默认启用，不改变许可执行行为；没有依据将它归因于 RBAC 拒绝。
- 其它已回传 enterprise 配置文件与目标版本相容；异常环境 db.env 行及部分比较行未完整回传，不补造结论。
- 异常企业后端 RBAC_INNER_BASE_URL 所在行被截断，API 路径转录呈 /inner/ap1；尚不能区分真实值与转录误差。下一轮用短 JSON 复核，不凭转录文本修改配置。
- 若路由核对正常，应转回具体成员/资源的角色、策略、迁移历史和 RBAC 服务版本差异。MIGRATION_ENABLED=true 不证明历史手工权限迁移已完成。

## 已有服务器证据

- 正常环境为 Enterprise 3.12.0，异常环境为 3.12.1；测试对象均为新增 Agent。
- 两边 RBAC 开启、worker 均订阅 app_rbac；异常环境出现授权初始化任务成功日志，但日志没有 app_id，不能与失败资源关联。
- 受影响账号有 admin 角色和 agent.manage；资源范围 specific，目标账号不在白名单/资源策略中。
- 已回传的关键 Python 源码指纹一致，但不代表 RBAC Go 服务及数据库内策略一致。
- 之前检查 DB_DATABASE 不充分：官方企业 Go 服务还配置 DIFY_DB_NAME、ENTERPRISE_DB_NAME 以及分库凭据。

## 检查范围和来源

实际本地项目：`/home/yangxiang/projects/docker-compose-diff-merge`，远端 https://github.com/yemmmm/docker-compose-diff-merge 。检查标签 v0.1.0、v0.1.1、v0.1.2；保留当前工作区已有的文档修改。

从标签读取 TypeScript，使用本地 TypeScript transpileModule 编译到临时目录执行，不切换项目分支，不安装依赖。使用仓库内 3.8.0、3.9.0、3.10.0、3.11.0、3.12.0、3.12.1 基准。

已重新下载并逐字节验证 3.10.0、3.11.0、3.12.0、3.12.1 的官方根 docker-compose.yaml 和 enterprise core/db/shared/rbac 环境文件，与本地基准一致（3.10 无 rbac.env）。发行包：

`https://langgenius.github.io/dify-enterprise-docker-compose/dify-docker-compose-<version>.tgz`

## 发现一：新增 RBAC 服务未继承自定义数据库名（已复现）

实验使用真实 3.10.0 -> 3.11.0 官方基准：

1. 模拟旧环境中所有已持有 DIFY_DB_NAME 的企业服务统一使用 `corp_dify`；这是合成值，不是生产库名。
2. 旧持有者为 collector、plugin-manager、audit、enterprise；3.10 没有 RBAC 服务。
3. 运行各旧标签的 runThreeWayDiff 和 runExport；该变量生成 user_kept_same_default 条目并按默认 keep 保留。其它冲突指定 keep。
4. 新版使用完整官方 envs 文件，排除“发行包文件本身缺失”干扰。

结果：

| 合并器版本 | enterprise 的 DIFY_DB_NAME | 新 RBAC 的 DIFY_DB_NAME | 根 .env 有对应覆盖 | 未决冲突 / 导出告警 |
|---|---|---|---|---|
| 0.1.0 | corp_dify | dify | 否 | 0 / 0 |
| 0.1.1 | corp_dify | dify | 否 | 0 / 0 |
| 0.1.2 | corp_dify | dify | 否 | 0 / 0 |

对 0.1.2 导出物另用真实 `docker compose config --format json` 展开，退出码 0，并确认同样的两个库名。该检查没有启动任何容器。

原因：保留决策的写入范围仅包括旧环境中的四个持有者，新 RBAC 继续读取官方 envs/enterprise/db.env 中的默认值。这是跨服务的部署语义缺口，不能靠 YAML 有效或导出无告警发现。

额外检查：同一场景在 0.1.3 仍得到相同库名分歧；不能建议仅升级合并器到 0.1.3 就能修复已有部署。

代码证据：v0.1.2 `diff.ts` 生成的 DIFY_DB_NAME 条目 apply.services 不包含新 RBAC；`export.ts` 按该服务集合写 environment，根 .env 没有该覆盖。

**边界：目前没有服务器的 DIFY_DB_NAME/ENTERPRISE_DB_NAME 回传，不能声称生产 RBAC 已连错库；Go 服务实际选用哪个分库还应结合配置和日志判断。**

## 发现二：envs 文件没有随导出交付（已确认代码）

三个旧版本的导出工作流只下载 docker-compose.yaml 与 .env。v0.1.2 `src/components/merge/workbench.tsx:189-196` 可见该行为；没有导出 envs/**。

3.10 开始使用 env_file 架构。如果只替换这两个导出文件，其他 envs 文件仍需按目标发行包更新。文件完全缺失可能直接阻止启动；文件存在但内容旧、或 environment 字面量覆盖正确 env_file 值，可能形成配置漂移。

官方说明：https://ee.dify.ai/releases/v3.10.0/

## 发现三：旧版插值及 env_file 链问题（已复现，但非当前根因证明）

| 输入 | 0.1.0 / 0.1.1 / 0.1.2 | 当前修复代码 |
|---|---|---|
| EMPTY 为空，`${EMPTY:-30}` | 空串 | 30 |
| first.env 定义 BASE=http://rbac:8086，second.env 定义 RBAC_URL=${BASE}/inner/api | /inner/api | http://rbac:8086/inner/api |

代码：各标签 interpolate.ts 的 REF_RE 丢失冒号信息；baseline.ts 解析链值仅使用根 interpEnv，没有累积前面文件的值。

用未经自定义的真实官方基准对照旧/修复渲染器，权限相关服务的 RBAC 开关、RBAC URL、数据库名没有因这两个缺陷变化。enterprise/RBAC 的 ENTERPRISE_URL 有差异。这说明缺陷成立，但不能把所有生产缺失都归因于它们；自定义值及原始上传输入决定是否触发。

## 优先排查项

1. API DB_DATABASE 与 enterprise/RBAC 的 DIFY_DB_NAME，以及 enterprise 与 RBAC 的 ENTERPRISE_DB_NAME 是否一致。异库可能有意配置，需按部署设计判断。
2. 企业服务的 DB_USER/DB_PASS 与 DIFY_DB_USER/DIFY_DB_PASS、ENTERPRISE_DB_USER/ENTERPRISE_DB_PASS 是否仍为旧/出厂配置。不能只查 Python API 的 DB_USERNAME/DB_PASSWORD。
3. ENTERPRISE_API_SECRET_KEY 在 API、enterprise、RBAC 间是否一致；先前仅比较 API/worker 不足。
4. MIGRATION_ENABLED、RBAC_INNER_BASE_URL、WORKSPACE_SYNC_CRON/TIMEOUT 是否有缺失、空值或旧文件覆盖。WORKSPACE_SYNC 名称本身不能证明它负责资源 ACL 同步。
5. envs/enterprise 文件是否与目标发行包一致；自定义文件与官方不同不等于错误，根 .env 或 compose environment 可能提供等效配置。

## 升级历史的独立边界

3.11 的成员角色、知识库权限迁移属于数据库动作，合并环境变量不会代为执行；MIGRATION_ENABLED=true 也不是这些手工迁移已完成的证明。当前不重跑迁移、不重置已有自定义角色。

官方迁移说明：https://ee.dify.ai/releases/v3.11.1/

下一轮执行同目录 cmds.sh 的两条只读命令，正常和异常环境各回传一份结果，再决定是否修复具体配置。不要批量覆盖 .env 或直接全量重跑原权限脚本。
