# Expect + SSH + sudo rootsh 最小可行性验证

这个 PoC 用于验证以下访问链路能否由操作机上的 Expect 串行执行：

```text
操作机
  -> 个人账号@目标服务器
  -> sudo /bin/rootsh -i -u qqaipd1
  -> 在交互式 rootsh Shell 中输入 ls -la
```

脚本运行时隐藏输入一次个人账号密码，并将其用于 SSH 和 sudo 认证。密码只保存在 Expect 进程内存中，不写入配置文件、命令行参数或日志。

## 环境要求

- 操作机安装了 Bash、OpenSSH 客户端和 Expect。
- 目标服务器允许个人账号通过 SSH 登录。
- 目标服务器上存在 `/bin/rootsh`，且个人账号被授权执行 `sudo /bin/rootsh -i -u qqaipd1`。

Linux Mint/Ubuntu 操作机安装 Expect：

```bash
sudo apt update
sudo apt install -y expect
expect -v
```

服务器端不需要安装 Python、Expect、`sshpass` 或其他第三方工具。

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

脚本串行处理服务器，并对每台服务器执行以下步骤：

1. 使用个人账号和密码建立 SSH 连接。
2. 执行 `sudo -k` 清除该连接的 sudo 缓存。
3. 精确执行已被 sudoers 授权的 `sudo /bin/rootsh -i -u <切换账号>`。
4. 等待 rootsh Shell 提示符出现，再通过终端输入固定的 `ls -la`。
5. 使用 `id -un` 验证实际身份，并检查 `ls -la` 的执行结果。
6. 输入 `exit` 退出 rootsh，继续处理下一台服务器。

某台服务器失败时，脚本会记录失败阶段并继续验证下一台服务器。

## 主机指纹

脚本使用 OpenSSH 的 `StrictHostKeyChecking=accept-new`：

- 首次连接会自动记录新服务器的主机指纹。
- 已记录服务器的指纹发生变化时，连接会被拒绝。

## 安全边界

- sudo 调用严格保持为 `sudo /bin/rootsh -i -u <切换账号>`，不会追加 `ls` 参数。
- `ls -la` 仅在 rootsh 成功切换账号后作为交互式 Shell 输入发送。
- 脚本不会使用 `StrictHostKeyChecking=no` 绕过主机身份校验。
- 脚本不会把密码放入命令行、配置文件、环境变量或日志。
- 当前版本禁用 SSH 公钥认证，以验证个人账号的密码认证链路。
- 服务器地址和账号经过白名单校验，远端操作固定为身份检查和 `ls -la`。

验证通过后，可以在此基础上增加 Docker Compose 的 `status`、`restart` 和 `logs` 等白名单操作。
