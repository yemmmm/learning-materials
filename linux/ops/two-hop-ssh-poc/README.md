# 两层 SSH 最小可行性验证

这个 PoC 用于验证以下访问链路是否能够被 Bash 脚本串行执行：

```text
操作机
  -> 个人账号@目标服务器
  -> 公用账号@127.0.0.1
  -> ls -la
```

脚本不读取、不保存密码。每次出现认证提示时，密码均由 OpenSSH 直接从当前终端读取。

## 环境要求

- 操作机安装了 Bash 和 OpenSSH 客户端。
- 目标服务器允许个人账号通过 SSH 登录。
- 目标服务器上存在 `ssh` 命令，并允许执行 `ssh 公用账号@127.0.0.1`。
- 公用账号允许通过密码或 keyboard-interactive 方式认证。

服务器端不需要安装 Python、`expect`、`sshpass` 或其他第三方工具。

## 配置

复制示例配置：

```bash
cd linux/ops/two-hop-ssh-poc
cp servers.example.conf servers.conf
chmod 600 servers.conf
```

编辑 `servers.conf`，填写两台实际服务器：

```text
# 名称|服务器地址|SSH端口|个人账号|公用账号
server-a|10.10.10.11|22|zhangsan|ops
server-b|10.10.10.12|22|zhangsan|ops
```

`servers.conf` 已被 `.gitignore` 排除，不会被提交。配置中也不要填写密码。

## 使用

先检查配置，不建立网络连接：

```bash
./two-hop-ssh-ls-poc.sh --dry-run
```

确认访问路径正确后执行：

```bash
./two-hop-ssh-ls-poc.sh
```

也可以指定其他位置的配置文件：

```bash
./two-hop-ssh-ls-poc.sh --config /安全目录/servers.conf
```

脚本串行处理服务器。每台服务器成功时会输出公用账号主目录的 `ls -la` 结果，失败时会记录 SSH 返回码，并继续验证下一台服务器。

## 首次运行时的正常提示

首次连接外层服务器或内层 `127.0.0.1` 时，OpenSSH 可能要求确认主机指纹。核对指纹后输入 `yes`，记录会写入操作机或目标服务器当前个人账号的 `known_hosts`。

一次完整连接最多可能出现两次密码提示：

1. 个人账号登录目标服务器。
2. 从个人账号登录公用账号。

当前 PoC 故意不自动填写密码。它只验证双层 SSH 链路和公用账号命令执行是否可行。

## 安全边界

- 远端命令固定为 `ls -la`，不能通过参数替换成其他命令。
- 脚本不会使用 `StrictHostKeyChecking=no` 绕过主机身份校验。
- 脚本不会把密码放入命令行、配置文件、环境变量或日志。
- 为了严格验证密码认证链路，当前版本禁用了公钥认证。

验证通过后，可以在此基础上增加 Docker Compose 的 `status`、`restart` 和 `logs` 等白名单操作。
