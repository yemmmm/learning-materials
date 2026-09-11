# 德勤封闭环境定位资料

配合 `detrick-troubleshoot` skill 使用。按用途存放命令、证据、查询及历史方案；问题状态以各文档和记录中的最后确认结果为准。

## 从哪里开始

| 用途 | 入口 | 使用说明 |
|---|---|---|
| 本轮排查命令 | [scripts/current-round.sh](scripts/current-round.sh) | SSO 邀请已有用户出现 pending、移除后 workspace 丢失：只读核对账户身份与成员关系。原 n8n HTTPS/CA 问题仍暂停、未解决，历史探针见 Git 历史 |
| 环境与执行约束 | [records/environment.md](records/environment.md) | 区分现场回传、本机实测和历史事实 |
| 问题时间线 | [records/issues.md](records/issues.md) | 保留证据、结论变化和未完成事项 |
| 工作空间角色查询 | [queries/workspace-member-roles.md](queries/workspace-member-roles.md) | 原 cmds.md；已关闭，保留已核对的 RBAC 表结构及 SQL |
| Agent 访问诊断 | [diagnoses/agent-access-diagnosis.md](diagnoses/agent-access-diagnosis.md) | 本轮已关闭，单点恢复不代表全量授权完成 |
| Completion 提示词诊断 | [diagnoses/completion-prompt-diagnosis.md](diagnoses/completion-prompt-diagnosis.md) | 专项证据和最小复现；验收边界见正文 |
| WebApp 401 复盘 | [diagnoses/webapp-access-mode-diagnosis.md](diagnoses/webapp-access-mode-diagnosis.md) | 已确认修复的 API/Enterprise RBAC 开关问题 |
| RBAC 配置合并审计 | [diagnoses/rbac-config-merge-audit.md](diagnoses/rbac-config-merge-audit.md) | 历史实验风险，不等于现场根因 |
| 旧工作流授权脚本 | [scripts/fix-rbac-workflow-access.sh](scripts/fix-rbac-workflow-access.sh) | 含写操作；使用前核对脚本适用范围及模式 |
| 单 Agent 成员授权脚本 | [scripts/grant-agent-member-access.sh](scripts/grant-agent-member-access.sh) | 含写操作，限定目标与角色；不作为通用批量授权 |
| 已撤回的源码补丁 | [archive/agent-content-access-fix/README.md](archive/agent-content-access-fix/README.md) | 仅供追溯，不执行准备、安装或重启步骤 |

## 文件约定

- `scripts/`：排查与修复脚本；执行前阅读用途、目标、状态，区分只读探针与写操作。
- `records/`：持续维护的环境事实和问题记录。
- `diagnoses/`：按问题命名的诊断、复盘、审计文档。
- `queries/`：可复用的数据库查询说明，注明库、版本和验证范围。
- `archive/`：已撤回方案及其完整附件，保留历史证据。
- 新文档使用主题名称，不再新建含义不明的 `cmds.md`。并行问题需要独立命令文件时，使用 `scripts/<问题名>-diagnostic.sh`，避免覆盖其他会话。
- 关闭、暂停与撤回保持区别；归档或目录整理不改变问题状态。

## 2026-09-10 路径迁移

| 原路径（相对 detrick/） | 新路径 |
|---|---|
| `cmds.md` | [queries/workspace-member-roles.md](queries/workspace-member-roles.md) |
| `cmds.sh` | [scripts/current-round.sh](scripts/current-round.sh) |
| `environment.md` | [records/environment.md](records/environment.md) |
| `issues.md` | [records/issues.md](records/issues.md) |
| `fix-rbac-workflow-access.sh` | [scripts/fix-rbac-workflow-access.sh](scripts/fix-rbac-workflow-access.sh) |
| `grant-agent-member-access.sh` | [scripts/grant-agent-member-access.sh](scripts/grant-agent-member-access.sh) |
| `agent-content-access-fix` | [archive/agent-content-access-fix](archive/agent-content-access-fix/README.md) |
| `webapp-access-mode-diagnosis.md` | [diagnoses/webapp-access-mode-diagnosis.md](diagnoses/webapp-access-mode-diagnosis.md) |
| `completion-prompt-diagnosis.md` | [diagnoses/completion-prompt-diagnosis.md](diagnoses/completion-prompt-diagnosis.md) |
| `agent-access-diagnosis.md` | [diagnoses/agent-access-diagnosis.md](diagnoses/agent-access-diagnosis.md) |
| `rbac-config-merge-audit.md` | [diagnoses/rbac-config-merge-audit.md](diagnoses/rbac-config-merge-audit.md) |

历史记录中的旧文件名与固定提交链接保留当时含义；查阅当前文件使用上表。脚本内容及权限位保持不变，旧路径不再保留副本。
