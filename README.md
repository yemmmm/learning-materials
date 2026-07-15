# Learning Materials

个人学习资料与工程产出归档库。按主题切分顶层目录，每个主题内部再用 `notes/` `projects/` `ops/` 区分形态。

## 顶层结构

| 目录 | 内容 |
|------|------|
| `ragflow/` | RAGFlow 升级 SQL、ES 优化、检索基准测试、源码补丁、HA 实验 |
| `dify/` | Dify 工作流调优、企业版分布式部署、性能分析、Jaeger tracing、env-sync 脚本 |
| `n8n/` | n8n 计费数据导出、Prometheus 指标、HA 企业版部署 |
| `detrick/` | 德勤封闭环境排查命令暂存（配合 `detrick-troubleshoot` skill） |
| `codex/` | Codex 相关阅读笔记与翻译 |
| `common/` | 跨产品通用知识：ES 低资源排错、MySQL→PG 迁移、SSO/OIDC 教程 |
| `tools/` | 与具体产品无关的通用脚本与 Claude Code 命令 |

## 主题内部约定

- `notes/` — Markdown 笔记、调研、方案文档
- `projects/` — 可独立运行/部署的子项目（自带 README、CLAUDE.md、依赖文件等）
- `ops/` — 运维脚本：env 同步、密钥重置、清理任务等

跨产品通用的内容放 `common/`；具体产品的内容放对应主题目录。

## 与 skill 的集成

`detrick/cmds.sh` 是 [`detrick-troubleshoot`](file:///home/yangxiang/.claude/skills/detrick-troubleshoot/SKILL.md) skill 的目标文件。该 skill 在本机生成 2-3 条 docker-compose 排查命令，写入此文件并 push 到 GitHub，供德勤服务器侧复制执行。

修改此文件路径时，必须同步更新 `~/.claude/skills/detrick-troubleshoot/SKILL.md` 中所有引用。
