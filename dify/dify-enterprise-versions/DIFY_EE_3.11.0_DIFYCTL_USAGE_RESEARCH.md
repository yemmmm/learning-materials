# Dify Enterprise 3.11.0 difyctl 使用调研

> 调研日期：2026-07-28  
> 适用版本：Dify Enterprise 3.11.0 及以上（社区版 1.15.0 及以上）  
> 资料范围：Dify 官方 CLI 文档、官方发布博客及企业版发布说明

## 结论摘要

`difyctl` 是 Dify 在 1.15.0 / Enterprise 3.11.0 引入的官方命令行客户端。它让已发布在 Dify 中的应用和工作流可以直接从终端、Shell 脚本、CI/CD 或编码 Agent 调用，而无需为每个应用单独实现 API 集成。

它使用 **OAuth 2.0 Device Flow** 登录，CLI 不接触用户密码；得到的会话代表登录用户在当前工作区内已有的权限。因此，difyctl 是“以用户身份调用 Dify”的自动化入口，不是绕过 Dify RBAC 的管理员通道。

## 1. 支持范围与适用场景

| 项目 | 结论 |
| --- | --- |
| 最低版本 | Dify Community 1.15.0；企业版对应 EE 3.11.0+ |
| 安装物 | 无运行时依赖的独立二进制，按 Dify 版本发布 |
| 平台 | macOS/Linux：x64、arm64；Windows：x64 |
| 可调用对象 | Chatbot、Chatflow、Agent、Text Generator、Workflow |
| 常见用途 | 本地脚本、CI 作业、内部自动化、编码 Agent 调用已发布应用 |
| 权限模型 | 沿用 OAuth 登录用户在当前工作区的权限与 RBAC 约束 |

3.11.0 同时引入了推理过程可视化；对于支持推理输出的模型和节点，CLI 可通过 `--think` 显示推理内容。该参数只控制显示，不会凭空产生模型未返回的推理内容。

## 2. 安装

### macOS / Linux

企业版 3.11.0 对应社区版 1.15.0，建议显式安装匹配版本，而不是让脚本默认取最新版本：

```bash
curl -fsSL https://raw.githubusercontent.com/langgenius/dify/main/cli/scripts/install-cli.sh | DIFY_VERSION=1.15.0 sh
difyctl version
```

默认安装路径为 `~/.local/bin/difyctl`。若终端提示找不到命令，将该目录加入 Shell 的 `PATH`：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Windows PowerShell

```powershell
$env:DIFY_VERSION = "1.15.0"
irm https://raw.githubusercontent.com/langgenius/dify/main/cli/scripts/install.ps1 | iex
difyctl version
```

默认路径为 `%LOCALAPPDATA%\difyctl\bin\difyctl.exe`。生产环境也可从官方 GitHub Releases 手动下载与服务器版本匹配的二进制及 checksums 文件，计算 SHA-256 后再放入 PATH。

> 版本原则：difyctl 的构建与 Dify 发布版本对应。EE 3.11.0 应优先使用 DIFY_VERSION=1.15.0 的构建；升级服务器版本时，重新运行安装脚本或显式切换版本。

## 3. 登录与凭据安全

自托管企业版登录时，`--host` 传入 **Console API URL**，而不是猜测 API 容器地址；请从部署的实际 Console 配置或反向代理公开地址确认。

```bash
difyctl auth login --host https://dify.example.com
```

命令会显示一次性验证码和验证 URL。用户在浏览器中完成登录并输入验证码后，CLI 获得会话；无图形界面的服务器或 SSH 会话可使用 `--no-browser`，再在其他设备打开给出的 URL。一次性验证码有效期为 15 分钟。

```bash
# 无浏览器服务器
difyctl auth login --host https://dify.example.com --no-browser

# 确认当前身份；脚本可用 JSON
difyctl auth whoami
difyctl auth whoami --json

# 退出：撤销服务端会话并清理本地凭据
difyctl auth logout
```

令牌带 `dfoa_` 前缀，代表登录用户的权限。difyctl 优先放入操作系统凭据库（macOS Keychain、Windows Credential Manager、Linux Secret Service）；没有可用凭据库时，退回到配置目录中权限为 `0600` 的 `tokens.yml`。macOS/Linux 默认配置目录是 `~/.config/difyctl`（Linux 遵循 `XDG_CONFIG_HOME`），Windows 为 `%APPDATA%\difyctl`；可用 `DIFY_CONFIG_DIR` 覆盖。

安全要求：不要把该目录、令牌、浏览器设备码或 `auth login` 产物提交进仓库、镜像或 CI 日志。CI/服务器上的会话应使用最小权限的专用 Dify 账号并设置轮换/撤销流程。

## 4. 最小可用流程

```bash
# 1) 登录（只需在当前机器/用户上下文完成一次）
difyctl auth login --host https://dify.example.com

# 2) 列出当前工作区的应用，复制目标 ID
difyctl get app

# 3) 不确定输入时先读取应用类型和输入 schema
difyctl describe app <APP_ID>

# 4a) Chatbot / Chatflow / Agent / Text Generator：位置参数传消息
difyctl run app <CHAT_APP_ID> "请总结今天的工单"

# 4b) Workflow：--inputs 传一个 JSON 对象
difyctl run app <WORKFLOW_ID> --inputs '{"topic":"季度报告","audience":"管理层"}'
```

聊天类应用把回答输出到 stdout，并在 stderr 给出可继续对话的 `conversation` ID。工作流输出为 JSON，适合在自动化中继续处理。

## 5. 常用命令速查

| 目标 | 命令 | 说明 |
| --- | --- | --- |
| 查找应用 | `difyctl get app` | 可配 `--name report --mode workflow` 过滤 |
| 跨全部可访问工作区列举 | `difyctl get app -A` | 只会显示当前账号有权访问的应用 |
| 查看输入契约 | `difyctl describe app <APP_ID>` | 运行陌生应用前先确认必填输入与类型 |
| 发起聊天 | `difyctl run app <APP_ID> "消息"` | 回复在 stdout，提示/错误在 stderr |
| 运行工作流 | `difyctl run app <APP_ID> --inputs '{...}'` | `--inputs` 必须是一个 JSON 对象 |
| 从文件读取大输入 | `difyctl run app <APP_ID> --inputs-file inputs.json` | 适合复杂或敏感 JSON，注意文件权限 |
| 流式响应 | `difyctl run app <APP_ID> "消息" --stream` | 长回答实时输出 |
| 续接会话 | `difyctl run app <APP_ID> "下一问" --conversation <ID>` | 使用上一次 stderr 提示的 ID |
| 机器可读输出 | `... -o json` | 可接 `jq` 或 CI 后续步骤 |
| 仅输出应用 ID | `difyctl get app -o name` | 方便 Shell 循环 |
| 工作区列表/切换 | `difyctl get workspace` / `difyctl use workspace <ID>` | 也可用 `--workspace <ID>` 做单次覆盖 |
| 认证状态 | `difyctl auth whoami --json` | 在自动化任务开头做身份检查 |
| 帮助的 JSON 描述 | `difyctl help -o json` | 供 Agent 运行时发现当前 CLI 能力 |

## 6. 自动化示例

### 6.1 CI 中运行工作流并消费 JSON

```bash
set -euo pipefail

workflow_id="<WORKFLOW_ID>"
result="$(difyctl run app "$workflow_id" --inputs '{"environment":"staging"}' -o json)"
printf '%s\n' "$result" | jq .
```

关键点：让 stdout 只承载结构化业务结果；CLI 的提示与错误会走 stderr。应在 CI 的机密存储和受控执行节点中准备登录会话，并在任务失败时保留安全的错误上下文，不输出 token。

### 6.2 多轮聊天

```bash
difyctl run app <CHAT_APP_ID> "今天有哪些高优先级事件？"
# 从 stderr 记录的提示中取得 conversation ID 后：
difyctl run app <CHAT_APP_ID> "按负责人分组" --conversation <CONVERSATION_ID>
```

### 6.3 推理显示

```bash
difyctl run app <APP_ID> "审阅这份策略" --think
```

仅在所用模型支持推理输出、且对应 LLM 节点启用了相关设置时，才可能看到内容。生产场景应审查推理内容是否包含不应向终端操作者或日志系统暴露的信息。

## 7. 与 Coding Agent 的集成方式

difyctl 不是 SDK，也不要求为 Agent 写专用适配层。Agent 可把它当普通子进程：

```text
get app  →  describe app  →  run app  →  解析 JSON
```

CLI 可通过 `difyctl help -o json` 自描述命令，因此 Agent 能在运行时发现当前版本能力，而非依赖硬编码命令表。前提是 Agent 运行的那台机器已经有有效会话；Agent 本身不会替用户进行浏览器登录。

在企业环境中，建议为 Agent 单独创建最小权限账号与工作区，明确其可调用应用，并将 CLI 配置目录挂载为受控 Secret，而不是复用个人管理员会话。

## 8. 常见问题与排障

| 现象 | 检查与处理 |
| --- | --- |
| `command not found` | 确认 `~/.local/bin`（或 Windows 安装目录）已经进入 PATH，再运行 `difyctl version` |
| 登录页未自动打开 | 使用 `--no-browser`，在另一设备手工打开输出 URL 并输入验证码 |
| 主机被拒绝或自签名证书失败 | 正式环境使用受信任的 HTTPS；仅本地开发可加 `--insecure` |
| `auth_expired`（退出码 4） | 会话已过期或被撤销，重新执行 `difyctl auth login` |
| 工作流输入报错 | 先执行 `difyctl describe app <APP_ID>`，按 schema 构造单个 `--inputs` JSON 对象 |
| 自动化脚本无法解析输出 | 使用 `-o json`；区分 stdout 的业务结果和 stderr 的提示/错误 |
| 权限不足 | 确认当前身份、活跃工作区以及 Dify RBAC/应用 ACL；不要以提高 CLI 权限作为替代 |

## 9. 企业版升级前提

difyctl 进入 EE 3.11.0，而该版本升级需要维护窗口并强制执行 RBAC 成员角色迁移、数据集权限迁移和插件自动升级回填。未完成迁移时成员访问会受影响；因此不应在升级尚未完成时把 difyctl 接入正式自动化任务。

## 官方来源

- [Dify CLI 概览](https://docs.dify.ai/en/cli/overview)
- [安装 difyctl](https://docs.dify.ai/en/cli/install)
- [快速开始](https://docs.dify.ai/en/cli/quick-start)
- [认证与令牌存储](https://docs.dify.ai/en/cli/authenticate)
- [常用任务命令](https://docs.dify.ai/en/cli/common-tasks)
- [Dify 官方发布博客：difyctl](https://dify.ai/blog/dify-s-official-cli-difyctl-ships)
- [Dify Enterprise 3.11.0 发布说明](https://ee.dify.ai/releases/)

