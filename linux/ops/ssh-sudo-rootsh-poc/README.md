# SSH + sudo rootsh 最小可行性验证

这个 PoC 用于验证以下访问链路是否能够被 Bash 脚本串行执行：

```text
操作机
  -> 个人账号@目标服务器
  -> sudo /bin/rootsh -i -u qqaipd1
  -> ls -la
```

脚本不读取、不保存密码。SSH 和 sudo 的认证提示都直接在当前终端中完成。

## 环境要求

- 操作机安装了 Bash 和 OpenSSH 客户端。
- 目标服务器允许个人账号通过 SSH 登录。
- 目标服务器上存在 `/bin/rootsh`，且个人账号被授权执行 `sudo /bin/rootsh -i -u qqaipd1`。
- `rootsh` 支持在账号参数后接要执行的命令；本 PoC 实际执行的是 `sudo /bin/rootsh -i -u qqaipd1 ls -la`。

服务器端不需要安装 Python、`expect`、`sshpass` 或其他第三方工具。

## 配置

复制示例配置：

```bash
cd linux/ops/ssh-sudo-rootsh-poc
cp servers.example.conf servers.conf
chmod 600 servers.conf
```

编辑 `servers.conf`，填写两台实际服务器：

```text
# 名称|服务器地址|SSH端口|个人账号|rootsh 切换账号
server-a|10.10.10.11|22|zhangsan|qqaipd1
server-b|10.10.10.12|22|zhangsan|qqaipd1
```

`servers.conf` 已被 `.gitignore` 排除，不会被提交。配置中也不要填写密码。

## 使用

先检查配置，不建立网络连接：

```bash
./ssh-sudo-rootsh-ls-poc.sh --dry-run
```

确认访问路径正确后执行：

```bash
./ssh-sudo-rootsh-ls-poc.sh
```

也可以指定其他位置的配置文件：

```bash
./ssh-sudo-rootsh-ls-poc.sh --config /安全目录/servers.conf
```

脚本串行处理服务器。每台服务器先执行 `sudo -k` 清除 sudo 缓存，再调用 rootsh 切换账号并执行 `ls -la`；失败时会记录 SSH 返回码，并继续验证下一台服务器。

## 首次运行时的正常提示

首次连接外层服务器时，OpenSSH 可能要求确认主机指纹。核对指纹后输入 `yes`，记录会写入操作机的 `known_hosts`。

一次完整连接通常会出现两次密码提示：

1. 个人账号登录目标服务器。
2. 个人账号执行 sudo/rootsh。

当前 PoC 故意不自动填写密码。它只验证 SSH 登录、sudo/rootsh 切换和公用账号命令执行是否可行。

## 安全边界

- 远端命令固定为 `sudo /bin/rootsh -i -u <切换账号> ls -la`，不能通过参数替换成其他命令。
- 脚本不会使用 `StrictHostKeyChecking=no` 绕过主机身份校验。
- 脚本不会把密码放入命令行、配置文件、环境变量或日志。
- 为了严格验证个人账号密码认证链路，当前版本禁用了 SSH 公钥认证；`sudo -k` 会清除 sudo 的短期认证缓存。

验证通过后，可以在此基础上增加 Docker Compose 的 `status`、`restart` 和 `logs` 等白名单操作。
