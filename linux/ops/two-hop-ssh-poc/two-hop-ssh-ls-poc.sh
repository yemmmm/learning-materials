#!/usr/bin/env bash

# 最小可行性验证：
#   操作机 -> 个人账号@目标服务器 -> 公用账号@127.0.0.1 -> ls -la
#
# 密码始终由 OpenSSH 在终端中交互读取，本脚本不会读取、保存或打印密码。

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CONFIG_FILE="${SCRIPT_DIR}/servers.conf"
DRY_RUN=0

usage() {
    cat <<'EOF'
用法：
  ./two-hop-ssh-ls-poc.sh [--config 配置文件] [--dry-run]

选项：
  --config FILE  指定服务器配置文件，默认使用脚本目录下的 servers.conf
  --dry-run      只检查配置并显示访问路径，不建立 SSH 连接
  -h, --help     显示帮助

配置格式：
  名称|服务器地址|SSH端口|个人账号|公用账号

本脚本只会在公用账号下执行固定命令：ls -la
EOF
}

die() {
    printf '错误：%s\n' "$*" >&2
    exit 2
}

validate_name() {
    case "$1" in
        ''|*[!A-Za-z0-9_.-]*) return 1 ;;
        *) return 0 ;;
    esac
}

validate_host() {
    case "$1" in
        ''|*[!A-Za-z0-9_.:-]*) return 1 ;;
        *) return 0 ;;
    esac
}

validate_port() {
    case "$1" in
        ''|*[!0-9]*) return 1 ;;
    esac
    [ "$1" -ge 1 ] 2>/dev/null && [ "$1" -le 65535 ] 2>/dev/null
}

validate_user() {
    case "$1" in
        ''|[!A-Za-z_]*|*[!A-Za-z0-9_.-]*) return 1 ;;
        *) return 0 ;;
    esac
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --config)
            [ "$#" -ge 2 ] || die "--config 后缺少文件路径"
            CONFIG_FILE=$2
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "未知参数：$1"
            ;;
    esac
done

[ -r "$CONFIG_FILE" ] || die "无法读取配置文件：$CONFIG_FILE"
command -v ssh >/dev/null 2>&1 || die "当前环境找不到 ssh 命令"

SSH_COMMON_OPTIONS=(
    -o ConnectTimeout=10
    -o ServerAliveInterval=15
    -o ServerAliveCountMax=2
    -o PubkeyAuthentication=no
    -o PreferredAuthentications=keyboard-interactive,password
    -o NumberOfPasswordPrompts=3
)

total=0
success=0
failed=0
line_number=0

while IFS='|' read -r label host port personal_user shared_user extra ||
      [ -n "${label}${host}${port}${personal_user}${shared_user}${extra}" ]; do
    line_number=$((line_number + 1))
    shared_user=${shared_user%$'\r'}

    case "$label" in
        ''|\#*) continue ;;
    esac

    [ -z "$extra" ] || die "配置文件第 ${line_number} 行字段过多"
    validate_name "$label" || die "配置文件第 ${line_number} 行名称不合法：$label"
    validate_host "$host" || die "配置文件第 ${line_number} 行服务器地址不合法：$host"
    validate_port "$port" || die "配置文件第 ${line_number} 行 SSH 端口不合法：$port"
    validate_user "$personal_user" || die "配置文件第 ${line_number} 行个人账号不合法：$personal_user"
    validate_user "$shared_user" || die "配置文件第 ${line_number} 行公用账号不合法：$shared_user"

    total=$((total + 1))
    printf '\n[%s] %s@%s:%s -> %s@127.0.0.1 -> ls -la\n' \
        "$label" "$personal_user" "$host" "$port" "$shared_user"

    if [ "$DRY_RUN" -eq 1 ]; then
        success=$((success + 1))
        continue
    fi

    # 两层都强制分配终端，使 OpenSSH 能安全地交互读取密码。
    # 参数均经过白名单校验，远端执行命令固定为 ls -la。
    if ssh "${SSH_COMMON_OPTIONS[@]}" -tt -p "$port" \
        "${personal_user}@${host}" \
        ssh "${SSH_COMMON_OPTIONS[@]}" -tt \
        "${shared_user}@127.0.0.1" \
        ls -la; then
        printf '[%s] 成功\n' "$label"
        success=$((success + 1))
    else
        result=$?
        printf '[%s] 失败，SSH 返回码：%s\n' "$label" "$result" >&2
        failed=$((failed + 1))
    fi
done < "$CONFIG_FILE"

[ "$total" -gt 0 ] || die "配置文件中没有有效的服务器记录"

printf '\n执行汇总：总数=%s，成功=%s，失败=%s\n' "$total" "$success" "$failed"
[ "$failed" -eq 0 ]
