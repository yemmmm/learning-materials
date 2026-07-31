# difyctl 使用指南

适用版本：Dify Community 1.15.0+，Dify Enterprise 3.11.0+

`difyctl` 是 Dify 官方命令行客户端，可以从终端、Shell 脚本、CI/CD 和编码 Agent 调用已经发布的应用或 Workflow，并将结果输出为文本或 JSON。

> 版本说明：Enterprise 3.11.0 以 Community 1.15.0 为基础。`difyctl` 的构建版本应与服务端 Dify 版本匹配。

## 1. 能做什么

- 登录 Dify，并使用当前用户在当前 Workspace 中已有的权限。
- 查看可访问的应用、应用类型和输入参数 schema。
- 调用 Chatbot、Chatflow、Agent、Text Generator 和 Workflow。
- 流式输出长回答，或输出可被 `jq`、CI 脚本处理的 JSON。
- 继续已有聊天会话。
- 在支持推理输出的模型和节点上显示思考过程。

`difyctl` 使用 OAuth 2.0 Device Flow 登录，不需要把 Dify 密码写入脚本；CLI 会话仍然受 Dify 的 Workspace 权限和 RBAC 约束。

## 2. 安装

### macOS / Linux

安装与服务端匹配的版本。Enterprise 3.11.0 通常对应 Community 1.15.0：

~~~bash
curl -fsSL https://raw.githubusercontent.com/langgenius/dify/main/cli/scripts/install-cli.sh \
  | DIFY_VERSION=1.15.0 sh

difyctl version
~~~

默认安装到 `~/.local/bin/difyctl`。如果提示找不到命令：

~~~bash
export PATH="$HOME/.local/bin:$PATH"
~~~

需要永久生效时，将该行加入 `~/.bashrc` 或 `~/.zshrc`。

### Windows PowerShell

~~~powershell
$env:DIFY_VERSION = "1.15.0"
irm https://raw.githubusercontent.com/langgenius/dify/main/cli/scripts/install.ps1 | iex
difyctl version
~~~

默认安装目录为 `%LOCALAPPDATA%\difyctl\bin`。

### 手动安装

从 [Dify GitHub Releases](https://github.com/langgenius/dify/releases) 下载：

1. 当前 Dify 版本对应平台的 `difyctl` 二进制文件；
2. 对应的 `difyctl-v<version>-checksums.txt`；
3. 使用 SHA-256 校验二进制文件，再放入 `PATH`。

Linux/macOS 示例：

~~~bash
shasum -a 256 difyctl-v<version>-<os>-<arch>
chmod +x difyctl-v<version>-<os>-<arch>
mv difyctl-v<version>-<os>-<arch> ~/.local/bin/difyctl
~~~

### 安装相关环境变量

| 变量 | 用途 | 示例 |
|---|---|---|
| `DIFY_VERSION` | 指定服务端 Dify 版本 | `1.15.0` |
| `DIFYCTL_VERSION` | 指定具体 CLI 构建版本；仅在未设置 `DIFY_VERSION` 时使用 | `0.1.0-alpha` |
| `DIFYCTL_PREFIX` | 修改安装目录；默认是 `~/.local` | `/usr/local` |

## 3. 自托管环境准备

自托管 Dify 在登录前需要确认 API 服务启用：

~~~dotenv
OPENAPI_ENABLED=true
ENABLE_OAUTH_BEARER=true
~~~

修改后重启 API 服务，并确认反向代理能够转发 OpenAPI 路由。

登录时的 `--host` 应填写用户可以访问的 Dify 对外地址或 Console API URL，不要填写 Docker Compose 内部的 API 容器地址。

## 4. 登录与退出

### 登录

~~~bash
difyctl auth login --host https://dify.example.com
~~~

CLI 会输出一次性验证码和验证地址。用浏览器打开地址，登录 Dify 并输入验证码。

服务器或 SSH 环境没有浏览器时：

~~~bash
difyctl auth login \
  --host https://dify.example.com \
  --no-browser
~~~

### 查看当前身份

~~~bash
difyctl auth whoami
difyctl auth whoami --json
~~~

JSON 输出适合在脚本开头做身份检查：

~~~bash
if ! difyctl auth whoami --json >/dev/null; then
  echo "difyctl session is invalid" >&2
  exit 1
fi
~~~

### 退出登录

~~~bash
difyctl auth logout
~~~

该命令会撤销服务端会话，并清理本机保存的凭据。

## 5. 最小可用流程

### 5.1 查看应用

~~~bash
difyctl get app
difyctl get app --name report --mode workflow
difyctl get app -o json
difyctl get app -o name
~~~

`-o name` 适合 Shell 循环；`-o json` 适合程序处理。

### 5.2 查看输入参数

运行陌生应用前，先查看应用类型和输入 schema：

~~~bash
difyctl describe app <APP_ID>
difyctl describe app <APP_ID> -o json
~~~

尤其是 Workflow，不要凭猜测填写输入字段；应以 `describe` 返回的字段名、类型和必填标记为准。

### 5.3 调用聊天类应用

Chatbot、Chatflow、Agent 和 Text Generator 将消息作为位置参数传入：

~~~bash
difyctl run app <CHAT_APP_ID> "请总结今天的工单"
~~~

回复默认写入 stdout，因此可以重定向到文件：

~~~bash
difyctl run app <CHAT_APP_ID> "总结本周故障" > reply.txt
~~~

### 5.4 运行 Workflow

Workflow 使用一个 JSON 对象作为输入：

~~~bash
difyctl run app <WORKFLOW_ID> \
  --inputs '{"topic":"季度报告","audience":"管理层"}'
~~~

输入较大或包含敏感信息时，放入文件：

~~~json
{
  "topic": "季度报告",
  "audience": "管理层"
}
~~~

然后执行：

~~~bash
chmod 600 inputs.json
difyctl run app <WORKFLOW_ID> --inputs-file inputs.json
~~~

## 6. 常用命令速查

| 目的 | 命令 |
|---|---|
| 查看版本 | `difyctl version` |
| 查看帮助 | `difyctl help` |
| 以 JSON 查看帮助 | `difyctl help -o json` |
| 登录 | `difyctl auth login --host <HOST>` |
| 无浏览器登录 | `difyctl auth login --host <HOST> --no-browser` |
| 查看当前用户 | `difyctl auth whoami` |
| 查看当前用户 JSON | `difyctl auth whoami --json` |
| 退出登录 | `difyctl auth logout` |
| 列出应用 | `difyctl get app` |
| 过滤应用 | `difyctl get app --name <TEXT> --mode <MODE>` |
| 列出所有可访问 Workspace 的应用 | `difyctl get app -A` |
| 查看应用输入 schema | `difyctl describe app <APP_ID>` |
| 调用聊天应用 | `difyctl run app <APP_ID> "<MESSAGE>"` |
| 运行 Workflow | `difyctl run app <APP_ID> --inputs '<JSON>'` |
| 从文件读取 Workflow 输入 | `difyctl run app <APP_ID> --inputs-file inputs.json` |
| 流式输出 | `difyctl run app <APP_ID> "<MESSAGE>" --stream` |
| 继续聊天会话 | `difyctl run app <APP_ID> "<MESSAGE>" --conversation <CONVERSATION_ID>` |
| 输出 JSON | 在命令末尾增加 `-o json` |
| 只输出名称或 ID | 在命令末尾增加 `-o name` |
| 查看 Workspace | `difyctl get workspace` |
| 切换 Workspace | `difyctl use workspace <WORKSPACE_ID>` |
| 单次指定 Workspace | 增加 `--workspace <WORKSPACE_ID>` |
| 显示思考过程 | 调用命令增加 `--think` |

## 7. 流式输出、会话和思考过程

### 流式输出

~~~bash
difyctl run app <CHAT_APP_ID> "写一份发布公告" --stream
~~~

### 继续多轮会话

聊天类应用执行后，CLI 会提示可继续使用的 `conversation` ID：

~~~bash
difyctl run app <CHAT_APP_ID> "今天有哪些高优先级事件？"

difyctl run app <CHAT_APP_ID> \
  "按负责人分组" \
  --conversation <CONVERSATION_ID>
~~~

### 显示 CoT 思考过程

~~~bash
difyctl run app <APP_ID> "审阅这份策略" --think
~~~

只有在模型实际返回 reasoning 内容、并且对应 LLM 节点启用了推理输出时，才会看到思考内容。`--think` 只控制显示，不会让不支持推理的模型产生推理结果。

生产环境中应评估思考内容是否包含敏感信息，避免未经审查地写入 CI 日志或共享终端。

## 8. JSON 与自动化

### 提取 Workflow 输出

~~~bash
set -euo pipefail

result="$(difyctl run app "$WORKFLOW_ID" \
  --inputs '{"environment":"staging"}' \
  -o json)"

printf '%s\n' "$result" | jq .
~~~

### 获取应用 ID

~~~bash
difyctl get app -o json | jq -r '.data[].id'
~~~

### 区分 stdout 和 stderr

- stdout：应用回答或 Workflow 结果；
- stderr：提示、会话续接信息和错误信息。

因此可以只保存业务结果：

~~~bash
difyctl run app <CHAT_APP_ID> "总结工单" > result.txt
~~~

不要把 `2>&1` 随意合并到结构化输出中，否则提示信息可能破坏 JSON 解析。

## 9. Workspace 切换

~~~bash
difyctl get workspace
difyctl use workspace <WORKSPACE_ID>
~~~

如果只想让某一条命令使用其他 Workspace，不改变默认上下文：

~~~bash
difyctl get app --workspace <WORKSPACE_ID>
~~~

跨 Workspace 查询仍然只会返回当前登录用户有权限访问的资源。

## 10. 凭据与安全建议

`difyctl` 使用 OAuth 会话。凭据优先存放在操作系统凭据库；没有可用凭据库时，才回退到配置目录中的 `tokens.yml`。

默认配置目录：

- macOS/Linux：`~/.config/difyctl`，Linux 会遵循 `XDG_CONFIG_HOME`；
- Windows：`%APPDATA%\difyctl`；
- 可通过 `DIFY_CONFIG_DIR` 修改。

建议：

1. 不要把 `tokens.yml`、配置目录或设备验证码提交到 Git、镜像和 CI 日志。
2. 自动化使用专用的最小权限 Dify 账号，不要复用管理员个人会话。
3. 通过 Dify Workspace/RBAC 限制该账号可访问的应用和资源。
4. 对 `inputs.json` 等可能包含敏感信息的文件设置 `600` 权限，并在任务结束后清理。
5. 生产环境使用有效 HTTPS 证书；`--insecure` 只用于本地开发和临时排障。

## 11. 常见问题

### `command not found: difyctl`

确认安装目录已加入 `PATH`：

~~~bash
export PATH="$HOME/.local/bin:$PATH"
difyctl version
~~~

### 登录时报 OpenAPI 或 OAuth 未启用

检查服务端：

~~~dotenv
OPENAPI_ENABLED=true
ENABLE_OAUTH_BEARER=true
~~~

然后重启 API 服务，并检查反向代理是否转发了 `/openapi/v1` 相关路由。

### `auth_expired`

会话已过期或被撤销，重新登录：

~~~bash
difyctl auth login --host <HOST>
~~~

### Workflow 输入错误

先查看 schema：

~~~bash
difyctl describe app <WORKFLOW_ID> -o json
~~~

确认字段名、类型、必填字段和 JSON 顶层结构。`--inputs` 必须是一个 JSON 对象。

### 自动化脚本解析失败

使用 `-o json`，并确保没有把 stderr 合并进 stdout：

~~~bash
difyctl run app <WORKFLOW_ID> \
  --inputs '{"topic":"test"}' \
  -o json | jq .
~~~

### 权限不足

检查当前用户、Workspace 和应用 ACL/RBAC 权限：

~~~bash
difyctl auth whoami --json
difyctl get workspace
difyctl get app
~~~

不要通过共享管理员会话规避权限问题。

## 12. 参考资料

- [Dify CLI 概览](https://docs.dify.ai/en/cli/overview)
- [安装 difyctl](https://docs.dify.ai/en/cli/install)
- [Quick Start](https://docs.dify.ai/en/cli/quick-start)
- [认证与令牌存储](https://docs.dify.ai/en/cli/authenticate)
- [常用任务命令](https://docs.dify.ai/en/cli/common-tasks)
- [Dify 1.15.0 Release Note](https://github.com/langgenius/dify/releases/tag/1.15.0)
- [Dify Enterprise 3.11.0 Release](https://ee.dify.ai/releases/)
